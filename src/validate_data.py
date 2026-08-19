"""Data-quality validation layer.

Each rule is an independent function that returns a :class:`ValidationResult`
with an explicit severity:

* ``critical`` — breaks the analytical model (bad keys, orphan facts, negative
  amounts, out-of-period dates). If present, the process is considered blocked.
* ``warning`` — recoverable during cleaning (descriptive nulls, duplicate rows).

The functions are pure (no I/O) so they can be unit-tested in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src import config


@dataclass
class ValidationResult:
    """Outcome of a single validation rule."""

    rule: str
    table: str
    severity: str  # "critical" | "warning"
    n_errors: int
    message: str

    @property
    def passed(self) -> bool:
        return self.n_errors == 0

    @property
    def blocking(self) -> bool:
        """A critical rule with errors blocks the pipeline."""
        return self.severity == "critical" and not self.passed


# --------------------------------------------------------------------------
# Individual rules
# --------------------------------------------------------------------------
def check_duplicate_keys(df: pd.DataFrame, key: str, table: str) -> ValidationResult:
    n = int(df[key].duplicated().sum())
    return ValidationResult(
        f"duplicate_key[{key}]", table, "critical", n,
        f"{n} duplicate values in primary key '{key}'.",
    )


def check_nulls(
    df: pd.DataFrame, col: str, table: str, severity: str
) -> ValidationResult:
    n = int(df[col].isna().sum())
    return ValidationResult(
        f"nulls[{col}]", table, severity, n,
        f"{n} null values in '{col}'.",
    )


def check_non_positive(df: pd.DataFrame, col: str, table: str) -> ValidationResult:
    n = int((pd.to_numeric(df[col], errors="coerce") <= 0).sum())
    return ValidationResult(
        f"non_positive[{col}]", table, "critical", n,
        f"{n} rows with '{col}' <= 0.",
    )


def check_negative(df: pd.DataFrame, col: str, table: str) -> ValidationResult:
    n = int((pd.to_numeric(df[col], errors="coerce") < 0).sum())
    return ValidationResult(
        f"negative[{col}]", table, "critical", n,
        f"{n} rows with negative '{col}'.",
    )


def check_foreign_key(
    child: pd.DataFrame, col: str, parent: pd.DataFrame, parent_key: str, table: str
) -> ValidationResult:
    valid = set(parent[parent_key])
    mask = ~child[col].isin(valid) & child[col].notna()
    n = int(mask.sum())
    return ValidationResult(
        f"foreign_key[{col}->{parent_key}]", table, "critical", n,
        f"{n} rows in '{table}.{col}' with no match in parent '{parent_key}'.",
    )


def check_date_range(
    df: pd.DataFrame, col: str, min_date: str, max_date: str, table: str
) -> ValidationResult:
    s = pd.to_datetime(df[col], errors="coerce")
    mask = (s < pd.Timestamp(min_date)) | (s > pd.Timestamp(max_date)) | s.isna()
    n = int(mask.sum())
    return ValidationResult(
        f"date_range[{col}]", table, "critical", n,
        f"{n} rows with '{col}' outside [{min_date}, {max_date}] or unparseable.",
    )


def check_duplicate_rows(df: pd.DataFrame, table: str) -> ValidationResult:
    n = int(df.duplicated().sum())
    return ValidationResult(
        "duplicate_rows", table, "warning", n,
        f"{n} fully duplicated rows.",
    )


def check_margin_sanity(df: pd.DataFrame, table: str) -> ValidationResult:
    """Flag economically impossible gross margins (> 100%)."""
    revenue = (
        df["quantity"] * df["unit_price"]
        - df["discount_amount"].fillna(0)
        + df["shipping_revenue"]
    )
    gross_profit = (
        revenue - df["product_cost"] - df["shipping_cost"].fillna(0)
        - df["payment_fee"] - df["refund_amount"]
    )
    margin = gross_profit.where(revenue > 0) / revenue.where(revenue > 0)
    n = int((margin > 1.0).sum())
    return ValidationResult(
        "margin_sanity", table, "warning", n,
        f"{n} rows with impossible gross margin > 100%.",
    )


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def _period_bounds() -> tuple[str, str]:
    start = pd.Timestamp(config.START_DATE)
    end = start + pd.DateOffset(months=config.N_MONTHS) - pd.Timedelta(days=1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def run_all_validations(tables: dict[str, pd.DataFrame]) -> list[ValidationResult]:
    """Run every rule against the provided tables and return the results."""
    d_date = tables["dim_date"]
    d_prod = tables["dim_product"]
    d_cust = tables["dim_customer"]
    d_chan = tables["dim_channel"]
    f_sales = tables["fact_sales"]
    f_mkt = tables["fact_marketing"]
    min_d, max_d = _period_bounds()

    results: list[ValidationResult] = []

    # Primary-key uniqueness (critical).
    results.append(check_duplicate_keys(d_date, "date_key", "dim_date"))
    results.append(check_duplicate_keys(d_prod, "product_id", "dim_product"))
    results.append(check_duplicate_keys(d_cust, "customer_id", "dim_customer"))
    results.append(check_duplicate_keys(d_chan, "channel_id", "dim_channel"))

    # Null checks on key columns (critical).
    for col in ("order_id", "customer_id", "product_id", "order_date",
                "quantity", "unit_price"):
        results.append(check_nulls(f_sales, col, "fact_sales", "critical"))

    # Null checks on descriptive / recoverable columns (warning).
    results.append(check_nulls(d_cust, "city", "dim_customer", "warning"))
    results.append(check_nulls(d_cust, "region", "dim_customer", "warning"))
    results.append(check_nulls(d_prod, "brand", "dim_product", "warning"))
    results.append(check_nulls(d_prod, "subcategory", "dim_product", "warning"))
    results.append(check_nulls(f_sales, "discount_amount", "fact_sales", "warning"))
    results.append(check_nulls(f_sales, "shipping_cost", "fact_sales", "warning"))

    # Value ranges (critical).
    results.append(check_non_positive(f_sales, "quantity", "fact_sales"))
    for col in ("unit_price", "discount_amount", "product_cost",
                "shipping_cost", "payment_fee", "refund_amount"):
        results.append(check_negative(f_sales, col, "fact_sales"))

    # Foreign keys (critical).
    results.append(check_foreign_key(f_sales, "customer_id", d_cust, "customer_id", "fact_sales"))
    results.append(check_foreign_key(f_sales, "product_id", d_prod, "product_id", "fact_sales"))
    results.append(check_foreign_key(f_sales, "channel_id", d_chan, "channel_id", "fact_sales"))
    results.append(check_foreign_key(f_mkt, "channel_id", d_chan, "channel_id", "fact_marketing"))

    # Date ranges (critical).
    results.append(check_date_range(f_sales, "order_date", min_d, max_d, "fact_sales"))
    results.append(check_date_range(f_mkt, "date", min_d, max_d, "fact_marketing"))

    # Recoverable structural issues (warning).
    results.append(check_duplicate_rows(f_sales, "fact_sales"))
    results.append(check_margin_sanity(f_sales, "fact_sales"))

    return results


def summarize(results: list[ValidationResult]) -> dict[str, int]:
    """Aggregate counts for reporting / gating."""
    return {
        "rules": len(results),
        "passed": sum(r.passed for r in results),
        "failed": sum(not r.passed for r in results),
        "critical_failures": sum(r.blocking for r in results),
        "warnings": sum(r.severity == "warning" and not r.passed for r in results),
        "total_errors": sum(r.n_errors for r in results),
    }


def has_blocking_errors(results: list[ValidationResult]) -> bool:
    return any(r.blocking for r in results)


# --------------------------------------------------------------------------
# CLI entry point
# --------------------------------------------------------------------------
def _load_raw_tables() -> dict[str, pd.DataFrame]:
    """Load the raw CSVs into a table dict keyed as ``run_all_validations`` expects.

    Loading is done here (rather than reusing ``clean_data.load_raw``) to avoid a
    circular import: ``clean_data`` already imports this module.
    """
    return {
        name: pd.read_csv(config.RAW_DATA_DIR / fname)
        for name, fname in config.RAW_FILES.items()
    }


def main() -> int:
    """Run every validation rule against ``data/raw`` and print a report.

    Returns a process exit code: ``0`` when no blocking (critical) errors are
    found, ``1`` otherwise, so the command can gate a CI pipeline.
    """
    tables = _load_raw_tables()
    results = run_all_validations(tables)

    print(f"Validating raw data in {config.RAW_DATA_DIR}")
    print("-" * 78)
    for r in sorted(results, key=lambda x: (x.severity != "critical", x.table, x.rule)):
        status = "OK  " if r.passed else ("BLOCK" if r.blocking else "WARN ")
        print(f"  [{status}] {r.severity:<8} {r.table:<15} {r.rule:<28} "
              f"errors={r.n_errors:>6}  {r.message}")
    print("-" * 78)

    summary = summarize(results)
    print(
        "  rules={rules} passed={passed} failed={failed} "
        "critical={critical_failures} warnings={warnings} "
        "total_errors={total_errors}".format(**summary)
    )

    if has_blocking_errors(results):
        print("  [BLOCKED] Critical errors present. Fix before loading the database.")
        return 1
    print("  [OK] No blocking errors. Data ready for cleaning / load.")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
