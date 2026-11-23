"""Exact mixed-change measurement and predecessor receipt preservation."""

import json
import shutil
from pathlib import Path

import pytest

from codeimpact import fresh_evaluate, holdout_evaluate, module_data
from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest
from codeimpact.real_evaluate import canonical_hash

ROOT = Path(__file__).parents[1]
CASE = "inflection_title"
RETAINED = {
    "test_inflection.py::test_titleize",
    "test_inflection.py::test_uncountable_word_is_not_greedy",
}


def test_set_cleanup_successor_removes_only_the_conservative_titleize_sibling(monkeypatch):
    dataset = ROOT / "corpus/real-v3"
    successor = json.loads((dataset / "baselines/set-cleanup-v1.json").read_text())
    previous = json.loads((dataset / "baselines/parameter-tables-v1.json").read_text())
    monkeypatch.setattr(module_data.Query, "empty_string_return", lambda *_: False)
    monkeypatch.setattr(module_data.Query, "finite_string_test", lambda *_: False)
    _, extensions = holdout_evaluate.label_extension(
        dataset, successor["expected_unclassified_recommendations"]
    )
    current = holdout_evaluate.evaluate_real(
        dataset, annotations=successor["annotations"], label_extensions=extensions
    )
    hashes = fresh_evaluate.measurement(current)["analysis_sha256"]
    assert fresh_evaluate.measurement(current) == successor["measurement"]
    assert {
        cid for cid in hashes if hashes[cid] != previous["measurement"]["analysis_sha256"][cid]
    } == {CASE}

    request = AnalysisRequest.model_validate(
        json.loads((dataset / f"cases/{CASE}.json").read_text())["request"]
    )
    after = analyze(request)
    validate_report(request, after)
    monkeypatch.setattr(module_data.Query, "restored_set_test", lambda *_: False)
    before = analyze(request)
    validate_report(request, before)
    assert (
        canonical_hash(before.model_dump(mode="json", exclude={"stats": {"elapsed_ms"}}))
        == (previous["measurement"]["analysis_sha256"][CASE])
    )
    assert after.recommendations == before.recommendations[:1]
    assert after.recommendations[0].evidence_path == [
        "test_inflection.py::test_titleize",
        "inflection.py::titleize",
    ]
    removed = "test_inflection.py::test_uncountable_word_is_not_greedy"
    assert before.recommendations[1].symbol == removed
    assert after.impacted == [sid for sid in before.impacted if sid != removed]
    for field in ("nodes", "edges", "changed", "changes", "removed", "source_files", "warnings"):
        assert getattr(after, field) == getattr(before, field)


def test_titleize_retains_exact_evidence_for_both_remaining_tests(monkeypatch):
    dataset = ROOT / "corpus/real-v3"
    case = json.loads((dataset / f"cases/{CASE}.json").read_text())
    request = AnalysisRequest.model_validate(case["request"])
    previous = json.loads((dataset / "baselines/additive-exports-v1.json").read_text())
    current = json.loads((dataset / "baselines/parameter-tables-v1.json").read_text())
    hashes = previous["measurement"]["analysis_sha256"]
    successor = current["measurement"]["analysis_sha256"]
    assert {k for k, digest in successor.items() if digest != hashes[k]} == {CASE}
    monkeypatch.setattr(module_data.Query, "restored_set_test", lambda *_: False)
    after = analyze(request)
    validate_report(request, after)
    monkeypatch.setattr(module_data, "deferred_body_edit", lambda *_: None)
    before = analyze(request)
    validate_report(request, before)
    for report, expected in ((before, hashes), (after, successor)):
        stable = report.model_dump(mode="json")
        stable["stats"].pop("elapsed_ms")
        assert canonical_hash(stable) == expected[CASE]
    assert len(before.recommendations) == 22
    assert {r.symbol for r in after.recommendations} == RETAINED
    assert after.recommendations == [r for r in before.recommendations if r.symbol in RETAINED]
    assert after.recommendations[0].evidence_path == [
        "test_inflection.py::test_titleize",
        "inflection.py::titleize",
    ]
    assert after.recommendations[1].evidence_path[-1] == "test_inflection.py::<module>"
    removed = {r.symbol for r in before.recommendations} - RETAINED
    assert removed == set(case["expected_unaffected"]) - RETAINED
    assert after.impacted == [sid for sid in before.impacted if sid not in removed]
    for field in ("nodes", "edges", "changed", "changes", "removed", "source_files", "warnings"):
        assert getattr(after, field) == getattr(before, field)


@pytest.mark.parametrize(
    ("name", "module", "evaluate"),
    [
        ("real-v2", fresh_evaluate, fresh_evaluate.evaluate_fresh),
        ("real-v3", holdout_evaluate, holdout_evaluate.evaluate_holdout),
    ],
)
def test_additive_exports_receipt_is_verified_before_analysis(
    tmp_path, monkeypatch, name, module, evaluate
):
    directory = tmp_path / name
    shutil.copytree(ROOT / "corpus" / name, directory)
    with (directory / "baselines/additive-exports-v1.json").open("ab") as stream:
        stream.write(b"\n")
    monkeypatch.setattr(module, "evaluate_real", lambda *_a, **_k: pytest.fail("ran analysis"))
    with pytest.raises(ValueError, match="Preserved additive exports baseline changed"):
        evaluate(directory)


def test_parameter_tables_receipt_is_verified_before_analysis(tmp_path, monkeypatch):
    directory = tmp_path / "real-v3"
    shutil.copytree(ROOT / "corpus/real-v3", directory)
    with (directory / "baselines/parameter-tables-v1.json").open("ab") as stream:
        stream.write(b"\n")
    monkeypatch.setattr(
        holdout_evaluate, "evaluate_real", lambda *_a, **_k: pytest.fail("ran analysis")
    )
    with pytest.raises(ValueError, match="Preserved parameter tables baseline changed"):
        holdout_evaluate.evaluate_holdout(directory)
