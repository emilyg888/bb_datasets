"""Load fraud transactions from DuckDB or registered dataset packages."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from datasets.loader import load_dataset


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


def load_registered_transactions(dataset_id: str) -> pd.DataFrame:
    """Return a detector-ready dataframe from a registered fraud dataset."""
    dataset = load_dataset(dataset_id)
    frame = dataset.evaluation_frame().copy()

    rename_map: dict[str, str] = {}
    if "transaction_id" in frame.columns and "txn_id" not in frame.columns:
        rename_map["transaction_id"] = "txn_id"

    label_column = dataset.metadata.get("label_column")
    if label_column and label_column in frame.columns and label_column != "fraud_flag":
        rename_map[label_column] = "fraud_flag"

    if rename_map:
        frame = frame.rename(columns=rename_map)

    if "fraud_flag" not in frame.columns:
        raise ValueError(
            f"Registered dataset {dataset_id!r} must provide a label column for evaluation"
        )

    if "merchant_category" not in frame.columns:
        frame["merchant_category"] = "Unknown"
    if "risk_rating" not in frame.columns:
        frame["risk_rating"] = "Unknown"

    frame["fraud_flag"] = frame["fraud_flag"].map(_coerce_bool)

    return frame


def _coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
