"""DuckDB loader for sandpit datasets."""

from __future__ import annotations

from typing import Any

import duckdb
import pandas as pd


def load_to_duckdb(
    data: dict[str, list[dict[str, Any]]],
    db_path: str = "exports/duckdb/sandbox.db",
) -> None:
    conn = duckdb.connect(db_path)
    try:
        for table, rows in data.items():
            df = pd.DataFrame(rows)  # noqa: F841 — referenced by DuckDB by name
            conn.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM df")
    finally:
        conn.close()
