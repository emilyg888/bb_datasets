"""Rule-based fraud detector v1.

Predictions are written to `predicted_fraud` so the ground-truth label
`fraud_flag` (set by datasets/generator_v3.py) survives untouched and we
can compute precision / recall against it.
"""

from __future__ import annotations

import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Module-level singletons for the ML detectors so the model is fit once
# per process. Reset only if you swap the dataset shape.
_ml_model = None
_ml_encoders: dict[str, LabelEncoder] = {}
_ml_honest_model = None
_ml_honest_encoders: dict[str, LabelEncoder] = {}
_ml_honest_test_idx = None


_ML_FEATURES = [
    "abs_amount",
    "same_ts_count",
    "z_score",
    "account_zscore",
    "merchant_category_enc",
    "risk_rating_enc",
]


def detect_fraud_ml(df: pd.DataFrame) -> pd.DataFrame:
    """Detector v6 — Logistic Regression baseline (full-data fit).

    Trains on every row's `fraud_flag` and predicts on the same rows. F1 here
    is *training F1*, not generalization — see detect_fraud_ml_honest for the
    train/test variant. Useful as an upper-bound demonstration that the
    feature set carries enough signal for a learned model.
    """
    global _ml_model, _ml_encoders
    df = df.copy()

    # Encode categoricals into new columns so we don't clobber the originals
    for col in ["merchant_category", "risk_rating"]:
        if col not in _ml_encoders:
            _ml_encoders[col] = LabelEncoder().fit(df[col])
        df[f"{col}_enc"] = _ml_encoders[col].transform(df[col])

    X = df[_ML_FEATURES]
    y = df["fraud_flag"].astype(int)

    if _ml_model is None:
        _ml_model = LogisticRegression(max_iter=1000)
        _ml_model.fit(X, y)

    probs = _ml_model.predict_proba(X)[:, 1]
    df["fraud_score"]     = probs
    df["predicted_fraud"] = probs > 0.5
    return df


def detect_fraud_ml_honest(df: pd.DataFrame) -> pd.DataFrame:
    """Detector v6h — Logistic Regression with proper train/test split.

    Trains on a 70% split and reports predictions only on the held-out 30%.
    Other rows get predicted_fraud=False / fraud_score=NaN — they're not
    eligible for scoring (the orchestrator's confusion matrix will count them
    as TN/FN, slightly under-counting metrics, but the system gets an honest
    generalization estimate of what the model would do on unseen data).
    """
    global _ml_honest_model, _ml_honest_encoders, _ml_honest_test_idx
    df = df.copy()

    for col in ["merchant_category", "risk_rating"]:
        if col not in _ml_honest_encoders:
            _ml_honest_encoders[col] = LabelEncoder().fit(df[col])
        df[f"{col}_enc"] = _ml_honest_encoders[col].transform(df[col])

    X = df[_ML_FEATURES]
    y = df["fraud_flag"].astype(int)

    if _ml_honest_model is None:
        X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
            X, y, df.index, test_size=0.30, random_state=42, stratify=y,
        )
        _ml_honest_model = LogisticRegression(max_iter=1000)
        _ml_honest_model.fit(X_train, y_train)
        _ml_honest_test_idx = set(idx_test)

    df["fraud_score"]     = float("nan")
    df["predicted_fraud"] = False
    test_mask = df.index.isin(_ml_honest_test_idx)
    test_probs = _ml_honest_model.predict_proba(df.loc[test_mask, _ML_FEATURES])[:, 1]
    df.loc[test_mask, "fraud_score"]     = test_probs
    df.loc[test_mask, "predicted_fraud"] = test_probs > 0.5
    return df


# Default thresholds — calibrated against generator_v3 distribution. These
# can be overridden per-pattern via the registry pattern.config block.
DEFAULTS = {
    "spike_threshold":   20_000,  # |amount| above which a single txn is suspicious
    "same_ts_threshold": 3,       # ≥N txns sharing (account_id, timestamp) → burst
    "zscore_threshold":  3.0,     # |z| above this on abs_amount → statistical anomaly
}


