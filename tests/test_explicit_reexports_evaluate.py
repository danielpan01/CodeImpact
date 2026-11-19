"""Strict replay of the re-export evidence delta."""

import json
from pathlib import Path

from codeimpact.explicit_reexports_evaluate import evaluate_reexports
from codeimpact.v4_evaluate import DIRECTORY, REEXPORTS_SUCCESSOR, stable_bytes

ROOT = Path(__file__).parents[1]
DATA = ROOT / DIRECTORY
BASELINE = ROOT / REEXPORTS_SUCCESSOR / "baseline.json"


def test_frozen_humanize_stays_conservative():
    report = evaluate_reexports(DATA)
    assert report["evaluation"]["regressions"] == []
    assert report["independent_review"] == "pending"
    assert report["selection_policy"] == "explicit-reexports-v1"
    observed = report["recommendation_delta"]
    assert observed["added"] == observed["removed"] == []
    assert observed["evidence_replacements"] == report["added_call_evidence"] == {}
    case = next(c for c in report["cases"] if c["id"] == "humanize_small_delta")
    assert case["selected_test_ids"] == observed["retained"]
    assert case["test_count"] == 33 and len(observed["retained"]) == 20
    assert case["reason_counts"] == {
        "Conservative module/import dependency": 19,
        "Test itself changed": 1,
    }


def test_reexport_replay_rejects_delta_drift(tmp_path):
    baseline = json.loads(BASELINE.read_bytes())
    baseline["recommendation_delta"]["retained"].pop()
    (tmp_path / BASELINE.name).write_bytes(stable_bytes(baseline))
    report = evaluate_reexports(DATA, successor=tmp_path)
    assert report["evaluation"]["regressions"] == [
        "v4 explicit re-exports: report differs from the recorded measurement"
    ]
