"""
Fraud detection orchestrator — engine integration.

Drives fraud detection through TheRollingPipelines runtime:
  1. Loads runtime config and registry
  2. Selector picks a fraud detector pattern by query relevance
  3. Pattern handler is dispatched with the pattern's config block
  4. Predictions scored against ground-truth `fraud_flag` (precision/recall/F1)
  5. Optional: compare-mode runs *all* fraud detector patterns side-by-side
     so the best can be promoted

This is the closing of the loop the architecture diagram describes:
    Dataset → Features → Detector → Evaluation → (future) Promotion
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make `fraud`, `datasets`, and `runtime` importable
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
RUNTIME_REPO = Path.home() / "LocalDocuments" / "Projects" / "TheRollingPipelines"
sys.path.insert(0, str(RUNTIME_REPO))

from runtime import load_config  # noqa: E402
from runtime.learning.updater import Updater  # noqa: E402
from runtime.registry import PatternRegistry  # noqa: E402
from runtime.selector import Selector  # noqa: E402

from fraud.features import build_features  # noqa: E402
from fraud.load import load_transactions  # noqa: E402


# Patterns whose handlers actually return scored DataFrames
DETECTOR_PREFIX = "fraud-rule-detector"


def _resolve_paths(config) -> None:
    """Resolve runtime config paths against the runtime repo, not cwd."""
    if not Path(config.registry_path).is_absolute():
        config.registry_path = str(RUNTIME_REPO / config.registry_path)
    if not Path(config.promotion.audit_log).is_absolute():
        config.promotion.audit_log = str(RUNTIME_REPO / config.promotion.audit_log)


def _confusion(df) -> dict[str, int]:
    truth = df["fraud_flag"].astype(bool)
    pred  = df["predicted_fraud"].astype(bool)
    return {
        "tp": int(( truth &  pred).sum()),
        "fp": int((~truth &  pred).sum()),
        "fn": int(( truth & ~pred).sum()),
        "tn": int((~truth & ~pred).sum()),
    }


def _metrics(c: dict[str, int]) -> dict[str, float]:
    p = c["tp"] / (c["tp"] + c["fp"]) if (c["tp"] + c["fp"]) else 0.0
    r = c["tp"] / (c["tp"] + c["fn"]) if (c["tp"] + c["fn"]) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"precision": p, "recall": r, "f1": f}


def _run_one_detector(pattern, df, config_override: dict | None = None) -> dict:
    fn = pattern.resolve_handler()
    if fn is None:
        return {"error": f"no handler for {pattern.id}"}
    cfg = {**pattern.config, **(config_override or {})}
    scored = fn(df, **cfg)
    c = _confusion(scored)
    m = _metrics(c)
    return {
        "pattern_id": pattern.id,
        "config":     cfg,
        "confusion":  c,
        "metrics":    m,
        "n_predicted": int(scored["predicted_fraud"].sum()),
    }


def _record_score(updater: Updater, pattern_id: str, f1: float) -> None:
    """Persist an F1 score as the pattern's new EMA-updated confidence."""
    existing = updater.load_registry()
    ok = updater.update_pattern_score(pattern_id, f1, existing)
    if ok:
        print(f"  ↺ {pattern_id}: recorded f1={f1:.3f} (EMA updated)")
    else:
        print(f"  ✗ {pattern_id}: could not record score (protected? not found?)")


def _tune_v1(pattern, df) -> tuple[dict, dict]:
    """2D grid sweep (spike_threshold × same_ts_threshold) for v1."""
    print(f"\n=== tuning {pattern.id}: 2D grid (spike × same_ts) ===")
    spike_grid = [20_000, 30_000, 40_000, 50_000, 75_000, 100_000, 150_000, 250_000]
    burst_grid = [3, 4, 5]

    best_f1     = -1.0
    best_config: dict = {}
    best_metrics: dict = {}

    print(f"   spike   burst  precision  recall  f1")
    for spike in spike_grid:
        for burst in burst_grid:
            override = {"spike_threshold": spike, "same_ts_threshold": burst}
            r = _run_one_detector(pattern, df, override)
            m = r["metrics"]
            marker = ""
            if m["f1"] > best_f1:
                best_f1 = m["f1"]
                best_config = override.copy()
                best_metrics = m
                marker = "  ←"
            print(f"  {spike:>6d}  {burst:>5d}  {m['precision']:.3f}      "
                  f"{m['recall']:.3f}   {m['f1']:.3f}{marker}")
    return best_config, best_metrics


def _tune_v3(pattern, df) -> tuple[dict, dict]:
    """1D sweep score_threshold for v3 (weights held at default).

    With default weights (0.4/0.4/0.2), strict > 0.4 → needs ≥2 signals,
    > 0.3 → any single spike or velocity also fires (anomaly alone still
    not enough at weight 0.2).
    """
    print(f"\n=== tuning {pattern.id}: score_threshold sweep ===")
    best_f1     = -1.0
    best_config: dict = {}
    best_metrics: dict = {}
    for t in [round(0.1 + 0.05 * i, 2) for i in range(11)]:  # 0.10 .. 0.60
        r = _run_one_detector(pattern, df, {"score_threshold": t})
        m = r["metrics"]
        c = r["confusion"]
        marker = ""
        if m["f1"] > best_f1:
            best_f1 = m["f1"]
            best_config = {"score_threshold": t}
            best_metrics = m
            marker = "  ←"
        print(f"  t={t:.2f}  precision={m['precision']:.3f}  "
              f"recall={m['recall']:.3f}  f1={m['f1']:.3f}  "
              f"(TP={c['tp']} FP={c['fp']} FN={c['fn']}){marker}")
    return best_config, best_metrics


