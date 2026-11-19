"""Replay accepts the measured row result and rejects a changing receipt."""

import json
from pathlib import Path

from codeimpact.parameter_rows_evaluate import evaluate_rows
from codeimpact.v4_evaluate import DIRECTORY, PARAMETER_ROWS_SUCCESSOR, stable_bytes

ROOT = Path(__file__).parents[1]
DATA = ROOT / DIRECTORY
BASELINE = ROOT / PARAMETER_ROWS_SUCCESSOR / "baseline.json"


def test_humanize_replay_keeps_the_opaque_initialization_paths():
    report = evaluate_rows(DATA)
    assert report["evaluation"]["regressions"] == []
    assert report["selection_policy"] == "parameter-rows-v1"
    assert report["independent_review"] == "pending"
    delta = report["humanize_delta"]
    assert delta["added"] == delta["removed"] == []
    assert delta["evidence_replacements"] == {}
    case = next(row for row in report["cases"] if row["id"] == "humanize_small_delta")
    assert delta["retained"] == case["selected_test_ids"]
    assert len(delta["retained"]) == 20
    assert case["metrics"]["counts"] == {
        "tp": 5,
        "fp": 15,
        "fn": 0,
        "tn": 13,
        "unclassified_recommendations": 0,
    }


def test_humanize_replay_rejects_delta_drift(tmp_path):
    raw = json.loads(BASELINE.read_bytes())
    raw["humanize_delta"]["retained"].pop()
    (tmp_path / BASELINE.name).write_bytes(stable_bytes(raw))
    report = evaluate_rows(DATA, successor=tmp_path)
    assert report["evaluation"]["regressions"] == [
        "v4 parameter rows: report differs from the recorded measurement"
    ]