def detect_fraud(
    df: pd.DataFrame,
    *,
    spike_threshold:   float = DEFAULTS["spike_threshold"],
    same_ts_threshold: int   = DEFAULTS["same_ts_threshold"],
    zscore_threshold:  float = DEFAULTS["zscore_threshold"],
) -> pd.DataFrame:
    """Detector v1 — global thresholds: spike + velocity + statistical anomaly.

    Adds boolean columns: is_spike, is_velocity, is_anomaly, predicted_fraud
    """
    df = df.copy()

    df["is_spike"]    = df["abs_amount"]    > spike_threshold
    df["is_velocity"] = df["same_ts_count"] >= same_ts_threshold
    df["is_anomaly"]  = df["z_score"].abs() > zscore_threshold

    df["predicted_fraud"] = (
        df["is_spike"] | df["is_velocity"] | df["is_anomaly"]
    )

    return df


def detect_fraud_v4(
    df: pd.DataFrame,
    *,
    spike_threshold:   float = 50_000,
    same_ts_threshold: int   = 4,
    zscore_threshold:  float = 3.0,
) -> pd.DataFrame:
    """Detector v4 — v1 + account-level burst signal.

    Adds is_account_burst as a 4th OR-rule. Recovers the burst *base*
    transactions that v1 misses (they have a different timestamp from the
    burst itself, so v1's same_ts rule never fires on them) at the cost of
    flagging every other transaction from those accounts.
    """
    df = df.copy()

    df["is_spike"]         = df["abs_amount"]    > spike_threshold
    df["is_velocity"]      = df["same_ts_count"] >= same_ts_threshold
    df["is_anomaly"]       = df["z_score"].abs() > zscore_threshold
    df["is_account_burst"] = df["account_had_burst"]

    df["predicted_fraud"] = (
        df["is_spike"]
        | df["is_velocity"]
        | df["is_account_burst"]
        | df["is_anomaly"]
    )
    return df


def detect_fraud_v5(df: pd.DataFrame) -> pd.DataFrame:
    """Detector v5 — v1 + same-account-same-day temporal burst signal.

    Builds a (account_id, day) lookup of velocity-burst events, then flags
    *any* txn from that account on that same day as part of the burst event.
    Localised in time so it doesn't contaminate the whole account history
    (which is what v4 did and why v4 collapsed precision).
    """
    df = df.copy()

    df["is_spike"]    = df["abs_amount"]    > 50_000
    df["is_velocity"] = df["same_ts_count"] >= 4
    df["is_anomaly"]  = df["z_score"].abs() > 3

    # Temporal burst signal
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    burst_rows = df[df["is_velocity"]]
    burst_lookup = set(
        zip(burst_rows["account_id"], burst_rows["timestamp"].dt.date)
    )
    df["is_temporal_burst"] = list(zip(df["account_id"], df["timestamp"].dt.date))
    df["is_temporal_burst"] = df["is_temporal_burst"].apply(lambda k: k in burst_lookup)

    df["predicted_fraud"] = (
        df["is_spike"]
        | df["is_velocity"]
        | df["is_temporal_burst"]
        | df["is_anomaly"]
    )
    return df


def detect_fraud_v3(df: pd.DataFrame) -> pd.DataFrame:
    """Detector v3 — weighted ensemble of three signals."""
    df = df.copy()

    df["is_spike"]    = df["abs_amount"]    > 20_000
    df["is_velocity"] = df["same_ts_count"] >= 3
    df["is_anomaly"]  = df["z_score"].abs() > 3

    df["fraud_score"] = (
        df["is_spike"]    * 0.4
        + df["is_velocity"] * 0.4
        + df["is_anomaly"]  * 0.2
    )

    df["predicted_fraud"] = df["fraud_score"] > 0.5
    return df


def detect_fraud_v2(
    df: pd.DataFrame,
    *,
    spike_threshold:           float = 15_000,
    same_ts_threshold:         int   = 3,
    account_zscore_threshold:  float = 2.5,
) -> pd.DataFrame:
    """Detector v2 — uses *per-account* z-score and a tighter spike threshold.

    Per-account z catches transactions that are anomalous *for that account*,
    which a global z-score on a log-normal distribution misses. Requires the
    `account_zscore` feature added by build_features_v2.

    Adds boolean columns: is_spike, is_velocity, is_anomaly, predicted_fraud
    """
    df = df.copy()

    df["is_spike"]    = df["abs_amount"]      > spike_threshold
    df["is_velocity"] = df["same_ts_count"]  >= same_ts_threshold
    df["is_anomaly"]  = df["account_zscore"].abs() > account_zscore_threshold

    df["predicted_fraud"] = (
        df["is_spike"] | df["is_velocity"] | df["is_anomaly"]
    )

    return df
