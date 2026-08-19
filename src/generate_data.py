"""Reproducible synthetic-data generator for the star-schema model.

Builds the six tables defined in CLAUDE.md (DimDate, DimProduct, DimCustomer,
DimChannel, FactSales, FactMarketing) with realistic, internally consistent
relationships, seasonality, returns, discounts, shipping/payment costs, and a
small amount of *controlled* data-quality noise for the validation layer.

Everything is driven by a fixed seed (``config.RANDOM_SEED``) so the dataset is
identical on every run.

Run with:  ``python -m src.generate_data``
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import config


# --------------------------------------------------------------------------
# Dimension builders
# --------------------------------------------------------------------------
def build_dim_date() -> pd.DataFrame:
    """Daily calendar covering ``config.N_MONTHS`` months from ``START_DATE``."""
    start = pd.Timestamp(config.START_DATE)
    end = start + pd.DateOffset(months=config.N_MONTHS)
    dates = pd.date_range(start, end - pd.Timedelta(days=1), freq="D")
    return pd.DataFrame({
        "date_key": dates.strftime("%Y%m%d").astype(int),
        "date": dates.strftime("%Y-%m-%d"),
        "year": dates.year,
        "quarter": dates.quarter,
        "month": dates.month,
        "month_name": dates.strftime("%B"),
        "week": dates.isocalendar().week.to_numpy(),
        "day_of_week": dates.strftime("%A"),
    })


def build_dim_channel() -> pd.DataFrame:
    """One row per acquisition channel; channel_id = position + 1."""
    names = list(config.ACQUISITION_CHANNELS)
    return pd.DataFrame({
        "channel_id": range(1, len(names) + 1),
        "channel_name": names,
        "channel_type": [config.CHANNEL_TYPES[n] for n in names],
    })


def build_dim_product(rng: np.random.Generator) -> pd.DataFrame:
    """Products spread across categories with category-driven price/cost/margin."""
    categories = list(config.PRODUCT_CATEGORIES)
    n = config.N_PRODUCTS
    # Distribute products across categories as evenly as possible.
    cat_assignment = [categories[i % len(categories)] for i in range(n)]
    rng.shuffle(cat_assignment)

    list_price = np.empty(n)
    unit_cost = np.empty(n)
    subcategory: list[str] = []
    for i, cat in enumerate(cat_assignment):
        prof = config.CATEGORY_PROFILES[cat]
        price = rng.uniform(prof["price_min"], prof["price_max"])
        margin = np.clip(
            rng.normal(prof["base_margin"], prof["margin_jitter"]), 0.05, 0.75
        )
        list_price[i] = round(price, 2)
        unit_cost[i] = round(price * (1 - margin), 2)
        subcategory.append(f"{cat.split()[0]} {rng.choice(config.SUBCATEGORY_TIERS)}")

    brands = rng.choice(config.BRANDS, size=n)
    return pd.DataFrame({
        "product_id": [f"P{i:04d}" for i in range(1, n + 1)],
        "product_name": [f"{b} {s}" for b, s in zip(brands, subcategory)],
        "category": cat_assignment,
        "subcategory": subcategory,
        "brand": brands,
        "unit_cost": unit_cost,
        "list_price": list_price,
        "supplier": rng.choice(config.SUPPLIERS, size=n),
        "active_flag": (rng.random(n) >= config.INACTIVE_PRODUCT_SHARE).astype(int),
    })


def build_dim_customer(rng: np.random.Generator, total_days: int) -> pd.DataFrame:
    """Customers with segment, geography and an acquisition date/channel.

    ``acquisition_offset`` (days from START; negative = acquired before the
    observation window) is returned as a helper column for order sampling and
    dropped before persisting.
    """
    n = config.N_CUSTOMERS
    start = pd.Timestamp(config.START_DATE)

    segments = list(config.SEGMENT_WEIGHTS)
    seg = rng.choice(segments, size=n, p=list(config.SEGMENT_WEIGHTS.values()))

    regions = list(config.REGIONS)
    region = rng.choice(regions, size=n)
    city = np.array([rng.choice(config.REGIONS[r]) for r in region])

    channels = list(config.CHANNEL_ORDER_WEIGHTS)
    acq_channel = rng.choice(
        channels, size=n, p=list(config.CHANNEL_ORDER_WEIGHTS.values())
    )

    # Acquisition offset in days from START.
    pre_mask = rng.random(n) < config.PRE_WINDOW_CUSTOMER_SHARE
    acq_offset = np.where(
        pre_mask,
        -rng.integers(1, config.PRE_WINDOW_MAX_DAYS + 1, size=n),
        rng.integers(0, total_days, size=n),
    )
    acq_date = start + pd.to_timedelta(acq_offset, unit="D")

    # Per-customer activity weight = segment propensity * individual spread.
    base_activity = np.array([config.SEGMENT_ACTIVITY[s] for s in seg])
    activity = base_activity * rng.gamma(shape=2.0, scale=0.5, size=n)

    df = pd.DataFrame({
        "customer_id": [f"C{i:05d}" for i in range(1, n + 1)],
        "customer_segment": seg,
        "city": city,
        "region": region,
        "acquisition_date": acq_date.strftime("%Y-%m-%d"),
        "acquisition_channel": acq_channel,
        "_acq_offset": acq_offset,
        "_activity": activity,
    })
    return df


# --------------------------------------------------------------------------
# Fact builders
# --------------------------------------------------------------------------
def _seasonal_day_weights(dim_date: pd.DataFrame) -> np.ndarray:
    """Sampling weight per calendar day from the monthly seasonality factors."""
    w = dim_date["month"].map(config.SEASONALITY_MONTH_MULTIPLIER).to_numpy(dtype=float)
    return w / w.sum()


def build_fact_sales(
    rng: np.random.Generator,
    dim_date: pd.DataFrame,
    dim_product: pd.DataFrame,
    dim_customer: pd.DataFrame,
    dim_channel: pd.DataFrame,
) -> pd.DataFrame:
    """Order-line grain fact table with coherent FKs and full cost breakdown."""
    start = pd.Timestamp(config.START_DATE)
    total_days = len(dim_date)
    n_orders = config.N_ORDERS

    # --- Order-level attributes ---
    day_weights = _seasonal_day_weights(dim_date)
    order_day = rng.choice(total_days, size=n_orders, p=day_weights)

    # Customer per order: weighted pick among customers already acquired by that
    # day. Sorting by acquisition offset lets us restrict to an eligible prefix.
    order_cust = _assign_customers(rng, dim_customer, order_day)

    channel_ids = dim_channel["channel_id"].to_numpy()
    channel_p = np.array([
        config.CHANNEL_ORDER_WEIGHTS[n] for n in dim_channel["channel_name"]
    ])
    channel_p = channel_p / channel_p.sum()
    order_channel = rng.choice(channel_ids, size=n_orders, p=channel_p)

    items_vals = np.array(config.ITEMS_PER_ORDER["values"])
    items_probs = np.array(config.ITEMS_PER_ORDER["probs"])
    n_items = rng.choice(items_vals, size=n_orders, p=items_probs)

    # --- Expand orders to line-item grain ---
    order_ids = np.arange(1, n_orders + 1)
    line_order_id = np.repeat(order_ids, n_items)
    line_day = np.repeat(order_day, n_items)
    line_customer = np.repeat(order_cust, n_items)
    line_channel = np.repeat(order_channel, n_items)
    n_lines = line_order_id.size

    # Product per line, weighted by category popularity.
    prod_pop = dim_product["category"].map(
        lambda c: config.CATEGORY_PROFILES[c]["popularity"]
    ).to_numpy() * rng.gamma(2.0, 0.5, size=len(dim_product))
    prod_p = prod_pop / prod_pop.sum()
    prod_idx = rng.choice(len(dim_product), size=n_lines, p=prod_p)

    unit_cost = dim_product["unit_cost"].to_numpy()[prod_idx]
    unit_price = dim_product["list_price"].to_numpy()[prod_idx]
    ret_rate = dim_product["category"].map(
        lambda c: config.CATEGORY_PROFILES[c]["return_rate"]
    ).to_numpy()[prod_idx]

    q_vals = np.array(config.QUANTITY_PER_LINE["values"])
    q_probs = np.array(config.QUANTITY_PER_LINE["probs"])
    quantity = rng.choice(q_vals, size=n_lines, p=q_probs)

    gross = unit_price * quantity

    # Discounts.
    disc_mask = rng.random(n_lines) < config.DISCOUNT_PROBABILITY
    disc_rate = rng.uniform(*config.DISCOUNT_RATE_RANGE, size=n_lines)
    discount_amount = np.where(disc_mask, np.round(disc_rate * gross, 2), 0.0)

    # Shipping.
    free_mask = rng.random(n_lines) < config.FREE_SHIPPING_PROBABILITY
    shipping_revenue = np.where(
        free_mask, 0.0,
        np.round(rng.uniform(*config.SHIPPING_REVENUE_RANGE, size=n_lines), 2),
    )
    shipping_cost = np.round(
        rng.uniform(*config.SHIPPING_COST_RANGE, size=n_lines) + 0.4 * (quantity - 1), 2
    )

    revenue = gross - discount_amount + shipping_revenue
    payment_fee = np.round(config.PAYMENT_FEE_RATE * revenue + config.PAYMENT_FEE_FIXED, 2)
    product_cost = np.round(unit_cost * quantity, 2)

    # Returns.
    returned_flag = (rng.random(n_lines) < ret_rate).astype(int)
    refund_amount = np.where(
        returned_flag == 1, np.round(gross - discount_amount, 2), 0.0
    )

    order_date = (start + pd.to_timedelta(line_day, unit="D")).strftime("%Y-%m-%d")
    customer_ids = dim_customer["customer_id"].to_numpy()[line_customer]
    product_ids = dim_product["product_id"].to_numpy()[prod_idx]

    return pd.DataFrame({
        "order_id": [f"O{i:06d}" for i in line_order_id],
        "order_date": order_date,
        "customer_id": customer_ids,
        "product_id": product_ids,
        "channel_id": line_channel,
        "quantity": quantity,
        "unit_price": np.round(unit_price, 2),
        "discount_amount": discount_amount,
        "shipping_revenue": shipping_revenue,
        "product_cost": product_cost,
        "shipping_cost": shipping_cost,
        "payment_fee": payment_fee,
        "returned_flag": returned_flag,
        "refund_amount": refund_amount,
    })


def _assign_customers(
    rng: np.random.Generator, dim_customer: pd.DataFrame, order_day: np.ndarray
) -> np.ndarray:
    """Return a customer row-index per order, weighted by activity and eligible
    only if the customer was acquired on or before the order day."""
    acq = dim_customer["_acq_offset"].to_numpy()
    weight = dim_customer["_activity"].to_numpy()

    sort_idx = np.argsort(acq, kind="stable")
    acq_sorted = acq[sort_idx]
    cum_w = np.cumsum(weight[sort_idx])

    # Number of eligible customers (acq_offset <= order_day) for each order.
    k = np.searchsorted(acq_sorted, order_day, side="right")
    k = np.clip(k, 1, len(acq_sorted))  # order days >= 0, earliest acq < 0 -> k>=1

    target = rng.random(order_day.size) * cum_w[k - 1]
    pos = np.searchsorted(cum_w, target, side="left")
    pos = np.minimum(pos, k - 1)
    return sort_idx[pos]


def build_fact_marketing(
    rng: np.random.Generator, dim_date: pd.DataFrame, dim_channel: pd.DataFrame
) -> pd.DataFrame:
    """Daily marketing spend and funnel metrics for the spend channels."""
    name_to_id = dict(zip(dim_channel["channel_name"], dim_channel["channel_id"]))
    rows: list[dict[str, object]] = []
    for _, d in dim_date.iterrows():
        season = config.SEASONALITY_MONTH_MULTIPLIER[int(d["month"])]
        quarter_tag = f"{int(d['year'])}Q{int(d['quarter'])}"
        for name, p in config.MARKETING_CHANNELS.items():
            spend = max(0.0, rng.normal(p["daily_spend"], p["daily_spend"] * 0.20)) * season
            clicks = spend / p["cpc"]
            impressions = clicks / p["ctr"]
            leads = clicks * p["lead_rate"]
            conversions = leads * p["conv_rate"]
            rows.append({
                "date": d["date"],
                "channel_id": name_to_id[name],
                "campaign_name": f"{name} {quarter_tag}",
                "impressions": int(round(impressions)),
                "clicks": int(round(clicks)),
                "leads": int(round(leads)),
                "conversions": int(round(conversions)),
                "marketing_spend": round(spend, 2),
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Controlled data-quality injection
# --------------------------------------------------------------------------
def inject_quality_issues(
    rng: np.random.Generator,
    dim_customer: pd.DataFrame,
    dim_product: pd.DataFrame,
    fact_sales: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Introduce a small, documented amount of nulls and duplicate rows.

    Foreign keys and numeric integrity are preserved so the base stays usable;
    these issues exist to exercise the Phase 3 validation layer.
    """
    q = config.QUALITY_ISSUES
    report: dict[str, int] = {}

    def _null_out(df: pd.DataFrame, col: str, rate: float, key: str) -> None:
        # Floor of 2 so small dimension tables still receive testable nulls.
        n = max(2, int(round(len(df) * rate))) if rate > 0 else 0
        idx = rng.choice(len(df), size=n, replace=False)
        df.loc[df.index[idx], col] = np.nan
        report[key] = len(idx)

    _null_out(dim_customer, "city", q["customer_city_null"], "customer_city_null")
    _null_out(dim_customer, "region", q["customer_region_null"], "customer_region_null")
    _null_out(dim_product, "brand", q["product_brand_null"], "product_brand_null")
    _null_out(dim_product, "subcategory", q["product_subcategory_null"], "product_subcategory_null")
    _null_out(fact_sales, "discount_amount", q["sales_discount_null"], "sales_discount_null")
    _null_out(fact_sales, "shipping_cost", q["sales_shipping_cost_null"], "sales_shipping_cost_null")

    # Duplicate a few complete sales rows.
    n_dup = int(len(fact_sales) * q["sales_duplicate_rows"])
    dup_idx = rng.choice(len(fact_sales), size=n_dup, replace=False)
    fact_sales = pd.concat(
        [fact_sales, fact_sales.iloc[dup_idx]], ignore_index=True
    )
    report["sales_duplicate_rows"] = n_dup

    return dim_customer, dim_product, fact_sales, report