def _tune_v2(pattern, df) -> tuple[dict, dict]:
    """1D sweep account_zscore_threshold for v2."""
    print(f"\n=== tuning {pattern.id}: account_zscore_threshold sweep ===")
    best_f1    = -1.0
    best_config: dict = {}
    best_metrics: dict = {}
    for t in [round(2.0 + 0.5 * i, 2) for i in range(13)]:  # 2.0 .. 8.0
        r = _run_one_detector(pattern, df, {"account_zscore_threshold": t})
        m = r["metrics"]
        marker = ""
        if m["f1"] > best_f1:
            best_f1 = m["f1"]
            best_config = {"account_zscore_threshold": t}
            best_metrics = m
            marker = "  ←"
        print(f"  z={t:.2f}  precision={m['precision']:.3f}  "
              f"recall={m['recall']:.3f}  f1={m['f1']:.3f}{marker}")
    return best_config, best_metrics


_TUNERS = {
    "fraud-rule-detector-v1": _tune_v1,
    "fraud-rule-detector-v2": _tune_v2,
    "fraud-rule-detector-v3": _tune_v3,
}


def run(
    query:   str,
    *,
    compare: bool = False,
    tune:    str | None = None,
    record:  bool = False,
    apply:   bool = False,
) -> int:
    config = load_config(str(RUNTIME_REPO / "runtime" / "runtime.yaml"))
    _resolve_paths(config)
    config.promotion.enabled = False  # don't run the engine's full promotion loop
    registry = PatternRegistry(config)
    selector = Selector(config)
    updater  = Updater(config) if (record or apply) else None

    # Filter to fraud detectors only
    active    = registry.filter_by_tier("exploration")
    detectors = [p for p in active if p.id.startswith(DETECTOR_PREFIX)]
    if not detectors:
        print("no fraud detector patterns registered")
        return 1

    print(f"Loading transactions from DuckDB...")
    df = load_transactions()
    print(f"  loaded {len(df):,} rows")

    print("Building features...")
    df = build_features(df)

    if tune:
        target = tune  # pattern id (cli sets this to v1 by default)
        pattern = next((p for p in detectors if p.id == target), None)
        if pattern is None:
            print(f"{target!r} not registered")
            return 1
        tuner = _TUNERS.get(target)
        if tuner is None:
            print(f"no tuner registered for {target!r}")
            return 1
        best_config, best_metrics = tuner(pattern, df)
        print(f"\n  → best: {best_config}  f1={best_metrics['f1']:.3f}")
        if apply:
            existing = updater.load_registry()
            for r in existing:
                if r["id"] == target:
                    r["config"].update(best_config)
                    print(f"  ✏ wrote {best_config} into {r['id']}")
                    break
            updater.save_registry(existing)
        return 0

    if compare:
        print(f"\n=== compare mode: scoring all {len(detectors)} fraud detectors ===\n")
        results = []
        for p in detectors:
            r = _run_one_detector(p, df)
            results.append(r)

        results.sort(key=lambda r: r["metrics"]["f1"], reverse=True)
        for r in results:
            m = r["metrics"]
            c = r["confusion"]
            print(f"  {r['pattern_id']:25s}  precision={m['precision']:.3f}  "
                  f"recall={m['recall']:.3f}  f1={m['f1']:.3f}  "
                  f"(TP={c['tp']} FP={c['fp']} FN={c['fn']})")
        print(f"\n  → best: {results[0]['pattern_id']}  f1={results[0]['metrics']['f1']:.3f}")

        if record:
            print("\n=== recording F1 scores into registry (EMA-updated) ===")
            for r in results:
                _record_score(updater, r["pattern_id"], r["metrics"]["f1"])
        return 0

    print(f"\nEngine: query={query!r}")
    chosen = selector.select(query, detectors)
    if chosen:
        pattern = chosen[0]
        print(f"  Selector chose: {pattern.id}")
    else:
        # Inside the orchestrator we've already filtered to fraud detectors,
        # so the Selector's relevance gate is too aggressive — fall back to
        # the highest-confidence detector.
        pattern = max(detectors, key=lambda p: p.confidence)
        print(f"  Selector found no relevance match — falling back to "
              f"highest-confidence detector: {pattern.id}")
    print(f"  config:         {pattern.config}")

    result = _run_one_detector(pattern, df)
    if "error" in result:
        print(result["error"])
        return 1

    c, m = result["confusion"], result["metrics"]
    print(f"\n--- evaluation against ground truth ---")
    print(f"  TP={c['tp']:>5}  FP={c['fp']:>5}")
    print(f"  FN={c['fn']:>5}  TN={c['tn']:>5}")
    print(f"\n  precision = {m['precision']:.3f}")
    print(f"  recall    = {m['recall']:.3f}")
    print(f"  f1        = {m['f1']:.3f}")

    if record:
        print()
        _record_score(updater, pattern.id, m["f1"])
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="Detect fraud in SME transactions")
    ap.add_argument("--compare", action="store_true",
                    help="Score every fraud detector side-by-side")
    ap.add_argument("--tune", nargs="?", const="fraud-rule-detector-v1",
                    metavar="PATTERN_ID",
                    help="Run grid sweep for the given detector pattern id "
                         "(default: fraud-rule-detector-v1)")
    ap.add_argument("--record",  action="store_true",
                    help="Record F1 into registry as the pattern's EMA score")
    ap.add_argument("--apply",   action="store_true",
                    help="With --tune: write best threshold into the pattern config")
    args = ap.parse_args()
    raise SystemExit(run(
        args.query,
        compare=args.compare,
        tune=args.tune,
        record=args.record,
        apply=args.apply,
    ))
