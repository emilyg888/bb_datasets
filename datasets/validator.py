"""Deterministic + light statistical validation for sandpit datasets."""

from __future__ import annotations

from typing import Any


def validate_basic(data: dict[str, list[dict[str, Any]]]) -> list[str]:
    errors: list[str] = []

    for acc in data["accounts"]:
        if acc["balance"] < 0:
            errors.append(f"Negative balance on account {acc['account_id']}")

    customer_ids = {c["customer_id"] for c in data["customers"]}
    for acc in data["accounts"]:
        if acc["customer_id"] not in customer_ids:
            errors.append(f"Invalid customer_id in account {acc['account_id']}")

    account_ids = {a["account_id"] for a in data["accounts"]}
    for txn in data["transactions"]:
        if txn["account_id"] not in account_ids:
            errors.append(f"Invalid account_id in txn {txn['txn_id']}")

    return errors


def validate_distribution(data: dict[str, list[dict[str, Any]]]) -> list[str]:
    amounts = [t["amount"] for t in data["transactions"]]

    if not amounts:
        return ["No transactions"]

    avg = sum(amounts) / len(amounts)
    if avg < -1_000 or avg > 10_000:
        return [f"Unrealistic average transaction amount: {avg:.2f}"]

    return []
