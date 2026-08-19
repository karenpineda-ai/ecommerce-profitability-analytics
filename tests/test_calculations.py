"""Unit tests for the business-indicator calculations.

These tests verify the *mathematical coherence* of the KPIs defined in CLAUDE.md
(Revenue, Product Cost, Gross Profit, Gross Margin %, AOV, CAC, ROAS, Net
Marketing Contribution, Return Rate, RFM) by exercising the pure aggregation
functions in ``src.analysis``.

Two layers:
  1. A tiny fixture with hand-computed expected values (exact assertions).
  2. Invariants checked end-to-end on the real processed dataset, when present.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import analysis as an


# --------------------------------------------------------------------------
# Tiny fixture with hand-computed expected values
# --------------------------------------------------------------------------
@pytest.fixture
def tables() -> dict[str, pd.DataFrame]:
    """Two orders / two lines with fully known economics.

    Line 1 (order O1, channel 1 = Organic Search):
        revenue      = 2*10 - 1 + 3          = 22.0
        gross_profit = 22 - 6 - 2 - 0.5 - 0  = 13.5
    Line 2 (order O2, channel 2 = Paid Search, returned):
        revenue      = 1*100 - 0 + 0             = 100.0
        gross_profit = 100 - 80 - 5 - 3 - 100    = -88.0
    """
    fact_sales = pd.DataFrame({
        "order_id": ["O1", "O2"],
        "order_date": ["2024-01-15", "2024-02-10"],
        "customer_id": ["C1", "C2"],
        "product_id": ["P1", "P2"],
        "channel_id": [1, 2],
        "quantity": [2, 1],
        "unit_price": [10.0, 100.0],
        "discount_amount": [1.0, 0.0],
        "shipping_revenue": [3.0, 0.0],
        "product_cost": [6.0, 80.0],
        "shipping_cost": [2.0, 5.0],
        "payment_fee": [0.5, 3.0],
        "returned_flag": [0, 1],
        "refund_amount": [0.0, 100.0],
    })
    return {
        "dim_date": pd.DataFrame({"date": ["2024-01-01", "2024-02-01"]}),
        "dim_product": pd.DataFrame({
            "product_id": ["P1", "P2"],
            "product_name": ["Widget", "Gadget"],
            "category": ["Home & Kitchen", "Electronics"],
        }),
        "dim_customer": pd.DataFrame({
            "customer_id": ["C1", "C2"],
            "region": ["North", "South"],
            "customer_segment": ["Regular", "VIP"],
            "acquisition_date": ["2024-01-05", "2024-02-01"],
            "acquisition_channel": ["Paid Search", "Paid Search"],
        }),
        "dim_channel": pd.DataFrame({
            "channel_id": [1, 2],
            "channel_name": ["Organic Search", "Paid Search"],
            "channel_type": ["Organic", "Paid"],
        }),
        "fact_sales": fact_sales,
        "fact_marketing": pd.DataFrame({
            "channel_id": [2],
            "marketing_spend": [50.0],
            "conversions": [10],
        }),
    }


@pytest.fixture
def sales(tables) -> pd.DataFrame:
    return an.prepare(tables)


# --------------------------------------------------------------------------
# Core per-line formulas (Revenue, Product Cost, Gross Profit)
# --------------------------------------------------------------------------
def test_revenue_formula(sales):
    # Revenue = quantity * unit_price - discount_amount + shipping_revenue
    assert sales.loc[sales["order_id"] == "O1", "revenue"].iloc[0] == pytest.approx(22.0)
    assert sales.loc[sales["order_id"] == "O2", "revenue"].iloc[0] == pytest.approx(100.0)


def test_gross_profit_formula(sales):
    # Gross Profit = Revenue - Product Cost - Shipping Cost - Payment Fee - Refund
    assert sales.loc[sales["order_id"] == "O1", "gross_profit"].iloc[0] == pytest.approx(13.5)
    assert sales.loc[sales["order_id"] == "O2", "gross_profit"].iloc[0] == pytest.approx(-88.0)


def test_gross_profit_never_exceeds_revenue(sales):
    assert (sales["gross_profit"] <= sales["revenue"] + 1e-9).all()


# --------------------------------------------------------------------------
# Monthly aggregation: margin %, MoM growth, partition coherence
# --------------------------------------------------------------------------
def test_monthly_margin_and_mom(sales):
    m = an.monthly(sales).sort_values("year_month").reset_index(drop=True)
    assert list(m["year_month"]) == ["2024-01", "2024-02"]
    # Gross margin % = 100 * gross_profit / revenue
    assert m.loc[0, "gross_margin_pct"] == pytest.approx(100 * 13.5 / 22.0)
    assert m.loc[1, "gross_margin_pct"] == pytest.approx(100 * -88.0 / 100.0)
    # First month has no prior period → MoM is NaN.
    assert pd.isna(m.loc[0, "revenue_mom_pct"])
    # Second month MoM = (100 - 22) / 22 * 100
    assert m.loc[1, "revenue_mom_pct"] == pytest.approx((100.0 - 22.0) / 22.0 * 100)


def test_monthly_revenue_sums_to_total(sales):
    m = an.monthly(sales)
    assert m["revenue"].sum() == pytest.approx(sales["revenue"].sum())
    assert m["orders"].sum() == sales["order_id"].nunique()


def test_average_order_value(sales):
    # AOV = total revenue / number of distinct orders
    aov = sales["revenue"].sum() / sales["order_id"].nunique()
    assert aov == pytest.approx((22.0 + 100.0) / 2)


# --------------------------------------------------------------------------
# Category / product partitions must reconcile to the grand total
# --------------------------------------------------------------------------
def test_category_partition_reconciles(sales):
    c = an.by_category(sales)
    assert c["revenue"].sum() == pytest.approx(sales["revenue"].sum())
    assert c["gross_profit"].sum() == pytest.approx(sales["gross_profit"].sum())
    for row in c.itertuples():
        assert row.gross_margin_pct == pytest.approx(100 * row.gross_profit / row.revenue)


def test_product_partition_reconciles(sales):
    p = an.by_product(sales)
    assert p["gross_profit"].sum() == pytest.approx(sales["gross_profit"].sum())
    assert p["units"].sum() == sales["quantity"].sum()


# --------------------------------------------------------------------------
# Channel KPIs: CAC, ROAS, Net Marketing Contribution
# --------------------------------------------------------------------------
def test_channel_kpis(tables, sales):
    ch = an.by_channel(tables, sales).set_index("channel_name")

    paid = ch.loc["Paid Search"]
    # 2 new customers acquired via Paid Search, spend 50 → CAC = 25.
    assert paid["cac"] == pytest.approx(25.0)
    # ROAS = channel revenue / spend = 100 / 50 = 2.0
    assert paid["roas"] == pytest.approx(2.0)
    # Net contribution = gross_profit - spend = -88 - 50 = -138
    assert paid["net_marketing_contribution"] == pytest.approx(-138.0)

    organic = ch.loc["Organic Search"]
    # No spend and no acquisitions → CAC and ROAS undefined (NaN).
    assert pd.isna(organic["cac"])
    assert pd.isna(organic["roas"])
    # With zero spend, net contribution equals gross profit.
    assert organic["net_marketing_contribution"] == pytest.approx(organic["gross_profit"])


# --------------------------------------------------------------------------
# Return rate
# --------------------------------------------------------------------------
def test_return_rate(sales):
    r = an.returns_by_category(sales).set_index("category")
    # Electronics has 1 line, all returned → 100%.
    assert r.loc["Electronics", "return_rate_pct"] == pytest.approx(100.0)
    # Home & Kitchen has 1 line, none returned → 0%.
    assert r.loc["Home & Kitchen", "return_rate_pct"] == pytest.approx(0.0)


# --------------------------------------------------------------------------
# End-to-end invariants on the real processed dataset (skipped if absent)
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def real_sales():
    from src import config
    if not (config.PROCESSED_DATA_DIR / config.RAW_FILES["fact_sales"]).exists():
        pytest.skip("processed data not generated yet")
    return an.load(), an.prepare(an.load())


def test_real_totals_reconcile(real_sales):
    t, s = real_sales
    total_rev = s["revenue"].sum()
    total_gp = s["gross_profit"].sum()

    # Category partition must equal the grand total.
    c = an.by_category(s)
    assert c["revenue"].sum() == pytest.approx(total_rev, rel=1e-9)
    assert c["gross_profit"].sum() == pytest.approx(total_gp, rel=1e-9)

    # Overall gross margin is a sensible fraction of revenue.
    margin = total_gp / total_rev
    assert -1.0 < margin < 1.0
    assert total_rev > 0


def test_real_monthly_growth_is_consistent(real_sales):
    _, s = real_sales
    m = an.monthly(s)
    # Margin % is always 100 * gp / revenue, recomputed independently.
    recomputed = 100 * m["gross_profit"] / m["revenue"]
    assert np.allclose(m["gross_margin_pct"], recomputed)
    # Exactly one month (the first) has an undefined MoM.
    assert m["revenue_mom_pct"].isna().sum() == 1


def test_real_rfm_partitions_all_customers(real_sales):
    t, s = real_sales
    seg = an.rfm_segments(t)
    # Canonical scheme covers 100% of customers (buyers + non-buyers).
    assert seg["customers"].sum() == t["dim_customer"]["customer_id"].nunique()
    # Segment monetary reconciles to net revenue (revenue - refunds) of buyers,
    # up to per-customer rounding to cents.
    net_revenue = s["revenue"].sum() - s["refund_amount"].sum()
    assert seg["total_monetary"].sum() == pytest.approx(net_revenue, rel=1e-4)


def test_real_channel_contribution_identity(real_sales):
    t, s = real_sales
    ch = an.by_channel(t, s)
    # Net marketing contribution is exactly gross profit minus spend, every row.
    assert np.allclose(
        ch["net_marketing_contribution"], ch["gross_profit"] - ch["spend"]
    )
    # ROAS is defined iff there is spend.
    assert (ch.loc[ch["spend"] == 0, "roas"].isna()).all()
    assert (ch.loc[ch["spend"] > 0, "roas"] > 0).all()
