"""Execute the documented analytical queries in ``sql/`` against the database.

Each ``sql/*.sql`` file is split into named blocks delimited by a
``-- name: <slug>`` comment. Every block is a single SELECT (optionally with
CTEs). Results are written to ``data/processed/analysis_outputs/`` as
``<file_stem>__<slug>.csv``.

Run with:  ``python -m src.run_sql``
"""

from __future__ import annotations

import re
import sqlite3

import pandas as pd

from src import config

OUTPUT_DIR = config.PROCESSED_DATA_DIR / "analysis_outputs"
NAME_MARKER = re.compile(r"^\s*--\s*name:\s*(\S+)\s*$", re.IGNORECASE)


def parse_blocks(sql_text: str) -> list[tuple[str, str]]:
    """Split a .sql file into (slug, statement) blocks by the name marker."""
    blocks: list[tuple[str, str]] = []
    slug: str | None = None
    buffer: list[str] = []
    for line in sql_text.splitlines():
        m = NAME_MARKER.match(line)
        if m:
            if slug is not None:
                blocks.append((slug, "\n".join(buffer)))
            slug = m.group(1)
            buffer = [line]
        elif slug is not None:
            buffer.append(line)
    if slug is not None:
        blocks.append((slug, "\n".join(buffer)))
    return blocks


def run_all() -> list[tuple[str, int]]:
    """Run every block in every sql file; return (output_name, row_count)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DATABASE_PATH)
    results: list[tuple[str, int]] = []
    try:
        for sql_file in sorted(config.SQL_DIR.glob("*.sql")):
            for slug, statement in parse_blocks(sql_file.read_text(encoding="utf-8")):
                df = pd.read_sql_query(statement, conn)
                out_name = f"{sql_file.stem}__{slug}.csv"
                df.to_csv(OUTPUT_DIR / out_name, index=False)
                results.append((out_name, len(df)))
    finally:
        conn.close()
    return results


def main() -> None:
    results = run_all()
    print(f"Executed {len(results)} queries. Outputs in {OUTPUT_DIR}")
    for name, rows in results:
        print(f"  {name:52s} rows={rows:>5}")


if __name__ == "__main__":
    main()
