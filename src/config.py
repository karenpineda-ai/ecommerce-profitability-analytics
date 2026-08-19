"""Centralized configuration for the E-commerce Profitability Analytics project.

All paths, the fixed random seed, and the synthetic-dataset parameters live here
so that every stage of the pipeline (generation, cleaning, validation, loading,
analysis) reads its settings from a single source of truth.

NOTE: The dataset is fully simulated and reproducible via ``RANDOM_SEED``.
"""

from __future__ import annotations

from pathlib import Path

# --- Project paths ---------------------------------------------------------
# PROJECT_ROOT points to the repository root (parent of the ``src`` package).
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"

DATABASE_DIR: Path = PROJECT_ROOT / "database"
DATABASE_PATH: Path = DATABASE_DIR / "ecommerce.db"

SQL_DIR: Path = PROJECT_ROOT / "sql"
REPORTS_DIR: Path = PROJECT_ROOT / "reports"

# --- Reproducibility -------------------------------------------------------
# Fixed seed guarantees that the simulated dataset is identical on every run.
RANDOM_SEED: int = 42

# --- Simulation period -----------------------------------------------------
# At least 18 months of activity (see CLAUDE.md data rules).
START_DATE: str = "2024-01-01"
N_MONTHS: int = 18

# --- Dataset volume (within the ranges defined in CLAUDE.md) --------------
N_CUSTOMERS: int = 3_000        # rule: 2,000–5,000
N_PRODUCTS: int = 60            # rule: 40–80
N_ORDERS: int = 20_000          # rule: 10,000–30,000

# --- Reference dimensions --------------------------------------------------
PRODUCT_CATEGORIES: tuple[str, ...] = (
    "Electronics",
    "Home & Kitchen",
    "Fashion",
    "Beauty & Health",
    "Sports & Outdoors",
    "Toys & Games",
    "Office",
    "Grocery",
)  # 8 categories (rule: 6–10)

ACQUISITION_CHANNELS: tuple[str, ...] = (
    "Organic Search",
    "Paid Search",
    "Social Ads",
    "Email",
    "Referral",
    "Direct",
)  # 6 channels (rule: 5–7)

CUSTOMER_SEGMENTS: tuple[str, ...] = ("New", "Regular", "VIP")

# --- Data-quality injection ------------------------------------------------
# Controlled share of nulls / inconsistencies to exercise the validation layer.
NULL_INJECTION_RATE: float = 0.01

# --- Output file names -----------------------------------------------------
RAW_FILES: dict[str, str] = {
    "dim_date": "dim_date.csv",
    "dim_product": "dim_product.csv",
    "dim_customer": "dim_customer.csv",
    "dim_channel": "dim_channel.csv",
    "fact_sales": "fact_sales.csv",
    "fact_marketing": "fact_marketing.csv",
}


# --- Business parameters (per category) ------------------------------------
# Realistic margin / price / return / popularity differences between categories.
# base_margin drives unit_cost = list_price * (1 - margin); return_rate and
# popularity create the "high-volume/low-margin" and "low-volume/high-margin"
# products required by CLAUDE.md.
CATEGORY_PROFILES: dict[str, dict[str, float]] = {
    "Electronics":       {"price_min": 80,  "price_max": 1200, "base_margin": 0.18, "margin_jitter": 0.06, "return_rate": 0.10, "popularity": 1.3},
    "Home & Kitchen":    {"price_min": 15,  "price_max": 300,  "base_margin": 0.35, "margin_jitter": 0.08, "return_rate": 0.06, "popularity": 1.1},
    "Fashion":           {"price_min": 12,  "price_max": 180,  "base_margin": 0.55, "margin_jitter": 0.10, "return_rate": 0.15, "popularity": 1.4},
    "Beauty & Health":   {"price_min": 5,   "price_max": 90,   "base_margin": 0.60, "margin_jitter": 0.08, "return_rate": 0.05, "popularity": 1.2},
    "Sports & Outdoors": {"price_min": 15,  "price_max": 400,  "base_margin": 0.40, "margin_jitter": 0.08, "return_rate": 0.08, "popularity": 0.9},
    "Toys & Games":      {"price_min": 8,   "price_max": 120,  "base_margin": 0.45, "margin_jitter": 0.08, "return_rate": 0.07, "popularity": 0.8},
    "Office":            {"price_min": 3,   "price_max": 150,  "base_margin": 0.30, "margin_jitter": 0.07, "return_rate": 0.04, "popularity": 0.7},
    "Grocery":           {"price_min": 2,   "price_max": 40,   "base_margin": 0.12, "margin_jitter": 0.05, "return_rate": 0.02, "popularity": 1.5},
}

SUBCATEGORY_TIERS: tuple[str, ...] = ("Basic", "Plus", "Pro", "Lite", "Max")
BRANDS: tuple[str, ...] = (
    "Aurora", "Nimbus", "Vertex", "Pioneer", "Lumen",
    "Cobalt", "Summit", "Zephyr", "Terra", "Onyx",
)
SUPPLIERS: tuple[str, ...] = (
    "GlobalSupply Co", "PrimeVendor Ltd", "NorthTrade",
    "BlueOcean Dist", "Apex Wholesale", "Meridian Goods",
)

