"""
Realistic SME business banking generator (v2).

Differences vs v1 (`generator.py`):
  - Customers carry a `size` segment (SMALL / MEDIUM / LARGE)
  - Account balances scale with customer size
  - Transaction amounts are log-normal (realistic financial distribution)
  - Payroll spikes (10% of txns × 5)
  - Fraud / anomaly spikes (1% of txns × 20)
  - Sign assigned independently of magnitude
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import numpy as np


def generate_realistic_data(
    n_customers: int = 100,
    n_accounts:  int = 300,
    n_txns:      int = 10_000,
    seed:        int = 42,
) -> dict[str, list[dict]]:
    random.seed(seed)
    np.random.seed(seed)

    customers: list[dict] = []
    accounts:  list[dict] = []
    transactions: list[dict] = []

    industries = ["Retail", "Tech", "Manufacturing"]
    sizes      = ["SMALL", "MEDIUM", "LARGE"]

    # ------------------------------------------------------------------
    # 1. Customers (with segmentation)
    # ------------------------------------------------------------------
    for i in range(n_customers):
        size = random.choices(sizes, weights=[0.6, 0.3, 0.1])[0]

        customers.append({
            "customer_id": f"C{i:03}",
            "name":        f"Company_{i}",
            "industry":    random.choice(industries),
            "size":        size,
            "risk_rating": random.choices(
                ["Low", "Medium", "High"],
                weights=[0.7, 0.2, 0.1],
            )[0],
            "country":     "AU",
            "created_at":  "2022-01-01",
        })

    # ------------------------------------------------------------------
    # 2. Accounts (linked to customers, balance scales with size)
    # ------------------------------------------------------------------
    for i in range(n_accounts):
        cust = random.choice(customers)

        base_balance = {
            "SMALL":  random.randint(5_000,    50_000),
            "MEDIUM": random.randint(50_000,   500_000),
            "LARGE":  random.randint(500_000,  5_000_000),
        }[cust["size"]]

        accounts.append({
            "account_id":   f"A{i:03}",
            "customer_id":  cust["customer_id"],
            "account_type": "Business",
            "balance":      base_balance,
            "currency":     "AUD",
            "opened_at":    "2022-01-10",
        })

    # ------------------------------------------------------------------
    # 3. Transactions (realistic behaviour)
    # ------------------------------------------------------------------
    base_time = datetime.now()

    for i in range(n_txns):
        acct = random.choice(accounts)

        # log-normal distribution (realistic financial data)
        amount = np.random.lognormal(mean=7, sigma=1.0)

        # payroll pattern (monthly spikes)
        if random.random() < 0.1:
            amount *= 5

        # fraud / anomaly
        if random.random() < 0.01:
            amount *= 20

        # sign
        if random.random() < 0.5:
            amount *= -1

        transactions.append({
            "txn_id":            f"T{i:05}",
            "account_id":        acct["account_id"],
            "amount":            round(float(amount), 2),
            "txn_type":          "CREDIT" if amount > 0 else "DEBIT",
            "merchant_category": random.choice([
                "Sales", "Payroll", "Utilities", "Supplier", "Tax",
            ]),
            "timestamp": (
                base_time - timedelta(days=random.randint(0, 365))
            ).isoformat(),
        })

    return {
        "customers":    customers,
        "accounts":     accounts,
        "transactions": transactions,
    }
