-- ==========================================================================
-- E-commerce Profitability Analytics — Analytical star schema (SQLite)
-- --------------------------------------------------------------------------
-- Two fact tables (FactSales, FactMarketing) surrounded by four dimensions
-- (DimDate, DimProduct, DimCustomer, DimChannel).
--
-- Data is SIMULATED (fixed seed). This script is idempotent: it drops and
-- recreates every object, so the database can be rebuilt from scratch.
-- Enable foreign keys on the connection:  PRAGMA foreign_keys = ON;
-- ==========================================================================

PRAGMA foreign_keys = ON;

-- Drop in dependency order (facts before dimensions).
DROP TABLE IF EXISTS fact_marketing;
DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_channel;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_date;

-- --------------------------------------------------------------------------
-- Dimensions
-- --------------------------------------------------------------------------
CREATE TABLE dim_date (
    date_key    INTEGER PRIMARY KEY,          -- YYYYMMDD
    date        TEXT    NOT NULL UNIQUE,       -- ISO 'YYYY-MM-DD' (FK target)
    year        INTEGER NOT NULL,
    quarter     INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    month_name  TEXT    NOT NULL,
    week        INTEGER NOT NULL,
    day_of_week TEXT    NOT NULL
);

CREATE TABLE dim_product (
    product_id   TEXT    PRIMARY KEY,
    product_name TEXT    NOT NULL,
    category     TEXT    NOT NULL,
    subcategory  TEXT,
    brand        TEXT,
    unit_cost    REAL    NOT NULL CHECK (unit_cost >= 0),
    list_price   REAL    NOT NULL CHECK (list_price >= 0),
    supplier     TEXT,
    active_flag  INTEGER NOT NULL CHECK (active_flag IN (0, 1))
);

CREATE TABLE dim_customer (
    customer_id         TEXT PRIMARY KEY,
    customer_segment    TEXT NOT NULL,
    city                TEXT,
    region              TEXT,
    acquisition_date    TEXT NOT NULL,
    acquisition_channel TEXT NOT NULL
);

CREATE TABLE dim_channel (
    channel_id   INTEGER PRIMARY KEY,
    channel_name TEXT NOT NULL UNIQUE,
    channel_type TEXT NOT NULL
);

-- --------------------------------------------------------------------------
-- Facts
-- --------------------------------------------------------------------------
-- Grain: one order line. sale_id is a surrogate key (no natural line key in
-- the source); order_id groups lines belonging to the same order.
CREATE TABLE fact_sales (
    sale_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id         TEXT    NOT NULL,
    order_date       TEXT    NOT NULL,
    customer_id      TEXT    NOT NULL,
    product_id       TEXT    NOT NULL,
    channel_id       INTEGER NOT NULL,
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    unit_price       REAL    NOT NULL CHECK (unit_price >= 0),
    discount_amount  REAL    NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    shipping_revenue REAL    NOT NULL DEFAULT 0 CHECK (shipping_revenue >= 0),
    product_cost     REAL    NOT NULL CHECK (product_cost >= 0),
    shipping_cost    REAL    NOT NULL DEFAULT 0 CHECK (shipping_cost >= 0),
    payment_fee      REAL    NOT NULL DEFAULT 0 CHECK (payment_fee >= 0),
    returned_flag    INTEGER NOT NULL CHECK (returned_flag IN (0, 1)),
    refund_amount    REAL    NOT NULL DEFAULT 0 CHECK (refund_amount >= 0),
    FOREIGN KEY (order_date)  REFERENCES dim_date(date),
    FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
    FOREIGN KEY (product_id)  REFERENCES dim_product(product_id),
    FOREIGN KEY (channel_id)  REFERENCES dim_channel(channel_id)
);

-- Grain: one channel-day-campaign of marketing activity.
CREATE TABLE fact_marketing (
    marketing_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT    NOT NULL,
    channel_id      INTEGER NOT NULL,
    campaign_name   TEXT    NOT NULL,
    impressions     INTEGER NOT NULL CHECK (impressions >= 0),
    clicks          INTEGER NOT NULL CHECK (clicks >= 0),
    leads           INTEGER NOT NULL CHECK (leads >= 0),
    conversions     INTEGER NOT NULL CHECK (conversions >= 0),
    marketing_spend REAL    NOT NULL CHECK (marketing_spend >= 0),
    FOREIGN KEY (date)       REFERENCES dim_date(date),
    FOREIGN KEY (channel_id) REFERENCES dim_channel(channel_id)
);

-- --------------------------------------------------------------------------
-- Indexes (support the analytical joins / filters used by the queries)
-- --------------------------------------------------------------------------
CREATE INDEX idx_sales_order      ON fact_sales(order_id);
CREATE INDEX idx_sales_customer   ON fact_sales(customer_id);
CREATE INDEX idx_sales_product    ON fact_sales(product_id);
CREATE INDEX idx_sales_channel    ON fact_sales(channel_id);
CREATE INDEX idx_sales_date       ON fact_sales(order_date);
CREATE INDEX idx_mkt_channel      ON fact_marketing(channel_id);
CREATE INDEX idx_mkt_date         ON fact_marketing(date);
CREATE INDEX idx_customer_channel ON dim_customer(acquisition_channel);
CREATE INDEX idx_product_category ON dim_product(category);
