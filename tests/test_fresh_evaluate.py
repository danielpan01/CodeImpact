"""Frozen fresh-source evaluation: integrity, offline execution and honest drift."""

import json
import shutil
from pathlib import Path

import pytest

from codeimpact.fresh_evaluate import (
    BASELINE_FILE,
    CURRENT_SOURCES,
    PARTIAL_BASELINE_FILE,
    evaluate_fresh,
    main,
    validate_frozen,
)

ROOT = Path(__file__).parents[1]
DATA = ROOT / "corpus/real-v2"


@pytest.fixture
def dataset(tmp_path):
    target = tmp_path / "fresh"
    shutil.copytree(DATA, target)
    return target


def edit(root, relative, mutate):
    path = root / relative
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data))


def test_reference_and_preanalysis_freeze():
    frozen = validate_frozen(DATA)
    assert frozen.reference_commit == "bef99db1bbc144ac399ecb3f537269293fe3f22e"
    assert len(frozen.cases) == 6
    assert len(frozen.analyzer_sha256) == 6


def test_missing_label_is_invalid(dataset):
    edit(dataset, "cases/atomicwrites_path.json", lambda d: d["expected_affected"].popitem())
    with pytest.raises(ValueError, match="explicit label"):
        validate_frozen(dataset)


def test_overlapping_label_is_invalid(dataset):
    edit(
        dataset,
        "cases/atomicwrites_path.json",
        lambda d: d["expected_unaffected"].update(d["expected_affected"]),
    )
    with pytest.raises(ValueError, match="disjoint"):
        validate_frozen(dataset)


@pytest.mark.parametrize(
    ("relative", "mutate", "error"),
    [
        (
            "cases/atomicwrites_path.json",
            lambda d: d["request"]["head"]["files"].pop("setup.py"),
            "complete",
        ),
        (
            "cases/atomicwrites_path.json",
            lambda d: d["request"]["head"]["files"].__setitem__("setup.py", "# tampered"),
            "hash",
        ),
        (
            "provenance/atomicwrites_path.json",
            lambda d: d["head"]["tree"].__setitem__("truncated", True),
            "truncated",
        ),
        (
            "provenance/atomicwrites_path.json",
            lambda d: d["head"]["license"].__setitem__("text", "changed license"),
            "license",
        ),
        (
            "provenance/atomicwrites_path.json",
            lambda d: d["label_review"].__setitem__("status", "reviewed"),
            "reviewer",
        ),
        (
            "provenance/atomicwrites_path.json",
            lambda d: d["label_review"].__setitem__("reviewer", "Invented review"),
            "Draft labels",
        ),
        (
            "provenance/atomicwrites_path.json",
            lambda d: d["head"]["commit"]["parents"][0].__setitem__("sha", "0" * 40),
            "parent",
        ),
        (
            "frozen-inputs.json",
            lambda d: d["analyzer_sha256"].pop("src/codeimpact/arguments.py"),
            "source inventory",
        ),
        (
            "frozen-inputs.json",
            lambda d: d["analyzer_sha256"].__setitem__("../outside", "0" * 64),
            "source inventory",
        ),
        (
            "frozen-inputs.json",
            lambda d: d.__setitem__("selection_sha256", "0" * 64),
            "selection",
        ),
    ],
)
def test_invalid_input_fails_before_analysis(dataset, relative, mutate, error, monkeypatch):
    from codeimpact import fresh_evaluate

    def forbidden(*args, **kwargs):
        raise AssertionError("invalid input reached the analyzer")

    edit(dataset, relative, mutate)
    monkeypatch.setattr(fresh_evaluate, "evaluate_real", forbidden)
    with pytest.raises(ValueError, match=error):
        evaluate_fresh(dataset)


def test_source_or_review_freeze_change_rejected(dataset, tmp_path):
    project = tmp_path / "project"
    validate_frozen(dataset)
    for relative in CURRENT_SOURCES:
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    path = project / "src/codeimpact/analyzer.py"
    path.write_bytes(path.read_bytes() + b"\n# changed engine\n")
    with pytest.raises(ValueError, match="Current analyzer mismatch"):
        validate_frozen(dataset, project)
    (dataset / "REVIEW.md").write_text("Replaced review pack")
    with pytest.raises(ValueError, match="review pack"):
        validate_frozen(dataset)


def test_coordinated_label_hash_update_cannot_rewrite_first_labels(dataset):
    from codeimpact.corpus import CorpusCase
    from codeimpact.real_evaluate import label_hash

    path = dataset / "cases/atomicwrites_path.json"
    data = json.loads(path.read_text())
    sid = next(iter(data["expected_affected"]))
    data["expected_affected"][sid] = "A different rationale after seeing recommendations"
    path.write_text(json.dumps(data))
    updated = label_hash(CorpusCase.model_validate(data))
    edit(
        dataset,
        "provenance/atomicwrites_path.json",
        lambda d: d["label_review"].__setitem__("labels_sha256", updated),
    )
    with pytest.raises(ValueError, match="Frozen labels mismatch"):
        validate_frozen(dataset)


