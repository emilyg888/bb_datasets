from datasets.schema import SCHEMA, TABLES


def test_tables_present():
    assert set(TABLES) == {"customers", "accounts", "transactions"}


def test_customer_columns():
    assert SCHEMA["customers"][0] == "customer_id"
    assert "risk_rating" in SCHEMA["customers"]


def test_account_has_fk_to_customer():
    assert "customer_id" in SCHEMA["accounts"]


def test_transaction_has_fk_to_account():
    assert "account_id" in SCHEMA["transactions"]
