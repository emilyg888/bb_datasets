"""Load transactions from the bb_datasets DuckDB sandbox."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


# DuckDB lives at <repo>/exports/duckdb/sandbox.db; resolve against this
# file's location so the loader works regardless of cwd.
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = REPO_ROOT / "exports" / "duckdb" / "sandbox.db"


def load_transactions(db_path: str | Path = DEFAULT_DB) -> pd.DataFrame:
    """Return the transactions table joined with account & customer metadata.

    The join enriches each transaction with the owning account's balance/type
    and the underlying customer's risk_rating/industry — features the ML
    detector needs but the rule detectors are free to ignore.
    """
    conn = duckdb.connect(str(db_path))
    try:
        return conn.execute("""
            SELECT
                t.*,
                a.account_type,
                a.balance        AS account_balance,
                c.risk_rating,
                c.industry
            FROM transactions t
            JOIN accounts  a ON t.account_id  = a.account_id
            JOIN customers c ON a.customer_id = c.customer_id
        """).df()
    finally:
        conn.close()
