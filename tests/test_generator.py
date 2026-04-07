from datasets.generator import generate_stub_data
from datasets.schema import SCHEMA


def test_counts_match_request():
    data = generate_stub_data(n_customers=10, n_accounts=20, n_txns=50, seed=1)
    assert len(data["customers"]) == 10
    assert len(data["accounts"]) == 20
    assert len(data["transactions"]) == 50


def test_seed_is_deterministic():
    a = generate_stub_data(n_customers=5, n_accounts=10, n_txns=25, seed=42)
    b = generate_stub_data(n_customers=5, n_accounts=10, n_txns=25, seed=42)
    assert a == b


def test_rows_have_schema_columns():
    data = generate_stub_data(n_customers=3, n_accounts=5, n_txns=10, seed=7)
    for table, columns in SCHEMA.items():
        for row in data[table]:
            assert set(row.keys()) == set(columns)


def test_referential_integrity():
    data = generate_stub_data(n_customers=5, n_accounts=15, n_txns=50, seed=3)
    cust_ids = {c["customer_id"] for c in data["customers"]}
    acct_ids = {a["account_id"] for a in data["accounts"]}
    assert all(a["customer_id"] in cust_ids for a in data["accounts"])
    assert all(t["account_id"] in acct_ids for t in data["transactions"])


def test_txn_type_matches_amount_sign():
    data = generate_stub_data(n_customers=3, n_accounts=5, n_txns=200, seed=9)
    for t in data["transactions"]:
        if t["amount"] > 0:
            assert t["txn_type"] == "CREDIT"
        else:
            assert t["txn_type"] == "DEBIT"
