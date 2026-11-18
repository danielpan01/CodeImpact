"""V4 replay integrity, evidence validation and a separate review workflow."""

import importlib
import json
import shutil
import socket
import subprocess
from pathlib import Path

import pytest

from codeimpact import evaluate, v4_evaluate
from codeimpact.fresh_evaluate import file_hash
from codeimpact.models import Snapshot

ROOT = Path(__file__).parents[1]
DATA = ROOT / v4_evaluate.DIRECTORY
CASE = "humanize_intcomma_locale"


@pytest.fixture
def review_real_v4(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT))
    return importlib.import_module("scripts.review_real_v4")


@pytest.fixture
def dataset(tmp_path):
    return Path(shutil.copytree(DATA, tmp_path / "real-v4"))


def edit(path, fn):
    obj = json.loads(path.read_text())
    fn(obj)
    path.write_bytes(v4_evaluate.stable_bytes(obj))


def test_v4_offline_measurement_validates_all_paths(monkeypatch):
    def forbidden(*_a, **_kw):
        pytest.fail("offline replay attempted network or subprocess")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    report = v4_evaluate.evaluate_v4(DATA)
    assert report["evaluation"]["regressions"] == []
    assert len(report["first_regressions"]) == 6
    assert report["independent_review"] == "pending"
    assert report["reference_commit"] == v4_evaluate.REFERENCE
    summary = report["summary"]
    assert summary["test_count"] == 105
    assert summary["test_shaped_definition_count"] == 169
    assert summary["outside_discovery_count"] == 64
    assert summary["selected_count"] == 92
    assert summary["unclassified_test_count"] == 16
    assert summary["unclassified_unselected_count"] == 0
    assert summary["reason_counts"] == {
        "Conservative module/import dependency": 87,
        "Test itself changed": 5,
    }
    assert summary["metrics"]["counts"] == {
        "tp": 19,
        "fp": 57,
        "fn": 0,
        "tn": 13,
        "unclassified_recommendations": 16,
    }
    assert report["repositories"]["gruns/icecream"]["metrics"]["recall"]["value"] is None
    assert all(
        "elapsed_ms" not in item["analysis"]["stats"] for item in report["evaluation"]["cases"]
    )


def test_discovery_audit_distinguishes_filename_function_and_compound_rules():
    snapshot = Snapshot(
        files={
            "test.py": "def test_current(): pass\n",
            "tests.py": "def test_filename(): pass\n",
            "test_modes.py": (
                "class Example:\n"
                "    def testCamelCase(self): pass\n"
                "    if flag:\n"
                "        def test_conditional(self): pass\n"
            ),
        }
    )
    audit = v4_evaluate.source_inventory(snapshot)
    assert audit["discovered_ids"] == ["test.py::test_current"]
    assert audit["outside_discovery"] == {
        "tests.py::test_filename": "unsupported_filename",
        "test_modes.py::Example.testCamelCase": "unsupported_function_name",
        "test_modes.py::Example.test_conditional": "compound_statement",
    }
    assert audit["test_shaped_definition_count"] == 4


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda d: d["request"]["head"]["files"].__setitem__("setup.py", "pass\n"),
            "Source blob hash/size mismatch",
        ),
        (
            lambda d: d["request"]["head"]["files"].pop("setup.py"),
            "complete supported Python tree",
        ),
        (
            lambda d: d["expected_affected"].pop("tests/test_number.py::test_intcomma"),
            "Every head test needs an explicit label",
        ),
        (
            lambda d: d["unclassified"].__setitem__(
                "tests/test_number.py::test_intcomma", "overlap"
            ),
            "labels must be disjoint",
        ),
    ],
)
def test_invalid_cases_fail_before_analysis(dataset, monkeypatch, mutate, message):
    edit(dataset / f"cases/{CASE}.json", mutate)
    monkeypatch.setattr(
        v4_evaluate, "evaluate_real", lambda *_a, **_kw: pytest.fail("ran analysis")
    )
    with pytest.raises(ValueError, match=message):
        v4_evaluate.evaluate_v4(dataset)


def test_tampered_provenance_review_metadata_is_rejected(dataset):
    edit(
        dataset / f"provenance/{CASE}.json",
        lambda d: d["label_review"].update(status="reviewed"),
    )
    with pytest.raises(ValueError, match="Reviewed labels need a named reviewer"):
        v4_evaluate.evaluate_v4(dataset)


