"""Fresh v3 receipts, discovery boundaries and safe offline replay."""

import hashlib
import importlib
import json
import shutil
from pathlib import Path

import pytest

from codeimpact import holdout_evaluate as holdout
from codeimpact.corpus import CorpusCase, load_corpus
from codeimpact.evaluate import evaluate
from codeimpact.fresh_evaluate import CURRENT_SOURCES, MAPPING_SOURCES, evaluate_fresh, measurement
from codeimpact.models import Snapshot
from codeimpact.real_evaluate import evaluate_real, label_hash

ROOT = Path(__file__).parents[1]
DATA = ROOT / "corpus/real-v3"


@pytest.fixture
def dataset(tmp_path):
    target = tmp_path / "holdout"
    shutil.copytree(DATA, target)
    return target


def edit(directory, path, mutate):
    target = directory / path
    data = json.loads(target.read_text())
    mutate(data)
    target.write_text(json.dumps(data))


def script(monkeypatch, name):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module(name)


def test_source_discovery_audit_does_not_execute_or_collect():
    audit = holdout.discovery_audit(
        Snapshot(
            files={
                "test_regular.py": "raise RuntimeError('never run')\ndef test_direct(): pass\n"
                "if True:\n    def test_conditional(): pass\n"
                "class Group:\n    async def test_method(self): pass\n",
                "test.py": "def test_other(): pass\n",
                "broken_test.py": "def broken(:",
            }
        )
    )
    assert audit["discovered_ids"] == [
        "test.py::test_other",
        "test_regular.py::Group.test_method",
        "test_regular.py::test_direct",
    ]
    assert audit["outside_discovery"] == {
        "test_regular.py::test_conditional": "compound_statement",
    }
    assert audit["test_shaped_definition_count"] == 4
    assert audit["unparseable_files"] == ["broken_test.py"]


def test_reference_freeze_and_source_review_pack(monkeypatch):
    frozen = holdout.validate_frozen(DATA)
    assert frozen.reference_commit == holdout.REFERENCE
    assert set(frozen.analyzer_sha256) == MAPPING_SOURCES
    assert len(frozen.files_sha256) == 31
    pack = (DATA / "REVIEW.md").read_text()
    assert pack.startswith(script(monkeypatch, "review_real").review_pack(DATA))
    assert pack.count("- [ ]") == 120  # 90 labels plus 30 explicitly outside discovery
    assert pack.count("Label status: **draft**") == 6
    assert "deferred by the owner" in (DATA / "README.md").read_text()


@pytest.mark.parametrize(
    "path",
    [
        "README.md",
        "PROTOCOL.md",
        "REVIEW.md",
        "discovery.json",
        "preservation.json",
        "licenses/ordered_set_pop-head.txt",
    ],
)
def test_input_bytes_cannot_change(dataset, path, monkeypatch):
    monkeypatch.setattr(holdout, "evaluate_real", lambda *_a, **_k: pytest.fail("ran analysis"))
    with (dataset / path).open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(ValueError, match="Frozen input changed"):
        holdout.evaluate_holdout(dataset)


def test_coordinated_label_and_provenance_change_rejected(dataset):
    path = "cases/iso8601_errors.json"
    edit(
        dataset,
        path,
        lambda data: data["expected_affected"].update(
            {
                "iso8601/test_iso8601.py::test_parse_valid_date": "Changed after measurement",
            }
        ),
    )
    new_hash = label_hash(CorpusCase.model_validate_json((dataset / path).read_text()))
    edit(
        dataset,
        "provenance/iso8601_errors.json",
        lambda data: data["label_review"].update(labels_sha256=new_hash),
    )
    with pytest.raises(ValueError, match="Frozen input changed"):
        holdout.validate_frozen(dataset)


@pytest.mark.parametrize(
    "path",
    [
        "../secret",
        "/secret",
        "licenses/../secret",
        "a//b",
        "a\\b",
        "a:b",
    ],
)
def test_unsafe_receipt_paths_are_rejected(tmp_path, path):
    with pytest.raises(ValueError, match="Unsafe receipt path"):
        holdout.safe_file(tmp_path, path)


@pytest.mark.parametrize(
    "path", ["licenses", "README.md", "first-run.json", "baselines", holdout.LABELS_FILE]
)
def test_symlink_files_and_parents_rejected(dataset, tmp_path, path):
    original = dataset / path
    outside = tmp_path / "outside"
    original.rename(outside)
    original.symlink_to(outside, target_is_directory=outside.is_dir())
    with pytest.raises(ValueError, match="[Ss]ymlink"):
        holdout.evaluate_holdout(dataset)


def test_frozen_inventory_rejects_extra_files(dataset):
    (dataset / "unreviewed.json").write_text("{}")
    with pytest.raises(ValueError, match="Unexpected dataset file"):
        holdout.validate_frozen(dataset)