# --------------------------------------------------------------------------
# Persistence and summary
# --------------------------------------------------------------------------
def _write_summary(tables: dict[str, pd.DataFrame], quality: dict[str, int]) -> str:
    """Build a markdown summary and inject it into data/README.md markers."""
    lines = ["| Tabla | Filas | Columnas |", "|---|---:|---:|"]
    for name, df in tables.items():
        lines.append(f"| `{name}` | {len(df):,} | {df.shape[1]} |")
    table_md = "\n".join(lines)

    quality_md = "\n".join(f"- `{k}`: {v}" for k, v in quality.items())
    summary = (
        f"**Datos simulados** (semilla `{config.RANDOM_SEED}`). "
        f"Periodo: {config.N_MONTHS} meses desde {config.START_DATE}.\n\n"
        f"{table_md}\n\n"
        f"**Problemas de calidad inyectados (controlados):**\n\n{quality_md}\n"
    )

    readme = config.DATA_DIR / "README.md"
    text = readme.read_text(encoding="utf-8")
    start_tag, end_tag = "<!-- SUMMARY:START -->", "<!-- SUMMARY:END -->"
    before = text.split(start_tag)[0]
    after = text.split(end_tag)[1]
    readme.write_text(
        f"{before}{start_tag}\n{summary}{end_tag}{after}", encoding="utf-8"
    )
    return summary