def test_source_only_pack_regenerates_and_freeze_detects_changes(
    dataset, monkeypatch, review_real_v4
):
    monkeypatch.setattr(evaluate, "analyze", lambda *_a: pytest.fail("ran analysis"))
    path = dataset / "REVIEW.md"
    assert review_real_v4.build_pack(dataset) == path.read_text()
    assert "unsupported_function_name" in path.read_text()
    with path.open("a") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="Frozen v4 input changed: REVIEW.md"):
        v4_evaluate.evaluate_v4(dataset)


def test_v4_rejects_bad_revision_evidence(monkeypatch):
    analyze = evaluate.analyze

    def corrupt(request):
        report = analyze(request)
        if report.recommendations:
            rec = report.recommendations[0]
            rec.path_revision = "after" if rec.path_revision == "both" else "both"
        return report

    monkeypatch.setattr(evaluate, "analyze", corrupt)
    with pytest.raises(ValueError, match="path revision intersection"):
        v4_evaluate.evaluate_v4(DATA)


def test_recorded_discrepancies_cannot_drift(dataset):
    edit(
        dataset / "baseline.json",
        lambda d: d["annotations"][CASE]["known_discrepancies"]["false_positives"].clear(),
    )
    assert (
        v4_evaluate.main(["--corpus", str(dataset), "--output", str(dataset.parent / "r.json")])
        == 1
    )
    report = json.loads((dataset.parent / "r.json").read_text())
    assert report["evaluation"]["regressions"] == [
        f"{CASE}: discrepancies differ from the v4 baseline"
    ]


def test_first_report_drift_fails_even_with_same_classifications(monkeypatch):
    evaluate_real = v4_evaluate.evaluate_real

    def changed(*args, **kw):
        report = evaluate_real(*args, **kw)
        rec = report["evaluation"]["cases"][0]["analysis"]["recommendations"][0]
        rec["score"] += 1
        return report

    monkeypatch.setattr(v4_evaluate, "evaluate_real", changed)
    assert v4_evaluate.evaluate_v4(DATA)["evaluation"]["regressions"] == [
        "v4: report differs from the frozen first measurement"
    ]


@pytest.fixture
def record():
    sid = "tests/test_number.py::test_intcomma"
    provenance = json.loads((DATA / f"provenance/{CASE}.json").read_text())
    return {
        "schema_version": "1.0",
        "case": CASE,
        "frozen_inputs_sha256": file_hash(DATA / v4_evaluate.FREEZE),
        "labels_sha256": provenance["label_review"]["labels_sha256"],
        "reviewer": "Synthetic Test Reviewer",
        "reviewed_on": "2026-11-17",
        "review_reference": "fixture for validator test",
        "discovery_notes": "Synthetic check of one discovered definition.",
        "decisions": {
            sid: {
                "original": "affected",
                "proposed": "uncertain",
                "rationale": "Synthetic disagreement.",
                "evidence": [
                    {
                        "revision": "head",
                        "path": "src/humanize/number.py",
                        "line": 70,
                        "end_line": 79,
                    }
                ],
            }
        },
    }


def test_review_record_does_not_change_frozen_labels(record, review_real_v4):
    before = file_hash(DATA / f"cases/{CASE}.json")
    result = review_real_v4.validate_review(
        DATA, review_real_v4.ReviewRecord.model_validate(record)
    )
    assert len(result["remaining_ids"]) == 33
    assert result["proposed_revisions"] == ["tests/test_number.py::test_intcomma"]
    assert file_hash(DATA / f"cases/{CASE}.json") == before


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("reviewed_on", "not-a-date", "reviewed_on"),
        ("reviewer", "   ", "reviewer"),
        ("labels_sha256", "0" * 64, "Review labels differ"),
        ("frozen_inputs_sha256", "0" * 64, "Review freeze differs"),
    ],
)
def test_bad_review_metadata(record, field, value, message, review_real_v4):
    record[field] = value
    with pytest.raises(ValueError, match=message):
        review_real_v4.validate_review(DATA, review_real_v4.ReviewRecord.model_validate(record))


def test_bad_review_span(record, review_real_v4):
    decision = record["decisions"]["tests/test_number.py::test_intcomma"]
    decision["evidence"][0]["end_line"] = 100000
    with pytest.raises(ValueError, match="Invalid pinned source range"):
        review_real_v4.validate_review(DATA, review_real_v4.ReviewRecord.model_validate(record))