# --- Geography (fictional, clearly simulated) ------------------------------
REGIONS: dict[str, tuple[str, ...]] = {
    "North":   ("Northport", "Rivertown", "Lakeside"),
    "South":   ("Southbay", "Meadowville", "Pinecrest"),
    "East":    ("Eastford", "Harborview", "Greenfield"),
    "West":    ("Westbrook", "Sunvalley", "Hillcrest"),
    "Central": ("Centerville", "Springdale", "Fairview"),
}

# --- Channels --------------------------------------------------------------
# channel_type per acquisition channel (order matches ACQUISITION_CHANNELS,
# so channel_id = index + 1).
CHANNEL_TYPES: dict[str, str] = {
    "Organic Search": "Organic",
    "Paid Search":    "Paid",
    "Social Ads":     "Paid",
    "Email":          "Owned",
    "Referral":       "Referral",
    "Direct":         "Direct",
}
# Probability that a given order originates from each channel.
CHANNEL_ORDER_WEIGHTS: dict[str, float] = {
    "Organic Search": 0.28,
    "Paid Search":    0.20,
    "Social Ads":     0.18,
    "Email":          0.12,
    "Referral":       0.07,
    "Direct":         0.15,
}
# Channels that spend marketing budget (drive FactMarketing).
MARKETING_CHANNELS: dict[str, dict[str, float]] = {
    "Paid Search": {"daily_spend": 900, "cpc": 0.90, "ctr": 0.045, "lead_rate": 0.25, "conv_rate": 0.35},
    "Social Ads":  {"daily_spend": 700, "cpc": 0.60, "ctr": 0.020, "lead_rate": 0.15, "conv_rate": 0.20},
    "Email":       {"daily_spend": 120, "cpc": 0.05, "ctr": 0.120, "lead_rate": 0.30, "conv_rate": 0.25},
    "Referral":    {"daily_spend": 200, "cpc": 0.40, "ctr": 0.050, "lead_rate": 0.20, "conv_rate": 0.30},
}

# --- Customers -------------------------------------------------------------
SEGMENT_WEIGHTS: dict[str, float] = {"New": 0.50, "Regular": 0.35, "VIP": 0.15}
# Relative propensity to place orders, by segment.
SEGMENT_ACTIVITY: dict[str, float] = {"New": 0.6, "Regular": 1.0, "VIP": 2.2}
# Share of customers acquired BEFORE the observation window (existing base).
PRE_WINDOW_CUSTOMER_SHARE: float = 0.25
PRE_WINDOW_MAX_DAYS: int = 180

# --- Seasonality (monthly demand multiplier) -------------------------------
SEASONALITY_MONTH_MULTIPLIER: dict[int, float] = {
    1: 0.85, 2: 0.80, 3: 0.90, 4: 0.95, 5: 1.00, 6: 1.00,
    7: 1.05, 8: 1.00, 9: 1.00, 10: 1.10, 11: 1.35, 12: 1.50,
}

# --- Order economics -------------------------------------------------------
ITEMS_PER_ORDER: dict[str, object] = {"values": (1, 2, 3, 4), "probs": (0.60, 0.25, 0.10, 0.05)}
QUANTITY_PER_LINE: dict[str, object] = {"values": (1, 2, 3, 4, 5), "probs": (0.50, 0.25, 0.13, 0.08, 0.04)}
DISCOUNT_PROBABILITY: float = 0.35
DISCOUNT_RATE_RANGE: tuple[float, float] = (0.05, 0.30)
FREE_SHIPPING_PROBABILITY: float = 0.40
SHIPPING_REVENUE_RANGE: tuple[float, float] = (3.0, 9.0)
SHIPPING_COST_RANGE: tuple[float, float] = (2.0, 7.0)
PAYMENT_FEE_RATE: float = 0.029
PAYMENT_FEE_FIXED: float = 0.30
INACTIVE_PRODUCT_SHARE: float = 0.10

# --- Controlled data-quality injection (for the validation layer) ----------
# Kept low so the dataset remains usable; exercised in Phase 3.
QUALITY_ISSUES: dict[str, float] = {
    "customer_city_null":     0.010,
    "customer_region_null":   0.005,
    "product_brand_null":     0.010,
    "product_subcategory_null": 0.010,
    "sales_discount_null":    0.005,
    "sales_shipping_cost_null": 0.005,
    "sales_duplicate_rows":   0.001,
}


def ensure_directories() -> None:
    """Create the data/database output directories if they do not exist.

    Safe to call repeatedly; used by later pipeline stages before writing.
    """
    for directory in (RAW_DATA_DIR, PROCESSED_DATA_DIR, DATABASE_DIR):
        directory.mkdir(parents=True, exist_ok=True)
