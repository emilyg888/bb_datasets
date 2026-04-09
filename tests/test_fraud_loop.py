from pathlib import Path

from fraud.detector import detect_fraud
from fraud.load import load_registered_transactions
from fraud.loop import PhaseResult, append_phase_results, prepare_dataset_frame, run_detector_phase


class _Pattern:
    id = "test-detector"
    config = {}
    confidence = 0.5

    def resolve_handler(self):
        return detect_fraud


def test_load_registered_transactions_normalizes_detector_columns():
    df = load_registered_transactions("fraud_gold")

    assert "txn_id" in df.columns
    assert "fraud_flag" in df.columns
    assert "transaction_id" not in df.columns
    assert df["fraud_flag"].tolist() == [False, True, True, False]


def test_prepare_dataset_frame_builds_required_features():
    df = prepare_dataset_frame("fraud_gold")

    assert {"abs_amount", "same_ts_count", "z_score", "account_zscore"} <= set(df.columns)


def test_run_detector_phase_scores_registered_dataset():
    result = run_detector_phase(
        _Pattern(),
        prepare_dataset_frame("fraud_gold"),
        phase="validation",
        dataset_id="fraud_gold",
    )

    assert result.error is None
    assert result.pattern_id == "test-detector"
    assert result.dataset_id == "fraud_gold"
    assert result.n_rows == 4
    assert set(result.metrics) == {"precision", "recall", "f1"}


def test_append_phase_results_writes_tsv_rows(tmp_path):
    log_path = tmp_path / "phase_runs.tsv"
    results = [
        PhaseResult(
            phase="exploration",
            dataset_id="fraud_v1",
            pattern_id="detector-a",
            config={"x": 1},
            confusion={"tp": 1, "fp": 0, "fn": 1, "tn": 1},
            metrics={"precision": 1.0, "recall": 0.5, "f1": 0.666666},
            n_rows=3,
            n_predicted=1,
        ),
        PhaseResult(
            phase="validation",
            dataset_id="fraud_gold",
            pattern_id="detector-a",
            config={"x": 1},
            confusion={"tp": 2, "fp": 0, "fn": 0, "tn": 2},
            metrics={"precision": 1.0, "recall": 1.0, "f1": 1.0},
            n_rows=4,
            n_predicted=2,
        ),
    ]

    append_phase_results(results, query="Detect fraud", phase_log_path=log_path)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("timestamp_utc\tquery\tphase\tdataset_id")
    assert "\texploration\tfraud_v1\tdetector-a\t" in lines[1]
    assert "\tvalidation\tfraud_gold\tdetector-a\t" in lines[2]
