"""Unit tests for the data-quality validation and cleaning layers.

The validation functions are pure, so they are tested against small, purpose-built
DataFrames rather than the full generated dataset.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import clean_data as cl
from src import validate_data as vd


# --------------------------------------------------------------------------
# Individual validation rules
# --------------------------------------------------------------------------
def test_duplicate_keys_detected():
    df = pd.DataFrame({"id": [1, 2, 2, 3]})
    res = vd.check_duplicate_keys(df, "id", "t")
    assert res.n_errors == 1
    assert res.blocking is True


def test_duplicate_keys_clean():
    df = pd.DataFrame({"id": [1, 2, 3]})
    assert vd.check_duplicate_keys(df, "id", "t").passed


def test_nulls_detected_with_severity():
    df = pd.DataFrame({"city": ["A", None, None]})
    res = vd.check_nulls(df, "city", "dim_customer", "warning")
    assert res.n_errors == 2
    assert res.severity == "warning"
    assert res.blocking is False  # warnings never block


def test_non_positive_quantity():
    df = pd.DataFrame({"quantity": [1, 0, -3, 5]})
    res = vd.check_non_positive(df, "quantity", "fact_sales")
    assert res.n_errors == 2
    assert res.blocking is True


def test_negative_amount():
    df = pd.DataFrame({"unit_price": [10.0, -1.0, 0.0]})
    assert vd.check_negative(df, "unit_price", "fact_sales").n_errors == 1


def test_foreign_key_orphans():
    child = pd.DataFrame({"product_id": ["P1", "P2", "P9"]})
    parent = pd.DataFrame({"product_id": ["P1", "P2"]})
    res = vd.check_foreign_key(child, "product_id", parent, "product_id", "fact_sales")
    assert res.n_errors == 1
    assert res.blocking is True


def test_date_range_out_of_period():
    df = pd.DataFrame({"order_date": ["2024-01-05", "2019-01-01", "bad-date"]})
    res = vd.check_date_range(df, "order_date", "2024-01-01", "2025-06-30", "fact_sales")
    assert res.n_errors == 2  # out-of-range + unparseable


def test_duplicate_rows_warning():
    df = pd.DataFrame({"a": [1, 1], "b": [2, 2]})
    res = vd.check_duplicate_rows(df, "fact_sales")
    assert res.n_errors == 1
    assert res.severity == "warning"


# --------------------------------------------------------------------------
# Cleaning behavior
# --------------------------------------------------------------------------
@pytest.fixture
def tiny_tables() -> dict[str, pd.DataFrame]:
    sales = pd.DataFrame({
        "order_id": ["O1", "O1", "O2"],
        "order_date": ["2024-01-01", "2024-01-01", "2024-02-01"],
        "customer_id": ["C1", "C1", "C2"],
        "product_id": ["P1", "P1", "P2"],
        "channel_id": [1, 1, 2],
        "quantity": [1, 1, 2],
        "unit_price": [10.0, 10.0, 20.0],
        "discount_amount": [np.nan, np.nan, 5.0],
        "shipping_revenue": [0.0, 0.0, 3.0],
        "product_cost": [6.0, 6.0, 12.0],
        "shipping_cost": [np.nan, np.nan, 4.0],
        "payment_fee": [0.6, 0.6, 1.2],
        "returned_flag": [0, 0, 0],
        "refund_amount": [0.0, 0.0, 0.0],
    })
    return {
        "dim_date": pd.DataFrame({"date_key": [1, 2]}),
        "dim_product": pd.DataFrame({"product_id": ["P1", "P2"], "brand": ["B", None],
                                     "subcategory": ["S", "S"]}),
        "dim_customer": pd.DataFrame({"customer_id": ["C1", "C2"], "city": ["X", None],
                                      "region": ["R", "R"], "customer_segment": ["New", "VIP"],
                                      "acquisition_channel": ["Direct", "Email"]}),
        "dim_channel": pd.DataFrame({"channel_id": [1, 2], "channel_name": ["a", "b"],
                                     "channel_type": ["Direct", "Owned"]}),
        "fact_sales": sales,
        "fact_marketing": pd.DataFrame({"channel_id": [1], "date": ["2024-01-01"]}),
    }


def test_clean_removes_duplicate_rows(tiny_tables):
    cleaned, log = cl.clean(tiny_tables)
    assert log.duplicates_removed == 1
    assert len(cleaned["fact_sales"]) == 2


def test_clean_fills_recoverable_nulls(tiny_tables):
    cleaned, log = cl.clean(tiny_tables)
    s = cleaned["fact_sales"]
    assert s["discount_amount"].isna().sum() == 0
    assert s["shipping_cost"].isna().sum() == 0
    assert cleaned["dim_customer"]["city"].isna().sum() == 0
    assert (cleaned["dim_customer"]["city"] == "Unknown").any()
    assert cleaned["dim_product"]["brand"].isna().sum() == 0


def test_clean_preserves_no_critical_errors(tiny_tables):
    cleaned, _ = cl.clean(tiny_tables)
    results = [
        vd.check_nulls(cleaned["fact_sales"], "customer_id", "fact_sales", "critical"),
        vd.check_non_positive(cleaned["fact_sales"], "quantity", "fact_sales"),
    ]
    assert not vd.has_blocking_errors(results)


def test_reconcile_revenue_difference_is_duplicates(tiny_tables):
    cleaned, _ = cl.clean(tiny_tables)
    recon = cl.reconcile_revenue(tiny_tables, cleaned)
    # One duplicated line of revenue = 1*10 - 0 + 0 = 10.
    assert recon["difference"] == pytest.approx(10.0)


# --------------------------------------------------------------------------
# End-to-end on the real generated dataset (if present)
# --------------------------------------------------------------------------
def test_full_dataset_has_no_blocking_errors_after_cleaning():
    from src import config
    if not (config.RAW_DATA_DIR / config.RAW_FILES["fact_sales"]).exists():
        pytest.skip("raw data not generated yet")
    raw = cl.load_raw()
    cleaned, _ = cl.clean(raw)
    after = vd.run_all_validations(cleaned)
    assert not vd.has_blocking_errors(after)
