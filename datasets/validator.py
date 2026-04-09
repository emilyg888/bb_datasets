"""Deterministic + light statistical validation for sandpit datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from datasets.loader import LoadedDataset, load_dataset
from datasets.registry import DEFAULT_REGISTRY_PATH, get_dataset_definition
from datasets.schema import validate_declared_types


def validate_basic(data: dict[str, list[dict[str, Any]]]) -> list[str]:
    errors: list[str] = []

    for acc in data["accounts"]:
        if acc["balance"] < 0:
            errors.append(f"Negative balance on account {acc['account_id']}")

    customer_ids = {c["customer_id"] for c in data["customers"]}
    for acc in data["accounts"]:
        if acc["customer_id"] not in customer_ids:
            errors.append(f"Invalid customer_id in account {acc['account_id']}")

    account_ids = {a["account_id"] for a in data["accounts"]}
    for txn in data["transactions"]:
        if txn["account_id"] not in account_ids:
            errors.append(f"Invalid account_id in txn {txn['txn_id']}")

    return errors


def validate_distribution(data: dict[str, list[dict[str, Any]]]) -> list[str]:
    amounts = [t["amount"] for t in data["transactions"]]

    if not amounts:
        return ["No transactions"]

    avg = sum(amounts) / len(amounts)
    if avg < -1_000 or avg > 10_000:
        return [f"Unrealistic average transaction amount: {avg:.2f}"]

    return []


def validate_dataset_package(
    dataset_id: str,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> list[str]:
    definition = get_dataset_definition(dataset_id, registry_path=registry_path)
    bootstrap_errors: list[str] = []

    if not definition.data_path.exists():
        bootstrap_errors.append("Missing required file: data.csv")
    if not definition.metadata_path.exists():
        bootstrap_errors.append("Missing required file: metadata.json")
    if definition.has_labels and definition.labels_path is None:
        bootstrap_errors.append("labels.csv is required for datasets with has_labels=true")

    if bootstrap_errors:
        return bootstrap_errors

    return validate_loaded_dataset(load_dataset(dataset_id, registry_path=registry_path))


def validate_loaded_dataset(dataset: LoadedDataset) -> list[str]:
    """Validate the filesystem package, metadata contract, and declared schema."""
    errors: list[str] = []
    definition = dataset.definition
    metadata = dataset.metadata
    data = dataset.data
    labels = dataset.labels

    for required_path in (definition.data_path, definition.metadata_path):
        if not required_path.exists():
            errors.append(f"Missing required file: {required_path.name}")

    required_metadata = {"name", "domain", "description", "version", "created_by"}
    missing_metadata = sorted(required_metadata - metadata.keys())
    if missing_metadata:
        errors.append(
            f"metadata.json missing required fields: {', '.join(missing_metadata)}"
        )

    if metadata.get("name") and metadata["name"] != definition.dataset_id:
        errors.append("metadata.json name must match the dataset registry id")

    if data.empty:
        errors.append("data.csv must contain at least one row")

    primary_keys = metadata.get("primary_keys") or []
    if primary_keys:
        missing_keys = [column for column in primary_keys if column not in data.columns]
        if missing_keys:
            errors.append(
                f"data.csv missing primary key columns: {', '.join(sorted(missing_keys))}"
            )
        elif data.duplicated(subset=primary_keys).any():
            errors.append("data.csv contains duplicate primary key rows")

    time_column = metadata.get("time_column")
    if time_column and time_column not in data.columns:
        errors.append(f"time_column {time_column!r} not found in data.csv")

    label_column = metadata.get("label_column")
    if definition.has_labels:
        if labels is None:
            errors.append("labels.csv is required for datasets with has_labels=true")
        elif not label_column:
            errors.append("metadata.json must declare label_column when labels are present")
        else:
            if label_column not in labels.columns and label_column not in data.columns:
                errors.append(f"label_column {label_column!r} not found in labels.csv or data.csv")

            if primary_keys:
                missing_label_keys = [
                    column for column in primary_keys if column not in labels.columns
                ]
                if missing_label_keys:
                    errors.append(
                        "labels.csv missing primary key columns: "
                        + ", ".join(sorted(missing_label_keys))
                    )
                elif labels.duplicated(subset=primary_keys).any():
                    errors.append("labels.csv contains duplicate primary key rows")
                else:
                    missing_data_labels = labels.merge(
                        data[primary_keys].drop_duplicates(),
                        on=primary_keys,
                        how="left",
                        indicator=True,
                    )
                    if (missing_data_labels["_merge"] == "left_only").any():
                        errors.append("labels.csv contains keys that do not exist in data.csv")

    if dataset.schema is not None:
        columns = dataset.schema.get("columns")
        if not isinstance(columns, dict):
            errors.append("schema.json must contain a columns object")
        else:
            declared_columns = set(columns)
            actual_columns = set(data.columns)
            if declared_columns != actual_columns:
                errors.append("schema.json columns must match data.csv columns exactly")
            errors.extend(validate_declared_types(data, columns))

    return errors
