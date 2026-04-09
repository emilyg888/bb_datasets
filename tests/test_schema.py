import pandas as pd

from datasets.schema import SCHEMA, SUPPORTED_DATASET_TYPES, TABLES, validate_declared_types


def test_tables_present():
    assert set(TABLES) == {"customers", "accounts", "transactions"}


def test_customer_columns():
    assert SCHEMA["customers"][0] == "customer_id"
    assert "risk_rating" in SCHEMA["customers"]


def test_account_has_fk_to_customer():
    assert "customer_id" in SCHEMA["accounts"]


def test_transaction_has_fk_to_account():
    assert "account_id" in SCHEMA["transactions"]


def test_dataset_schema_supports_governed_types():
    assert {"string", "float", "datetime", "boolean"} <= SUPPORTED_DATASET_TYPES


def test_declared_types_validate_dataframe():
    frame = pd.DataFrame(
        {
            "transaction_id": ["x1", "x2"],
            "amount": [10.5, 12.0],
            "timestamp": ["2024-01-01T00:00:00", "2024-01-02T00:00:00"],
            "is_fraud": ["false", "true"],
        }
    )

    errors = validate_declared_types(
        frame,
        {
            "transaction_id": "string",
            "amount": "float",
            "timestamp": "datetime",
            "is_fraud": "boolean",
        },
    )

    assert errors == []