def test_offline_source_as_data_and_honest_first_measurement(monkeypatch):
    import builtins
    import socket
    import subprocess

    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        assert name.split(".")[0] not in {"atomicwrites", "slugify", "cachetools"}
        return original(name, *args, **kwargs)

    def forbidden(*args, **kwargs):
        raise AssertionError("offline evaluation attempted network/process activity")

    monkeypatch.setattr(builtins, "__import__", guarded)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    report = evaluate_fresh(DATA)
    assert not report["first_measurement_matches"]
    assert report["current_measurement_matches"]
    assert report["previous_summary"]["metrics"]["counts"]["fp"] == 291
    assert report["original_summary"]["metrics"]["counts"]["fn"] == 44
    assert report["active_baseline"] == "argument-guards-v1"
    assert report["fresh_evaluation_schema_version"] == "3.0"
    assert report["evaluation"]["regressions"] == []
    summary = report["summary"]
    assert summary["test_count"] == 581
    assert summary["selected_count"] == 406
    assert summary["label_status_counts"] == {"draft": 6}
    assert summary["metrics"]["counts"] == {
        "tp": 109,
        "fn": 0,
        "fp": 284,
        "tn": 166,
        "unclassified_recommendations": 13,
    }
    assert summary["unclassified_test_count"] == 22
    assert report["uncertainty"]["overall"] == {"total": 22, "selected": 13, "unselected": 9}
    for case in report["cases"]:
        assert len(case["selected_test_ids"]) == case["selected_count"]
        assert sum(case["reason_counts"].values()) == case["selected_count"]
        assert case["unclassified_test_count"] >= case["unclassified_recommendation_count"]
        uncertainty = report["uncertainty"]["cases"][case["id"]]
        assert len(uncertainty["unselected_test_ids"]) == uncertainty["unselected"]
        assert uncertainty["selected"] + uncertainty["unselected"] == uncertainty["total"]
    for group in report["uncertainty"]["repositories"].values():
        assert group["selected"] + group["unselected"] == group["total"]
    descriptor = next(c for c in report["cases"] if c["id"] == "cachetools_descriptor")
    assert descriptor["metrics"]["recall"]["value"] is None  # zero classified positives


def test_source_only_review_pack_matches_freeze(monkeypatch):
    import importlib

    from codeimpact import evaluate

    def forbidden(*args, **kwargs):
        raise AssertionError("review generation invoked analyzer")

    monkeypatch.setattr(evaluate, "analyze", forbidden)
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    pack = importlib.import_module("review_real").review_pack(DATA)
    assert pack == (DATA / "REVIEW.md").read_text()
    assert pack.count("- [ ]") == 581
    assert pack.count("Label status: **draft**") == 6


def test_invalid_recommendation_evidence_fails(monkeypatch):
    from codeimpact import evaluate

    original = evaluate.analyze

    def corrupt(request):
        report = original(request)
        report.recommendations[0].evidence_edges[0] = "invented-edge"
        return report

    monkeypatch.setattr(evaluate, "analyze", corrupt)
    with pytest.raises(ValueError, match="Invalid analyzer report"):
        evaluate_fresh(DATA)


def test_discrepancy_drift_is_nonzero_without_relabeling(dataset, tmp_path, capsys):
    path = dataset / "cases/slugify_ascii.json"
    before = path.read_bytes()
    edit(
        dataset,
        BASELINE_FILE,
        lambda d: d["annotations"]["slugify_ascii"]["known_discrepancies"][
            "false_positives"
        ].clear(),
    )
    output = tmp_path / "result.json"
    assert main(["--corpus", str(dataset), "--output", str(output)]) == 1
    report = json.loads(output.read_text())
    assert report["current_measurement_matches"]
    assert report["evaluation"]["regressions"]
    assert "CHANGED" in capsys.readouterr().out
    assert path.read_bytes() == before


def test_current_measurement_drift_is_nonzero(dataset, tmp_path):
    edit(
        dataset,
        BASELINE_FILE,
        lambda d: d["measurement"]["summary"].__setitem__("selected_count", 0),
    )
    output = tmp_path / "result.json"
    assert main(["--corpus", str(dataset), "--output", str(output)]) == 1
    assert not json.loads(output.read_text())["current_measurement_matches"]


@pytest.mark.parametrize(
    ("relative", "mutate", "message"),
    [
        (
            "first-run.json",
            lambda d: d["measurement"]["summary"].__setitem__("selected_count", 0),
            "Original first-run measurement changed",
        ),
        (
            "cases/slugify_ascii.json",
            lambda d: d["known_discrepancies"]["false_negatives"].clear(),
            "Original case annotations changed",
        ),
        (
            BASELINE_FILE,
            lambda d: d["analyzer_sha256"].pop("src/codeimpact/partial_bindings.py"),
            "source inventory",
        ),
        (
            BASELINE_FILE,
            lambda d: d["analyzer_sha256"].__setitem__("../outside", "0" * 64),
            "source inventory",
        ),
        (BASELINE_FILE, lambda d: d["annotations"].pop("slugify_ascii"), "case inventory"),
    ],
)
def test_historical_baseline_and_current_receipt_tampering(dataset, relative, mutate, message):
    edit(dataset, relative, mutate)
    with pytest.raises(ValueError, match=message):
        evaluate_fresh(dataset)


