"""DuckDB loader plus filesystem-backed dataset package loading."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from datasets.registry import DEFAULT_REGISTRY_PATH, DatasetDefinition, get_dataset_definition


@dataclass(frozen=True)
class LoadedDataset:
    definition: DatasetDefinition
    data: pd.DataFrame
    labels: pd.DataFrame | None
    metadata: dict[str, Any]
    schema: dict[str, Any] | None

    def evaluation_frame(self) -> pd.DataFrame:
        """Return a frame ready for evaluation, joining labels when needed."""
        label_column = self.metadata.get("label_column")
        primary_keys = self.metadata.get("primary_keys") or []

        if self.labels is None or not label_column:
            return self.data.copy()

        if label_column in self.data.columns:
            return self.data.copy()

        if label_column in self.labels.columns and primary_keys:
            return self.data.merge(
                self.labels,
                on=primary_keys,
                how="left",
                validate="one_to_one",
            )

        return self.data.copy()


def load_dataset(
    dataset_id: str,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> LoadedDataset:
    definition = get_dataset_definition(dataset_id, registry_path=registry_path)

    with definition.metadata_path.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)

    schema = None
    if definition.schema_path is not None:
        with definition.schema_path.open("r", encoding="utf-8") as handle:
            schema = json.load(handle)

    data = pd.read_csv(definition.data_path)
    labels = pd.read_csv(definition.labels_path) if definition.labels_path is not None else None

    return LoadedDataset(
        definition=definition,
        data=data,
        labels=labels,
        metadata=metadata,
        schema=schema,
    )


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
