"""SME business banking sandpit dataset package."""

from datasets.generator import generate_stub_data
from datasets.loader import LoadedDataset, load_dataset, load_to_duckdb
from datasets.registry import (
    DEFAULT_DATASET_ROOT,
    DEFAULT_REGISTRY_PATH,
    DatasetDefinition,
    get_dataset_definition,
    list_datasets,
)
from datasets.schema import SCHEMA, TABLES
from datasets.validator import (
    validate_basic,
    validate_dataset_package,
    validate_distribution,
)

__all__ = [
    "DEFAULT_DATASET_ROOT",
    "DEFAULT_REGISTRY_PATH",
    "DatasetDefinition",
    "generate_stub_data",
    "get_dataset_definition",
    "list_datasets",
    "LoadedDataset",
    "load_dataset",
    "load_to_duckdb",
    "SCHEMA",
    "TABLES",
    "validate_basic",
    "validate_dataset_package",
    "validate_distribution",
]
