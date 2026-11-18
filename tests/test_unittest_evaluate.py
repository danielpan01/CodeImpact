"""Validate both v4 policies and the separately frozen discovery receipt."""

import json
import shutil
from pathlib import Path

import pytest

from codeimpact import unittest_evaluate as replay
from codeimpact.discovery import CURRENT_POLICY
from codeimpact.v4_evaluate import DIRECTORY, SUCCESSOR, inventories, stable_bytes, validate_frozen

ROOT = Path(__file__).parents[1]
DATA = ROOT / DIRECTORY
EXTENSION = ROOT / SUCCESSOR
ICECREAM = {
    "icecream_local_time": (7, 22, 3),
    "icecream_source_error": (1, 26, 5),
}


@pytest.fixture
def successor(tmp_path):
    return shutil.copytree(EXTENSION, tmp_path / "successor")


def test_successor_replay_checks_exact_ids_and_revision_evidence():
    report = replay.evaluate_unittest(DATA)
    assert report["evaluation"]["regressions"] == []
    assert report["discovery_policy"] == CURRENT_POLICY
    assert report["independent_review"] == "pending"
    assert report["original_summary"]["outside_discovery_count"] == 64
    assert report["summary"]["outside_discovery_count"] == 0
    assert report["summary"]["unclassified_unselected_count"] == 0
    assert (report["summary"]["test_count"], report["summary"]["selected_count"]) == (169, 156)
    assert report["summary"]["metrics"]["counts"] == {
        "tp": 27,
        "fn": 0,
        "fp": 105,
        "tn": 13,
        "unclassified_recommendations": 24,
    }
    assert set(report["newly_discovered"]) == set(ICECREAM)
    for row in report["evaluation"]["cases"]:
        cid = row["case"]["id"]
        if cid not in ICECREAM:
            continue
        assert len(report["newly_discovered"][cid]) == 32
        assert (
            tuple(
                row["results"]["metrics"]["counts"][key]
                for key in ("tp", "fp", "unclassified_recommendations")
            )
            == ICECREAM[cid]
        )
        recommendations = row["analysis"]["recommendations"]
        assert {rec["symbol"] for rec in recommendations} == set(report["newly_discovered"][cid])
        assert sum("TestIceCreamInstall." in rec["symbol"] for rec in recommendations) == 2
        for rec in recommendations:
            path = rec["evidence_path"]
            assert rec["path_revision"] == "both"
            assert rec["reason"] == "Conservative module/import dependency"
            assert path[0] == rec["symbol"]
            assert path[-2:] == ["icecream/__init__.py::<module>", "icecream/icecream.py::<module>"]
            if rec["symbol"].endswith(".testDifferentName"):
                assert len(path) == 3
            else:
                assert path[1] == rec["symbol"].split("::")[0] + "::<module>"
                assert len(path) == 4


def test_successor_rejects_a_changed_label_file(successor):
    with (successor / replay.LABELS).open("a") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="Frozen discovery labels changed"):
        replay.evaluate_unittest(DATA, successor=successor)


@pytest.mark.parametrize("edit", ["range", "inventory"])
def test_successor_rejects_invalid_label_inventory_before_expanded_analysis(edit, monkeypatch):
    _, cases, historical = validate_frozen(DATA)
    receipt = replay.DiscoveryLabels.model_validate_json((EXTENSION / replay.LABELS).read_bytes())
    first_case = receipt.cases["icecream_local_time"]
    first_id = next(iter(first_case.labels))
    if edit == "range":
        first_case.labels[first_id].line += 1
    else:
        first_case.labels.pop(first_id)

    def forbidden(*_args, **_kwargs):
        pytest.fail("ran expanded analysis before validating labels")

    monkeypatch.setattr(replay, "evaluate_real", forbidden)
    monkeypatch.setattr(replay, "validate_frozen", lambda _: (None, cases, historical))
    message = "Label source range mismatch" if edit == "range" else "Missing new labels"
    with pytest.raises(ValueError, match=message):
        replay.measure(DATA, receipt)


def test_successor_replay_fails_on_measurement_drift(successor):
    path = successor / replay.BASELINE
    baseline = json.loads(path.read_text())
    baseline["report_sha256"] = "0" * 64
    path.write_bytes(stable_bytes(baseline))
    report = replay.evaluate_unittest(DATA, successor=successor)
    assert report["evaluation"]["regressions"] == [
        "v4 unittest discovery: report differs from the recorded measurement"
    ]


def test_current_inventory_retains_frozen_non_target_cases():
    _, cases, historical = validate_frozen(DATA)
    current = inventories(cases, policy=CURRENT_POLICY)
    assert {cid for cid in current if current[cid] != historical[cid]} == set(ICECREAM)


def test_report_cannot_overwrite_successor_inputs():
    path = EXTENSION / replay.BASELINE
    assert replay.main(["--output", str(path)]) == 2
