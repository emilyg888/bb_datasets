"""Stub generator for SME business banking data.

Deterministic when ``seed`` is provided so unit tests are reproducible.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any


def generate_stub_data(
    n_customers: int = 100,
    n_accounts: int = 300,
    n_txns: int = 10_000,
    seed: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    rng = random.Random(seed)

    customers = [
        {
            "customer_id": f"C{i:03}",
            "name": f"Company_{i}",
            "industry": rng.choice(["Retail", "Tech", "Manufacturing"]),
            "risk_rating": rng.choice(["Low", "Medium", "High"]),
            "country": "AU",
            "created_at": "2022-01-01",
        }
        for i in range(n_customers)
    ]

    accounts = [
        {
            "account_id": f"A{i:03}",
            "customer_id": rng.choice(customers)["customer_id"],
            "account_type": "Business",
            "balance": rng.randint(1_000, 500_000),
            "currency": "AUD",
            "opened_at": "2022-01-10",
        }
        for i in range(n_accounts)
    ]

    base_time = datetime(2024, 1, 1)
    transactions = []
    for i in range(n_txns):
        acct = rng.choice(accounts)
        amount = round(rng.gauss(2_000, 5_000), 2)
        transactions.append(
            {
                "txn_id": f"T{i:05}",
                "account_id": acct["account_id"],
                "amount": amount,
                "txn_type": "CREDIT" if amount > 0 else "DEBIT",
                "merchant_category": rng.choice(["Sales", "Payroll", "Utilities"]),
                "timestamp": (
                    base_time - timedelta(days=rng.randint(0, 365))
                ).isoformat(),
            }
        )

    return {
        "customers": customers,
        "accounts": accounts,
        "transactions": transactions,
    }
