"""New discovery receipts must extend, never relabel or replace, frozen evidence."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from codeimpact import holdout_evaluate as holdout
from codeimpact.analyzer import analyze
from codeimpact.corpus import CorpusCase
from codeimpact.discovery import LEGACY_POLICY, is_test_file
from codeimpact.fresh_evaluate import MAPPING_BASELINE_FILE, evaluate_fresh
from codeimpact.models import AnalysisRequest
from codeimpact.real_evaluate import evaluate_real

ROOT = Path(__file__).parents[1]
DATA = ROOT / "corpus/real-v3"


@pytest.fixture
def dataset(tmp_path):
    target = tmp_path / "v3"
    shutil.copytree(DATA, target)
    return target


def test_frozen_zero_label_case_requires_explicit_historical_policy():
    raw = (DATA / "cases/ordered_set_pop.json").read_text()
    with pytest.raises(ValueError, match="Every head test needs an explicit label"):
        CorpusCase.model_validate_json(raw)
    original = CorpusCase.model_validate_json(raw, context={"discovery_policy": LEGACY_POLICY})
    assert not original.expected_affected
    assert not original.expected_unaffected
    assert not original.unclassified
    with pytest.raises(ValueError, match="Unknown discovery policy"):
        CorpusCase.model_validate_json(raw, context={"discovery_policy": "unknown"})


@pytest.mark.parametrize("name", [holdout.LABELS_FILE, holdout.BASELINE_FILE])
def test_missing_new_receipt_is_never_created(dataset, name, tmp_path):
    path = dataset / name
    path.unlink()
    assert holdout.main(["--corpus", str(dataset), "--output", str(tmp_path / "out.json")]) == 2
    assert not path.exists()


@pytest.mark.parametrize("field", ["classification", "rationale", "line"])
def test_new_label_changes_fail_before_analysis(dataset, monkeypatch, field):
    path = dataset / holdout.LABELS_FILE
    data = json.loads(path.read_text())
    data["labels"]["test.py::test_pop"][field] = "unaffected" if field != "line" else 1
    path.write_text(json.dumps(data))
    monkeypatch.setattr(holdout, "evaluate_real", lambda *_a, **_k: pytest.fail("ran analysis"))
    with pytest.raises(ValueError, match="Discovery labels changed"):
        holdout.evaluate_holdout(dataset)


def test_extension_rejects_missing_definitions_and_wrong_source_ranges(dataset):
    path = dataset / holdout.LABELS_FILE
    original = json.loads(path.read_text())
    data = json.loads(path.read_text())
    data["labels"].pop("test.py::test_pop")
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Expanded label inventory"):
        holdout.label_extension(dataset, [])
    original["labels"]["test.py::test_pop"]["line"] = 1
    path.write_text(json.dumps(original))
    with pytest.raises(ValueError, match="Label source range mismatch"):
        holdout.label_extension(dataset, [])


def test_extensions_cannot_relabel_existing_tests(monkeypatch):
    from codeimpact import evaluate as evaluator

    monkeypatch.setattr(evaluator, "analyze", lambda *_a: pytest.fail("ran analysis"))
    with pytest.raises(ValueError, match="rewrites an original label"):
        evaluate_real(
            DATA,
            label_extensions={
                "inflection_rules": {
                    "expected_affected": {},
                    "unclassified": {},
                    "expected_unaffected": {
                        "test_inflection.py::test_pluralize_plural": "Relabeled"
                    },
                    "expected_unclassified_recommendations": [],
                }
            },
        )


def test_invalid_annotation_inventory_fails_before_extensions(monkeypatch):
    from codeimpact import evaluate as evaluator

    monkeypatch.setattr(evaluator, "analyze", lambda *_a: pytest.fail("ran analysis"))
    _, extension = holdout.label_extension(DATA, [])
    with pytest.raises(ValueError, match="Baseline case inventory"):
        evaluate_real(DATA, annotations={}, label_extensions=extension)


def test_preserved_mapping_baseline_cannot_be_rewritten(tmp_path, monkeypatch):
    from codeimpact import fresh_evaluate

    path = tmp_path / "v2"
    shutil.copytree(ROOT / "corpus/real-v2", path)
    with (path / MAPPING_BASELINE_FILE).open("ab") as stream:
        stream.write(b"\n")
    monkeypatch.setattr(
        fresh_evaluate, "evaluate_real", lambda *_a, **_k: pytest.fail("ran analysis")
    )
    with pytest.raises(ValueError, match="Preserved mapping baseline changed"):
        evaluate_fresh(path)


def test_original_baseline_and_frozen_engine_receipt_remain_enforced(dataset):
    with (dataset / "baseline.json").open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(ValueError, match="Historical first baseline changed"):
        holdout.validate_frozen(dataset)


def test_authored_zero_discovery_fixture_retains_both_exclusion_reasons():
    request = AnalysisRequest.model_validate_json(
        (ROOT / "tests/fixtures/unsupported-discovery.json").read_text()
    )
    audit = holdout.discovery_audit(request.head)
    assert audit["discovered_ids"] == []
    assert audit["outside_discovery"] == {
        "checks.py::test_total": "unsupported_filename",
        "test_conditional.py::test_conditional": "compound_statement",
    }
    report = analyze(request)
    assert not report.recommendations
    assert not any(node.kind == "test" for node in report.nodes)


def test_draft_receipt_remains_the_preanalysis_version():
    assert hashlib.sha256((DATA / holdout.LABELS_FILE).read_bytes()).hexdigest() == (
        "bb40f5912e4cc8e535c8aa908db2c44871a355336ca9f4457df862356653b879"
    )


def test_original_v3_first_report_is_reproducible_with_historical_filters(monkeypatch):
    from codeimpact import analyzer, corpus
    from codeimpact.additive_exports import AdditiveExports
    from codeimpact.module_data import ModuleDataFallback

    # A test-scoped historical replay, not a production mode or new baseline.
    # Restore the historical filename policy and disable the newer fallback filters.
    # The complete old report hash still has to match exactly.
    def historical_filename(path, **_kwargs):
        return is_test_file(path, policy=LEGACY_POLICY)

    monkeypatch.setattr(analyzer, "is_test_file", historical_filename)
    monkeypatch.setattr(corpus, "is_test_file", historical_filename)
    monkeypatch.setattr(ModuleDataFallback, "allows", lambda *_: True)
    monkeypatch.setattr(AdditiveExports, "allows", lambda *_: True)
    report = evaluate_real(DATA)
    raw = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    receipt = json.loads((DATA / "first-run.json").read_text())
    assert hashlib.sha256(raw).hexdigest() == receipt["first_report_sha256"]
    assert report["evaluation"]["regressions"] == receipt["initial_regressions"]
