"""Historical replay and evidence checks for the literal table refinement."""

import json
import shutil
from pathlib import Path

import pytest

from codeimpact import fresh_evaluate, holdout_evaluate
from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest
from codeimpact.module_data import ModuleDataFallback
from codeimpact.real_evaluate import canonical_hash

ROOT = Path(__file__).parents[1]


def test_both_module_contributions_and_affected_paths_match_history(monkeypatch):
    dataset = ROOT / "corpus/real-v3"
    case = json.loads((dataset / "cases/inflection_rules.json").read_text())
    old = json.loads((dataset / "baselines/legacy-dispatch-v1.json").read_text())["measurement"]
    new = json.loads((dataset / "baselines/literal-tables-v1.json").read_text())["measurement"]
    request = AnalysisRequest.model_validate(case["request"])
    current = analyze(request)
    validate_report(request, current)
    monkeypatch.setattr(ModuleDataFallback, "allows", lambda *_: True)
    predecessor = analyze(request)
    validate_report(request, predecessor)
    stable = predecessor.model_dump(mode="json")
    stable["stats"].pop("elapsed_ms")
    assert canonical_hash(stable) == old["analysis_sha256"]["inflection_rules"]
    removed = set(old["classifications"]["inflection_rules"]["false_positives"]) - set(
        new["classifications"]["inflection_rules"]["false_positives"]
    )
    assert len(removed) == 14
    assert "test_inflection.py::test_camelize" in removed
    old_recommendations = {r.symbol: r for r in predecessor.recommendations}
    new_recommendations = {r.symbol: r for r in current.recommendations}
    assert old_recommendations.keys() - new_recommendations.keys() == removed
    assert not new_recommendations.keys() - old_recommendations.keys()
    replaced_paths = {
        "test_inflection.py::test_pluralize_empty_string": "pluralize",
        "test_inflection.py::test_pluralize_plurals": "pluralize",
        "test_inflection.py::test_tableize": "tableize",
        "test_inflection.py::test_uncountability": "pluralize",
    }
    for sid, item in new_recommendations.items():
        previous = old_recommendations[sid]
        assert item.reason == previous.reason == "Conservative module/import dependency"
        assert item.path_revision == previous.path_revision == "both"
        if sid in replaced_paths:
            assert previous.evidence_path == [sid, "test_inflection.py::<module>"]
            assert previous.score == 50 and previous.distance == 1
            assert item.evidence_path == [
                sid,
                f"inflection.py::{replaced_paths[sid]}",
                "inflection.py::<module>",
            ]
            assert item.score == 40 and item.distance == 2
        else:
            assert item == previous
    assert current.impacted == [sid for sid in predecessor.impacted if sid not in removed]
    assert len(current.recommendations) == 8
    assert len(case["expected_affected"]) == 6
    assert case["expected_affected"].keys() <= {r.symbol for r in current.recommendations}
    for field in ("nodes", "edges", "changed", "changes", "removed", "source_files", "warnings"):
        assert getattr(current, field) == getattr(predecessor, field)


@pytest.mark.parametrize(
    ("dataset", "module", "evaluate"),
    [
        ("real-v2", fresh_evaluate, fresh_evaluate.evaluate_fresh),
        ("real-v3", holdout_evaluate, holdout_evaluate.evaluate_holdout),
    ],
)
def test_legacy_receipt_is_checked_before_analysis(
    tmp_path, monkeypatch, dataset, module, evaluate
):
    directory = tmp_path / dataset
    shutil.copytree(ROOT / "corpus" / dataset, directory)
    with (directory / "baselines/legacy-dispatch-v1.json").open("ab") as stream:
        stream.write(b"\n")
    monkeypatch.setattr(module, "evaluate_real", lambda *_a, **_k: pytest.fail("ran analysis"))
    with pytest.raises(ValueError, match="Preserved legacy dispatch baseline changed"):
        evaluate(directory)
