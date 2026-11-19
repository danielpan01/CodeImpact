"""Timestamp replay independently validates the incumbent and successor."""

import json
from pathlib import Path

from codeimpact.v4_evaluate import DIRECTORY, VARIADIC_SUCCESSOR, stable_bytes
from codeimpact.variadic_evaluate import evaluate_variadic

ROOT = Path(__file__).parents[1]
DATA = ROOT / DIRECTORY
RECEIPT = ROOT / VARIADIC_SUCCESSOR / "baseline.json"


def test_timestamp_replay_preserves_the_unproved_paths():
    report = evaluate_variadic(DATA)
    assert report["evaluation"]["regressions"] == []
    assert report["independent_review"] == "pending"
    assert report["selection_policy"] == "variadic-dispatch-v1"
    delta = report["timestamp_delta"]
    assert delta["removed"] == delta["added"] == delta["evidence_replaced"] == []
    assert len(delta["retained"]) == 32
    timestamp = next(row for row in report["cases"] if row["id"] == "icecream_local_time")
    assert delta["retained"] == timestamp["selected_test_ids"]
    assert timestamp["metrics"]["counts"] == {
        "tp": 7,
        "fp": 22,
        "fn": 0,
        "tn": 0,
        "unclassified_recommendations": 3,
    }


def test_timestamp_replay_rejects_drift(tmp_path):
    raw = json.loads(RECEIPT.read_bytes())
    raw["timestamp_delta"]["retained"].pop()
    (tmp_path / "baseline.json").write_bytes(stable_bytes(raw))
    report = evaluate_variadic(DATA, successor=tmp_path)
    assert report["evaluation"]["regressions"] == [
        "v4 variadic dispatch: report differs from the recorded measurement"
    ]
