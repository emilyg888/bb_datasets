from datasets.generator import generate_stub_data
from datasets.validator import (
    validate_basic,
    validate_dataset_package,
    validate_distribution,
)


def _good_data():
    return generate_stub_data(n_customers=10, n_accounts=20, n_txns=200, seed=11)


def test_basic_passes_on_clean_data():
    assert validate_basic(_good_data()) == []


def test_basic_detects_negative_balance():
    data = _good_data()
    data["accounts"][0]["balance"] = -1
    errors = validate_basic(data)
    assert any("Negative balance" in e for e in errors)


def test_basic_detects_invalid_customer_fk():
    data = _good_data()
    data["accounts"][0]["customer_id"] = "C999"
    errors = validate_basic(data)
    assert any("Invalid customer_id" in e for e in errors)


def test_basic_detects_invalid_account_fk():
    data = _good_data()
    data["transactions"][0]["account_id"] = "A999"
    errors = validate_basic(data)
    assert any("Invalid account_id" in e for e in errors)


def test_distribution_passes_on_clean_data():
    assert validate_distribution(_good_data()) == []


def test_distribution_flags_empty_transactions():
    data = _good_data()
    data["transactions"] = []
    assert validate_distribution(data) == ["No transactions"]


def test_distribution_flags_unrealistic_average():
    data = _good_data()
    data["transactions"] = [
        {
            "txn_id": f"T{i}",
            "account_id": "A000",
            "amount": 1_000_000,
            "txn_type": "CREDIT",
            "merchant_category": "Sales",
            "timestamp": "2024-01-01T00:00:00",
        }
        for i in range(5)
    ]
    errors = validate_distribution(data)
    assert any("Unrealistic" in e for e in errors)


def test_dataset_package_passes_for_seeded_gold_dataset():
    assert validate_dataset_package("fraud_gold") == []


def test_dataset_package_flags_missing_labels(tmp_path):
    dataset_root = tmp_path / "external-datasets"
    registry_dir = dataset_root / "registry"
    dataset_dir = dataset_root / "fraud" / "broken_v1"
    registry_dir.mkdir(parents=True)
    dataset_dir.mkdir(parents=True)

    (registry_dir / "datasets.json").write_text(
        """
        {
          "broken_v1": {
            "domain": "fraud",
            "path": "../fraud/broken_v1",
            "version": "1.0",
            "tier": "bronze",
            "has_labels": true
          }
        }
        """.strip(),
        encoding="utf-8",
    )
    (dataset_dir / "data.csv").write_text(
        "transaction_id,amount,timestamp\nx1,10.0,2024-01-01T00:00:00\n",
        encoding="utf-8",
    )
    (dataset_dir / "metadata.json").write_text(
        """
        {
          "name": "broken_v1",
          "domain": "fraud",
          "description": "Broken dataset",
          "label_column": "is_fraud",
          "primary_keys": ["transaction_id"],
          "time_column": "timestamp",
          "evaluation_metric": "f1_score",
          "created_by": "ai-lab",
          "version": "1.0"
        }
        """.strip(),
        encoding="utf-8",
    )

    errors = validate_dataset_package("broken_v1", registry_path=registry_dir / "datasets.json")
    assert "labels.csv is required for datasets with has_labels=true" in errors
