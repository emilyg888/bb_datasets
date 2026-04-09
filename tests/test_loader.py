import duckdb

from datasets.generator import generate_stub_data
from datasets.loader import load_dataset, load_to_duckdb


def test_load_creates_all_tables(tmp_path):
    db = tmp_path / "sandbox.db"
    data = generate_stub_data(n_customers=5, n_accounts=10, n_txns=25, seed=4)

    load_to_duckdb(data, db_path=str(db))

    conn = duckdb.connect(str(db))
    try:
        tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
        assert {"customers", "accounts", "transactions"} <= tables

        assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 5
        assert conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 10
        assert conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 25
    finally:
        conn.close()


def test_load_is_idempotent(tmp_path):
    db = tmp_path / "sandbox.db"
    data = generate_stub_data(n_customers=3, n_accounts=6, n_txns=12, seed=5)

    load_to_duckdb(data, db_path=str(db))
    load_to_duckdb(data, db_path=str(db))  # CREATE OR REPLACE — must not error

    conn = duckdb.connect(str(db))
    try:
        assert conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 12
    finally:
        conn.close()


def test_load_dataset_reads_metadata_schema_and_labels():
    dataset = load_dataset("fraud_gold")

    assert dataset.metadata["evaluation_metric"] == "f1_score"
    assert dataset.schema["columns"]["amount"] == "float"
    assert list(dataset.data.columns) == [
        "transaction_id",
        "account_id",
        "amount",
        "timestamp",
        "country",
        "merchant_category",
        "channel",
    ]
    assert dataset.labels is not None
    assert dataset.labels["is_fraud"].tolist() == [False, True, True, False]


def test_load_dataset_evaluation_frame_joins_labels():
    dataset = load_dataset("fraud_gold")
    merged = dataset.evaluation_frame()

    assert "is_fraud" in merged.columns
    assert len(merged) == len(dataset.data)
