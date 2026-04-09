"""Dataset registry for discoverable versioned dataset packages."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_ROOT = REPO_ROOT / "external-datasets"
DEFAULT_REGISTRY_PATH = DEFAULT_DATASET_ROOT / "registry" / "datasets.json"


@dataclass(frozen=True)
class DatasetDefinition:
    dataset_id: str
    domain: str
    path: Path
    version: str
    tier: str
    has_labels: bool
    metadata_path: Path
    schema_path: Path | None
    data_path: Path
    labels_path: Path | None


def load_registry(
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> dict[str, dict[str, Any]]:
    path = Path(registry_path)
    with path.open("r", encoding="utf-8") as handle:
        registry = json.load(handle)

    if not isinstance(registry, dict):
        raise ValueError("Dataset registry must be a JSON object keyed by dataset id")

    return registry


def get_dataset_definition(
    dataset_id: str,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> DatasetDefinition:
    registry = load_registry(registry_path)
    payload = registry.get(dataset_id)
    if payload is None:
        raise KeyError(f"Dataset {dataset_id!r} not found in registry")
    return _build_definition(dataset_id, payload, Path(registry_path))


def list_datasets(
    *,
    domain: str | None = None,
    tier: str | None = None,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> list[DatasetDefinition]:
    registry = load_registry(registry_path)
    definitions = [
        _build_definition(dataset_id, payload, Path(registry_path))
        for dataset_id, payload in sorted(registry.items())
    ]

    if domain is not None:
        definitions = [definition for definition in definitions if definition.domain == domain]

    if tier is not None:
        definitions = [definition for definition in definitions if definition.tier == tier]

    return definitions


def _build_definition(
    dataset_id: str,
    payload: dict[str, Any],
    registry_path: Path,
) -> DatasetDefinition:
    registry_dir = registry_path.resolve().parent
    relative_path = payload["path"]
    dataset_dir = (registry_dir / relative_path).resolve()

    metadata_path = dataset_dir / "metadata.json"
    schema_path = dataset_dir / "schema.json"
    labels_path = dataset_dir / "labels.csv"

    return DatasetDefinition(
        dataset_id=dataset_id,
        domain=payload["domain"],
        path=dataset_dir,
        version=str(payload["version"]),
        tier=payload["tier"],
        has_labels=bool(payload.get("has_labels", False)),
        metadata_path=metadata_path,
        schema_path=schema_path if schema_path.exists() else None,
        data_path=dataset_dir / "data.csv",
        labels_path=labels_path if labels_path.exists() else None,
    )
