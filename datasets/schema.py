"""Canonical schema for the business banking sandpit dataset (v1)."""

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