def test_engine_change_rejected_before_analysis(dataset, tmp_path):
    project = tmp_path / "project"
    for relative in CURRENT_SOURCES:
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    with (project / "src/codeimpact/analyzer.py").open("ab") as stream:
        stream.write(b"\n# drift")
    with pytest.raises(ValueError, match="Engine changed"):
        holdout.validate_frozen(dataset, project)


def test_total_budget_rejects_input_before_analysis(monkeypatch):
    monkeypatch.setattr(holdout, "MAX_CORPUS_BYTES", 1)
    monkeypatch.setattr(holdout, "evaluate_real", lambda *_a, **_k: pytest.fail("ran analysis"))
    with pytest.raises(ValueError, match="total size limit"):
        holdout.evaluate_holdout(DATA)


def test_first_measurement_is_not_rewritten(dataset):
    edit(
        dataset,
        "first-run.json",
        lambda data: data["measurement"]["summary"].update(selected_count=0),
    )
    with pytest.raises(ValueError, match="First measurement changed"):
        holdout.evaluate_holdout(dataset)


def test_missing_first_run_fails_without_creating_receipt(dataset, tmp_path):
    path = dataset / "first-run.json"
    path.unlink()
    assert holdout.main(["--corpus", str(dataset), "--output", str(tmp_path / "out.json")]) == 2
    assert not path.exists()


def test_no_upstream_import_network_or_subprocess_and_versioned_measurement(monkeypatch):
    import builtins
    import socket
    import subprocess

    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        assert name.split(".")[0] not in {"iso8601", "inflection", "ordered_set"}
        return original(name, *args, **kwargs)

    def forbidden(*args, **kwargs):
        pytest.fail("offline evaluation attempted network or subprocess")

    monkeypatch.setattr(builtins, "__import__", guarded)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    # The old frozen case lacks labels for the newly supported inventory. Refuse
    # an unversioned evaluation rather than silently dropping those definitions.
    with pytest.raises(ValueError, match="Every head test needs an explicit label"):
        evaluate_real(DATA)
    receipt = json.loads((DATA / "first-run.json").read_text())
    report = holdout.evaluate_holdout(DATA)
    assert report == holdout.evaluate_holdout(DATA)
    assert report["holdout_evaluation_schema_version"] == "11.0"
    assert not report["first_measurement_matches"]
    assert report["current_measurement_matches"]
    assert report["original_summary"] == receipt["measurement"]["summary"]
    assert report["original_summary"]["test_count"] == 90
    assert report["original_summary"]["selected_count"] == 84
    for cid, digest in measurement(report)["analysis_sha256"].items():
        if cid not in {
            "ordered_set_pop",
            "inflection_rules",
            "iso8601_validator",
            "inflection_title",
        }:
            assert digest == receipt["measurement"]["analysis_sha256"][cid]
    assert report["evaluation"]["regressions"] == []
    assert len(report["initial_regressions"]) == 3
    assert report["summary"]["test_count"] == 120
    assert report["summary"]["selected_count"] == 44
    assert report["summary"]["label_status_counts"] == {"draft": 6}
    assert report["summary"]["metrics"]["counts"] == {
        "tp": 42,
        "fp": 2,
        "fn": 0,
        "tn": 64,
        "unclassified_recommendations": 0,
    }
    missing = next(case for case in report["cases"] if case["id"] == "ordered_set_pop")
    assert missing["test_count"] == 30
    assert missing["selected_test_ids"] == ["test.py::test_pop"]
    assert missing["unclassified_test_count"] == 12
    assert missing["unclassified_recommendation_count"] == 0
    assert report["discovery"]["ordered_set_pop"]["outside_discovery"] == {}
    outside = report["original_discovery"]["ordered_set_pop"]["outside_discovery"]
    assert len(outside) == 30
    assert outside["test.py::test_pop"] == "unsupported_filename"


def test_bad_evidence_cannot_be_recorded_as_matching(monkeypatch):
    from codeimpact import evaluate as evaluator

    original = evaluator.analyze

    def corrupt(request, **kwargs):
        report = original(request, **kwargs)
        if report.recommendations:
            report.recommendations[0].evidence_edges[0] = "invalid-edge"
        return report

    monkeypatch.setattr(evaluator, "analyze", corrupt)
    with pytest.raises(ValueError, match="Invalid analyzer report"):
        holdout.evaluate_holdout(DATA)


def test_annotation_drift_fails_gate_without_relabeling(dataset, tmp_path):
    before = (dataset / "cases/inflection_title.json").read_bytes()
    edit(
        dataset,
        holdout.BASELINE_FILE,
        lambda data: data["annotations"]["inflection_title"]["known_discrepancies"][
            "false_positives"
        ].update(
            {
                "test_inflection.py::test_uncountable_word_is_not_greedy": "Stale discrepancy",
            }
        ),
    )
    assert holdout.main(["--corpus", str(dataset), "--output", str(tmp_path / "out.json")]) == 1
    assert (dataset / "cases/inflection_title.json").read_bytes() == before