def test_preserved_v2_files_are_byte_identical():
    import hashlib

    baseline = json.loads((DATA / BASELINE_FILE).read_text())
    assert len(baseline["historical_files_sha256"]) == 25
    for relative, expected in baseline["historical_files_sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative
    original = json.loads((DATA / "first-run.json").read_text())
    assert original["measurement"]["summary"]["metrics"]["counts"] == {
        "tp": 65,
        "fn": 44,
        "fp": 284,
        "tn": 166,
        "unclassified_recommendations": 13,
    }


def test_first_run_receipt_mismatch_is_invalid(dataset, tmp_path):
    edit(dataset, "first-run.json", lambda d: d.__setitem__("frozen_inputs_sha256", "0" * 64))
    assert main(["--corpus", str(dataset), "--output", str(tmp_path / "result.json")]) == 2
    assert not (tmp_path / "result.json").exists()


def test_output_cannot_overwrite_frozen_inputs(dataset):
    path = dataset / "frozen-inputs.json"
    original = path.read_bytes()
    assert main(["--corpus", str(dataset), "--output", str(path)]) == 2
    assert path.read_bytes() == original


def test_reversed_snapshot_inventory_keeps_report_identical(dataset):
    for path in (dataset / "cases").glob("*.json"):
        data = json.loads(path.read_text())
        for side in ("base", "head"):
            data["request"][side]["files"] = dict(reversed(data["request"][side]["files"].items()))
        path.write_text(json.dumps(data))
    assert evaluate_fresh(dataset) == evaluate_fresh(DATA)


def test_reference_datasets_and_reports_remain_unchanged():
    import hashlib

    from codeimpact.corpus import load_corpus
    from codeimpact.evaluate import evaluate
    from codeimpact.real_evaluate import evaluate_real

    receipt = json.loads((DATA / "preservation.json").read_text())
    for relative, expected in receipt["files_sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative
    reports = {
        "authored": evaluate(load_corpus(ROOT / "corpus/cases")).model_dump(mode="json"),
        "v1": evaluate_real(ROOT / "corpus/real"),
    }
    for key, report in reports.items():
        raw = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
        assert hashlib.sha256(raw).hexdigest() == receipt["reports_sha256"][key]


def test_ci_runs_all_offline_gates():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    for command in ("make evaluate", "make evaluate-real", "make evaluate-real-v2"):
        assert f"run: {command}\n" in workflow
    assert "capture_real.py" not in workflow


def test_fresh_metadata_total_budget(monkeypatch):
    from codeimpact import fresh_evaluate

    monkeypatch.setattr(fresh_evaluate, "MAX_CORPUS_BYTES", 1)
    with pytest.raises(ValueError, match="total size limit"):
        evaluate_fresh(DATA)


def test_first_run_symlink_rejected(dataset, tmp_path):
    path = dataset / "first-run.json"
    outside = tmp_path / "initial.json"
    path.rename(outside)
    path.symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        evaluate_fresh(dataset)


def test_missing_first_run_fails_without_creating_baseline(dataset, tmp_path):
    path = dataset / "first-run.json"
    path.unlink()
    assert main(["--corpus", str(dataset), "--output", str(tmp_path / "result.json")]) == 2
    assert not path.exists()


@pytest.mark.parametrize("field", ["measurement", "explanation", "analyzer_sha256"])
def test_partial_baseline_cannot_be_rewritten(dataset, field, monkeypatch):
    from codeimpact import fresh_evaluate

    def forbidden(*args, **kwargs):
        raise AssertionError("tampered history reached analysis")

    monkeypatch.setattr(fresh_evaluate, "evaluate_real", forbidden)
    edit(dataset, PARTIAL_BASELINE_FILE, lambda d: d.__setitem__(field, {}))
    with pytest.raises(ValueError, match="Preserved partial baseline changed"):
        evaluate_fresh(dataset)


def test_missing_partial_baseline_is_not_recreated(dataset, tmp_path):
    path = dataset / PARTIAL_BASELINE_FILE
    path.unlink()
    assert main(["--corpus", str(dataset), "--output", str(tmp_path / "result.json")]) == 2
    assert not path.exists()


def test_argument_filter_source_hash_is_required(dataset):
    edit(
        dataset,
        BASELINE_FILE,
        lambda d: d["analyzer_sha256"].pop("src/codeimpact/call_arguments.py"),
    )
    with pytest.raises(ValueError, match="source inventory"):
        evaluate_fresh(dataset)
