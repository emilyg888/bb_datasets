"""
Fraud-focused SME business banking generator (v3).

Differences vs v2:
  - Customer risk distribution biased toward Medium/High
  - Account balances are log-normal (mean=10)
  - Three injected fraud patterns:
      1. Large spike      — 1% of txns × 50
      2. Velocity burst   — 2% of txns emit 5 same-amount DEBITs at base_time
      3. High-risk amp    — high-risk customers get 1.5×–3× multiplier
  - Designed for anomaly detection / fraud-rule training
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import numpy as np


def generate_fraud_dataset(
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

    # ------------------------------------------------------------------
    # 1. Customers (with risk bias)
    # ------------------------------------------------------------------
    for i in range(n_customers):
        risk = random.choices(
            ["Low", "Medium", "High"],
            weights=[0.6, 0.25, 0.15],
        )[0]

        customers.append({
            "customer_id": f"C{i:03}",
            "name":        f"Company_{i}",
            "industry":    random.choice(industries),
            "risk_rating": risk,
            "country":     "AU",
            "created_at":  "2022-01-01",
        })

    # ------------------------------------------------------------------
    # 2. Accounts (log-normal balances)
    # ------------------------------------------------------------------
    for i in range(n_accounts):
        cust = random.choice(customers)

        balance = np.random.lognormal(mean=10, sigma=1.0)

        accounts.append({
            "account_id":   f"A{i:03}",
            "customer_id":  cust["customer_id"],
            "account_type": "Business",
            "balance":      round(float(balance), 2),
            "currency":     "AUD",
            "opened_at":    "2022-01-10",
        })

    # ------------------------------------------------------------------
    # 3. Transactions (with anomalies)
    # ------------------------------------------------------------------
    base_time = datetime.now()

    for i in range(n_txns):
        acct = random.choice(accounts)
        cust = next(c for c in customers if c["customer_id"] == acct["customer_id"])

        # base distribution
        amount = np.random.lognormal(mean=7, sigma=1.2)
        is_fraud = False

        # FRAUD PATTERN 1 — large spike
        if random.random() < 0.01:
            amount *= 50
            is_fraud = True

        # FRAUD PATTERN 2 — velocity burst (the burst itself is fraud)
        # Pick a fraud merchant from a *subset* of categories so the model
        # can't trivially learn merchant_category=='Unknown' ⇒ fraud.
        if random.random() < 0.02:
            is_fraud = True
            burst_merchant = random.choice(["Unknown", "Supplier", "Utilities"])
            for _ in range(5):
                transactions.append({
                    "txn_id":            f"T{i:05}_burst",
                    "account_id":        acct["account_id"],
                    "amount":            round(float(amount), 2),
                    "txn_type":          "DEBIT",
                    "merchant_category": burst_merchant,
                    "timestamp":         base_time.isoformat(),
                    "fraud_flag":        True,
                })

        # FRAUD PATTERN 3 — high-risk amplification (NOT labelled as fraud:
        # this is a behavioural amplifier, not an injected anomaly)
        if cust["risk_rating"] == "High":
            amount *= random.uniform(1.5, 3)

        # sign
        if random.random() < 0.5:
            amount *= -1

        # Background merchant — uniform over all 5 categories so each
        # category has both fraud and non-fraud examples.
        merchant = random.choices(
            ["Sales", "Payroll", "Utilities", "Supplier", "Unknown"],
            weights=[0.2, 0.2, 0.2, 0.2, 0.2],
        )[0]

        transactions.append({
            "txn_id":            f"T{i:05}",
            "account_id":        acct["account_id"],
            "amount":            round(float(amount), 2),
            "txn_type":          "CREDIT" if amount > 0 else "DEBIT",
            "merchant_category": merchant,
            "timestamp": (
                base_time - timedelta(days=random.randint(0, 365))
            ).isoformat(),
            "fraud_flag":        is_fraud,
        })

    return {
        "customers":    customers,
        "accounts":     accounts,
        "transactions": transactions,
    }
