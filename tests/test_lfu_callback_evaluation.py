"""Replay the preserved LFU result and compare every retained evidence field."""

import ast
import json
from pathlib import Path

import pytest

from codeimpact import holdout_evaluate as holdout
from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.mapping_protocols import MappingReferences
from codeimpact.models import AnalysisRequest
from codeimpact.real_evaluate import canonical_hash

ROOT = Path(__file__).parents[1]


def test_only_reviewed_lfu_callback_is_removed_and_retained_reports_are_identical(monkeypatch):
    case = json.loads((ROOT / "corpus/real-v2/cases/cachetools_lfu.json").read_text())
    request = AnalysisRequest.model_validate(case["request"])
    current = analyze(request)
    validate_report(request, current)

    def historical_nested_guard(_self, _sid, node):
        return not any(
            isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            for n in list(ast.walk(node))[1:]
        )

    monkeypatch.setattr(MappingReferences, "closed_callbacks", historical_nested_guard)
    previous = analyze(request)
    validate_report(request, previous)
    stable = previous.model_dump(mode="json")
    stable["stats"].pop("elapsed_ms")
    receipt = json.loads((ROOT / "corpus/real-v2/baselines/test-discovery-v1.json").read_text())
    assert canonical_hash(stable) == receipt["measurement"]["analysis_sha256"]["cachetools_lfu"]
    before = {r.symbol: r for r in previous.recommendations}
    after = {r.symbol: r for r in current.recommendations}
    assert before.keys() - after.keys() == {"tests/test_rr.py::RRCacheTest.test_rr_bad_choice"}
    assert not after.keys() - before.keys()
    assert len(after) == 138
    assert case["expected_affected"].keys() <= after.keys()
    assert case["unclassified"].keys() <= after.keys()
    assert len(case["expected_affected"]) == 6
    assert len(case["unclassified"]) == 8
    assert all(value == before[sid] for sid, value in after.items())
    assert current.nodes == previous.nodes
    assert current.edges == previous.edges
    assert current.changed == previous.changed
    assert current.removed == previous.removed
    assert current.source_files == previous.source_files
    assert current.warnings == previous.warnings


@pytest.mark.parametrize("dataset", ["real-v2", "real-v3"])
def test_discovery_receipt_link_is_immutable(dataset, tmp_path, monkeypatch):
    import shutil

    from codeimpact import fresh_evaluate as fresh

    target = tmp_path / dataset
    shutil.copytree(ROOT / "corpus" / dataset, target)
    with (target / "baselines/test-discovery-v1.json").open("ab") as stream:
        stream.write(b"\n")
    module = fresh if dataset == "real-v2" else holdout
    monkeypatch.setattr(module, "evaluate_real", lambda *_a, **_k: pytest.fail("ran analysis"))
    evaluator = fresh.evaluate_fresh if dataset == "real-v2" else holdout.evaluate_holdout
    with pytest.raises(ValueError, match="Preserved discovery baseline changed"):
        evaluator(target)
