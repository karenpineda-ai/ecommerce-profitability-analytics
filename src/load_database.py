"""Build the SQLite analytical database from the processed CSVs.

Steps:
1. Apply ``database/schema.sql`` (drops + recreates the star schema).
2. Load ``data/processed/*.csv`` in dependency order (dimensions, then facts)
   with foreign keys enforced.
3. Verify row counts, referential integrity and basic totals.

Run with:  ``python -m src.load_database``
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import pandas as pd

from src import config

SCHEMA_PATH = config.DATABASE_DIR / "schema.sql"

# Load order matters: dimensions must exist before facts (FK enforcement).
LOAD_ORDER: tuple[str, ...] = (
    "dim_date", "dim_product", "dim_customer", "dim_channel",
    "fact_sales", "fact_marketing",
)


@dataclass
class Check:
    """A single post-load verification."""

    name: str
    expected: object
    actual: object

    @property
    def passed(self) -> bool:
        return self.expected == self.actual


# --------------------------------------------------------------------------
# Load
# --------------------------------------------------------------------------
def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.execute("PRAGMA foreign_keys = ON;")  # re-assert after executescript


def _insert(conn: sqlite3.Connection, table: str, df: pd.DataFrame) -> None:
    """Insert a DataFrame into an existing table by column name.

    Columns absent from the DataFrame (e.g. surrogate AUTOINCREMENT keys) are
    left for SQLite to fill. NaN -> NULL and numpy scalars -> native Python.
    """
    cols = list(df.columns)
    placeholders = ", ".join(["?"] * len(cols))
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
    safe = df.astype(object).where(pd.notna(df), None)
    conn.executemany(sql, list(safe.itertuples(index=False, name=None)))


def load_all() -> dict[str, pd.DataFrame]:
    """Create the schema and load every processed table. Returns source frames."""
    config.ensure_directories()
    frames = {
        name: pd.read_csv(config.PROCESSED_DATA_DIR / config.RAW_FILES[name])
        for name in LOAD_ORDER
    }
    conn = _connect()
    try:
        apply_schema(conn)
        for name in LOAD_ORDER:
            _insert(conn, name, frames[name])
        conn.commit()
    finally:
        conn.close()
    return frames


# --------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------
def _scalar(conn: sqlite3.Connection, sql: str) -> object:
    return conn.execute(sql).fetchone()[0]


def verify(frames: dict[str, pd.DataFrame]) -> tuple[list[Check], list[tuple]]:
    """Run count, integrity and total checks against the loaded database."""
    conn = _connect()
    try:
        checks: list[Check] = []

        # 1. Row counts match the processed files.
        for name in LOAD_ORDER:
            actual = _scalar(conn, f"SELECT COUNT(*) FROM {name}")
            checks.append(Check(f"rowcount[{name}]", len(frames[name]), actual))

        # 2. Referential integrity (orphans must be zero).
        checks.append(Check("orphan_sales_customer", 0, _scalar(conn,
            "SELECT COUNT(*) FROM fact_sales f "
            "LEFT JOIN dim_customer d ON f.customer_id = d.customer_id "
            "WHERE d.customer_id IS NULL")))
        checks.append(Check("orphan_sales_product", 0, _scalar(conn,
            "SELECT COUNT(*) FROM fact_sales f "
            "LEFT JOIN dim_product p ON f.product_id = p.product_id "
            "WHERE p.product_id IS NULL")))
        checks.append(Check("orphan_sales_channel", 0, _scalar(conn,
            "SELECT COUNT(*) FROM fact_sales f "
            "LEFT JOIN dim_channel c ON f.channel_id = c.channel_id "
            "WHERE c.channel_id IS NULL")))
        checks.append(Check("orphan_sales_date", 0, _scalar(conn,
            "SELECT COUNT(*) FROM fact_sales f "
            "LEFT JOIN dim_date d ON f.order_date = d.date "
            "WHERE d.date IS NULL")))
        checks.append(Check("orphan_marketing_channel", 0, _scalar(conn,
            "SELECT COUNT(*) FROM fact_marketing m "
            "LEFT JOIN dim_channel c ON m.channel_id = c.channel_id "
            "WHERE c.channel_id IS NULL")))
        checks.append(Check("orphan_marketing_date", 0, _scalar(conn,
            "SELECT COUNT(*) FROM fact_marketing m "
            "LEFT JOIN dim_date d ON m.date = d.date "
            "WHERE d.date IS NULL")))

        # 3. Business integrity requested explicitly.
        checks.append(Check("orders_without_customer", 0, _scalar(conn,
            "SELECT COUNT(*) FROM fact_sales WHERE customer_id IS NULL")))
        checks.append(Check("lines_without_product", 0, _scalar(conn,
            "SELECT COUNT(*) FROM fact_sales WHERE product_id IS NULL")))
        checks.append(Check("invalid_order_dates", 0, _scalar(conn,
            "SELECT COUNT(*) FROM fact_sales WHERE date(order_date) IS NULL")))

        # 4. Totals reconcile with the processed file.
        src = frames["fact_sales"]
        src_rev = round(float((src["quantity"] * src["unit_price"]
                               - src["discount_amount"] + src["shipping_revenue"]).sum()), 2)
        db_rev = round(float(_scalar(conn,
            "SELECT SUM(quantity * unit_price - discount_amount + shipping_revenue) "
            "FROM fact_sales")), 2)
        checks.append(Check("total_revenue", src_rev, db_rev))
        checks.append(Check("total_quantity",
                            int(src["quantity"].sum()),
                            int(_scalar(conn, "SELECT SUM(quantity) FROM fact_sales"))))
        checks.append(Check("distinct_orders",
                            int(src["order_id"].nunique()),
                            int(_scalar(conn, "SELECT COUNT(DISTINCT order_id) FROM fact_sales"))))

        # 5. SQLite's own FK integrity check must be empty.
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        checks.append(Check("pragma_foreign_key_check", 0, len(fk_violations)))

        return checks, fk_violations
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def build() -> tuple[list[Check], list[tuple]]:
    frames = load_all()
    return verify(frames)


def main() -> None:
    checks, fk_violations = build()
    print(f"Database built at {config.DATABASE_PATH}")
    print("-" * 62)
    for c in checks:
        status = "OK " if c.passed else "FAIL"
        print(f"  [{status}] {c.name:28s} expected={c.expected!s:>14}  actual={c.actual!s:>14}")
    failed = [c for c in checks if not c.passed]
    print("-" * 62)
    if failed:
        print(f"  {len(failed)} check(s) FAILED.")
        if fk_violations:
            print("  FK violations:", fk_violations[:10])
    else:
        print("  All checks passed. Model ready for SQL queries (Phase 5).")


if __name__ == "__main__":
    main()
