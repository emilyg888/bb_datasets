"""Feature engineering for fraud detection v1."""

from __future__ import annotations

import pandas as pd


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add absolute amount, per-account txn count, and z-score features."""
    df = df.copy()

    # Absolute amount — sign isn't fraud-relevant on its own
    df["abs_amount"] = df["amount"].abs()

    # Per-account transaction count (cheap velocity proxy — total volume,
    # not time-windowed; sufficient for v1, refine later for time bursts)
    df["txn_count"] = df.groupby("account_id")["txn_id"].transform("count")

    # Same-timestamp burst proxy — velocity bursts in v3 share base_time,
    # so this directly captures FRAUD PATTERN 2
    df["same_ts_count"] = df.groupby(["account_id", "timestamp"])["txn_id"].transform("count")

    # Global z-score on absolute amount
    mean = df["abs_amount"].mean()
    std  = df["abs_amount"].std() or 1.0
    df["z_score"] = (df["abs_amount"] - mean) / std

    # Per-account z-score — catches "unusual for *this* account", which
    # the global z misses on a log-normal distribution.
    grouped = df.groupby("account_id")["abs_amount"]
    acc_mean = grouped.transform("mean")
    acc_std  = grouped.transform("std").replace(0, 1.0).fillna(1.0)
    df["account_zscore"] = (df["abs_amount"] - acc_mean) / acc_std

    # Account-level burst signal — propagates the velocity-burst event to
    # *every* txn from a contaminated account. Catches the base txn that
    # triggered the burst (different timestamp, so per-row same_ts misses
    # it), but also flags every normal txn from those accounts. Whether
    # this is net positive is an empirical question.
    df["is_burst"]          = df["same_ts_count"] >= 3
    burst_accounts          = set(df.loc[df["is_burst"], "account_id"])
    df["account_had_burst"] = df["account_id"].isin(burst_accounts)

    return df
