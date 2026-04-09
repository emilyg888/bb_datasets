"""Schema helpers for legacy banking tables and versioned dataset packages."""

from __future__ import annotations

import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype


SCHEMA = {
    "customers": [
        "customer_id",
        "name",
        "industry",
        "risk_rating",
        "country",
        "created_at",
    ],
    "accounts": [
        "account_id",
        "customer_id",
        "account_type",
        "balance",
        "currency",
        "opened_at",
    ],
    "transactions": [
        "txn_id",
        "account_id",
        "amount",
        "txn_type",
        "merchant_category",
        "timestamp",
    ],
}

TABLES = tuple(SCHEMA.keys())

SUPPORTED_DATASET_TYPES = frozenset(
    {"string", "float", "integer", "number", "datetime", "boolean"}
)


def validate_declared_types(
    frame: pd.DataFrame,
    column_types: dict[str, str],
) -> list[str]:
    """Validate a dataframe against a lightweight schema.json declaration."""
    errors: list[str] = []

    missing = [column for column in column_types if column not in frame.columns]
    if missing:
        return [f"Schema missing columns in data.csv: {', '.join(sorted(missing))}"]

    for column, declared_type in column_types.items():
        if declared_type not in SUPPORTED_DATASET_TYPES:
            errors.append(f"Unsupported schema type for {column}: {declared_type}")
            continue

        series = frame[column].dropna()
        if series.empty:
            continue

        if declared_type == "string":
            continue

        if declared_type in {"float", "integer", "number"}:
            if not _is_numeric_like(series):
                errors.append(f"Column {column} is not numeric as declared")
            continue

        if declared_type == "datetime":
            try:
                pd.to_datetime(series, errors="raise")
            except (TypeError, ValueError):
                errors.append(f"Column {column} is not datetime-like as declared")
            continue

        if declared_type == "boolean" and not _is_boolean_like(series):
            errors.append(f"Column {column} is not boolean-like as declared")

    return errors


def _is_numeric_like(series: pd.Series) -> bool:
    if is_numeric_dtype(series):
        return True

    try:
        pd.to_numeric(series, errors="raise")
    except (TypeError, ValueError):
        return False
    return True


def _is_boolean_like(series: pd.Series) -> bool:
    if is_bool_dtype(series):
        return True

    normalized = {str(value).strip().lower() for value in series.tolist()}
    return normalized <= {"true", "false", "0", "1"}