def test_measurement_drift_fails_gate(monkeypatch):
    original = holdout.evaluate_real

    def changed(*args, **kwargs):
        report = original(*args, **kwargs)
        report["summary"]["selected_count"] -= 1
        return report

    monkeypatch.setattr(holdout, "evaluate_real", changed)
    report = holdout.evaluate_holdout(DATA)
    assert not report["first_measurement_matches"]
    assert report["evaluation"]["regressions"] == [
        "v3: measurement differs from finite-string-guards-v1",
    ]


def test_old_corpus_and_unchanged_reports_preserve_versioned_v2_measurements():
    receipt = holdout.validate_preservation(DATA)
    reports = {
        "corpus-evaluation.json": evaluate(load_corpus(ROOT / "corpus/cases")).model_dump(
            mode="json"
        ),
        "real-evaluation.json": evaluate_real(ROOT / "corpus/real"),
    }
    for name, report in reports.items():
        raw = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
        assert hashlib.sha256(raw).hexdigest() == receipt.reports_sha256[name]
    mapping = json.loads((ROOT / "corpus/real-v2/baselines/mapping-fallback-v1.json").read_text())
    discovery = json.loads((ROOT / "corpus/real-v2/baselines/test-discovery-v1.json").read_text())
    assert mapping["measurement"] == discovery["measurement"]
    current = json.loads((ROOT / "corpus/real-v2/baselines/legacy-dispatch-v1.json").read_text())
    assert measurement(evaluate_fresh(ROOT / "corpus/real-v2")) == current["measurement"]
    assert receipt.reports_sha256["real-v2-evaluation.json"] == (
        "e4cd3fe60b1728dccfb5abc6326b998815f7f3d477314638a1fbcf520397b254"
    )


def test_pilot_preparation_only_exports_frozen_json(monkeypatch, tmp_path):
    from codeimpact import evaluate as evaluator

    monkeypatch.setattr(evaluator, "analyze", lambda *_a: pytest.fail("pilot ran analysis"))
    preparer = script(monkeypatch, "prepare_pilot")
    output = tmp_path / "pilot"
    preparer.prepare(DATA, output)
    assert {p.name for p in output.iterdir()} == {
        "inflection_title.json",
        "ordered_set_pop.json",
        "README.txt",
    }
    for case_id in preparer.CASES:
        assert (
            json.loads((output / f"{case_id}.json").read_text())
            == json.loads((DATA / f"cases/{case_id}.json").read_text())["request"]
        )
    assert "deferred" in (output / "README.txt").read_text()
    with pytest.raises(ValueError, match="already exists"):
        preparer.prepare(DATA, output)
    with pytest.raises(ValueError, match="outside the corpus"):
        preparer.prepare(DATA, DATA / "pilot")


def test_pilot_failure_does_not_write_partial_output(monkeypatch, dataset, tmp_path):
    (dataset / "README.md").write_text("corrupted")
    output = tmp_path / "pilot"
    with pytest.raises(ValueError, match="Frozen input changed"):
        script(monkeypatch, "prepare_pilot").prepare(dataset, output)
    assert not output.exists()


@pytest.mark.parametrize("name", ["LICENSE", "LICENSE.txt", "LICENSE.rst", "MIT-LICENSE"])
def test_capture_accepts_one_explicit_ordinary_license(monkeypatch, name):
    from codeimpact.github import Tree, TreeEntry

    entry = TreeEntry(path=name, mode="100644", type="blob", sha="0" * 40, size=10)
    tree = Tree(sha="1" * 40, truncated=False, tree=[entry])
    assert script(monkeypatch, "capture_real").select_license(tree) == entry


@pytest.mark.parametrize(
    "entries",
    [
        [],
        [("nested/LICENSE", "100644", "blob")],
        [("LICENSE", "100644", "blob"), ("MIT-LICENSE", "100644", "blob")],
        [("MIT-LICENSE", "120000", "blob")],
        [("LICENSE", "040000", "tree")],
    ],
)
def test_capture_rejects_ambiguous_or_nonregular_licenses(monkeypatch, entries):
    from codeimpact.github import Tree, TreeEntry

    tree = Tree(
        sha="1" * 40,
        truncated=False,
        tree=[TreeEntry(path=p, mode=m, type=t, sha="0" * 40) for p, m, t in entries],
    )
    with pytest.raises(ValueError, match="license|License"):
        script(monkeypatch, "capture_real").select_license(tree)


def test_ci_has_four_offline_gates():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    for command in ("evaluate", "evaluate-real", "evaluate-real-v2", "evaluate-real-v3"):
        assert f"run: make {command}\n" in workflow
    assert "capture_real.py" not in workflow
