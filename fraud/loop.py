"""Two-phase fraud engine loop over exploration and judge datasets."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, UTC
import json
from pathlib import Path
from typing import Any, Protocol

import pandas as pd

from fraud.features import build_features
from fraud.load import load_registered_transactions


DEFAULT_EXPLORATION_DATASET = "fraud_v1"
DEFAULT_VALIDATION_DATASET = "fraud_gold"
DEFAULT_PHASE_LOG_PATH = Path(__file__).resolve().parent / "memory" / "phase_runs.tsv"


class PatternLike(Protocol):
    id: str
    config: dict[str, Any]
    confidence: float

    def resolve_handler(self): ...


@dataclass(frozen=True)
class PhaseResult:
    phase: str
    dataset_id: str
    pattern_id: str
    config: dict[str, Any]
    confusion: dict[str, int]
    metrics: dict[str, float]
    n_rows: int
    n_predicted: int
    error: str | None = None


def prepare_dataset_frame(dataset_id: str) -> pd.DataFrame:
    """Load a registered fraud dataset and derive detector features."""
    frame = load_registered_transactions(dataset_id)
    return build_features(frame)


def select_pattern(query: str, detectors: list[PatternLike], selector) -> PatternLike:
    chosen = selector.select(query, detectors)
    if chosen:
        return chosen[0]
    return max(detectors, key=lambda pattern: pattern.confidence)


def run_detector_phase(
    pattern: PatternLike,
    df: pd.DataFrame,
    *,
    phase: str,
    dataset_id: str,
    config_override: dict[str, Any] | None = None,
) -> PhaseResult:
    fn = pattern.resolve_handler()
    if fn is None:
        return PhaseResult(
            phase=phase,
            dataset_id=dataset_id,
            pattern_id=pattern.id,
            config={**pattern.config, **(config_override or {})},
            confusion={"tp": 0, "fp": 0, "fn": 0, "tn": 0},
            metrics={"precision": 0.0, "recall": 0.0, "f1": 0.0},
            n_rows=len(df),
            n_predicted=0,
            error=f"no handler for {pattern.id}",
        )

    cfg = {**pattern.config, **(config_override or {})}
    try:
        scored = fn(df.copy(), **cfg)
    except Exception as exc:  # pragma: no cover - defensive wrapper for external handlers
        return PhaseResult(
            phase=phase,
            dataset_id=dataset_id,
            pattern_id=pattern.id,
            config=cfg,
            confusion={"tp": 0, "fp": 0, "fn": 0, "tn": 0},
            metrics={"precision": 0.0, "recall": 0.0, "f1": 0.0},
            n_rows=len(df),
            n_predicted=0,
            error=str(exc),
        )

    confusion = _confusion(scored)
    metrics = _metrics(confusion)
    return PhaseResult(
        phase=phase,
        dataset_id=dataset_id,
        pattern_id=pattern.id,
        config=cfg,
        confusion=confusion,
        metrics=metrics,
        n_rows=len(scored),
        n_predicted=int(scored["predicted_fraud"].sum()),
    )


def run_two_phase_loop(
    pattern: PatternLike,
    *,
    query: str,
    exploration_dataset_id: str = DEFAULT_EXPLORATION_DATASET,
    validation_dataset_id: str = DEFAULT_VALIDATION_DATASET,
    phase_log_path: str | Path = DEFAULT_PHASE_LOG_PATH,
) -> tuple[PhaseResult, PhaseResult]:
    exploration_df = prepare_dataset_frame(exploration_dataset_id)
    validation_df = prepare_dataset_frame(validation_dataset_id)

    exploration = run_detector_phase(
        pattern,
        exploration_df,
        phase="exploration",
        dataset_id=exploration_dataset_id,
    )
    validation = run_detector_phase(
        pattern,
        validation_df,
        phase="validation",
        dataset_id=validation_dataset_id,
    )

    append_phase_results(
        [exploration, validation],
        query=query,
        phase_log_path=phase_log_path,
    )
    return exploration, validation


def append_phase_results(
    results: list[PhaseResult],
    *,
    query: str,
    phase_log_path: str | Path = DEFAULT_PHASE_LOG_PATH,
) -> None:
    path = Path(phase_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()

    fieldnames = [
        "timestamp_utc",
        "query",
        "phase",
        "dataset_id",
        "pattern_id",
        "precision",
        "recall",
        "f1",
        "tp",
        "fp",
        "fn",
        "tn",
        "n_rows",
        "n_predicted",
        "config_json",
        "error",
    ]

    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        if write_header:
            writer.writeheader()

        timestamp = datetime.now(UTC).isoformat()
        for result in results:
            writer.writerow(
                {
                    "timestamp_utc": timestamp,
                    "query": query,
                    "phase": result.phase,
                    "dataset_id": result.dataset_id,
                    "pattern_id": result.pattern_id,
                    "precision": f"{result.metrics['precision']:.6f}",
                    "recall": f"{result.metrics['recall']:.6f}",
                    "f1": f"{result.metrics['f1']:.6f}",
                    "tp": result.confusion["tp"],
                    "fp": result.confusion["fp"],
                    "fn": result.confusion["fn"],
                    "tn": result.confusion["tn"],
                    "n_rows": result.n_rows,
                    "n_predicted": result.n_predicted,
                    "config_json": json.dumps(result.config, sort_keys=True),
                    "error": result.error or "",
                }
            )


def _confusion(df: pd.DataFrame) -> dict[str, int]:
    truth = df["fraud_flag"].astype(bool)
    pred = df["predicted_fraud"].astype(bool)
    return {
        "tp": int((truth & pred).sum()),
        "fp": int((~truth & pred).sum()),
        "fn": int((truth & ~pred).sum()),
        "tn": int((~truth & ~pred).sum()),
    }


def _metrics(confusion: dict[str, int]) -> dict[str, float]:
    precision = (
        confusion["tp"] / (confusion["tp"] + confusion["fp"])
        if (confusion["tp"] + confusion["fp"])
        else 0.0
    )
    recall = (
        confusion["tp"] / (confusion["tp"] + confusion["fn"])
        if (confusion["tp"] + confusion["fn"])
        else 0.0
    )
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}