def generate() -> dict[str, pd.DataFrame]:
    """Generate every table, inject controlled issues, persist CSVs and summary."""
    config.ensure_directories()
    rng = np.random.default_rng(config.RANDOM_SEED)

    dim_date = build_dim_date()
    dim_channel = build_dim_channel()
    dim_product = build_dim_product(rng)
    dim_customer = build_dim_customer(rng, total_days=len(dim_date))
    fact_sales = build_fact_sales(rng, dim_date, dim_product, dim_customer, dim_channel)
    fact_marketing = build_fact_marketing(rng, dim_date, dim_channel)

    dim_customer, dim_product, fact_sales, quality = inject_quality_issues(
        rng, dim_customer, dim_product, fact_sales
    )
    dim_customer = dim_customer.drop(columns=["_acq_offset", "_activity"])

    tables = {
        "dim_date": dim_date,
        "dim_product": dim_product,
        "dim_customer": dim_customer,
        "dim_channel": dim_channel,
        "fact_sales": fact_sales,
        "fact_marketing": fact_marketing,
    }
    for name, df in tables.items():
        df.to_csv(config.RAW_DATA_DIR / config.RAW_FILES[name], index=False)

    _write_summary(tables, quality)
    return tables


def main() -> None:
    tables = generate()
    print("Synthetic data generated in", config.RAW_DATA_DIR)
    for name, df in tables.items():
        print(f"  {name:16s} rows={len(df):>7,}  cols={df.shape[1]}")


if __name__ == "__main__":
    main()
