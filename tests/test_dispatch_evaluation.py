"""Reproduce the prior Slugify analysis and compare every retained evidence field."""

import json
import shutil
from pathlib import Path

import pytest

from codeimpact import fresh_evaluate, holdout_evaluate
from codeimpact.analyzer import analyze
from codeimpact.dispatch_fallback import DispatchFallback
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest
from codeimpact.real_evaluate import canonical_hash

ROOT = Path(__file__).parents[1]


def test_legacy_exclusion_preserves_evidence_and_existing_outcomes(monkeypatch):
    dataset = ROOT / "corpus/real-v2"
    key = "slugify_boundary"
    case = json.loads((dataset / f"cases/{key}.json").read_text())
    old = json.loads((dataset / "baselines/descriptor-binding-v1.json").read_text())["measurement"]
    new = json.loads((dataset / "baselines/legacy-dispatch-v1.json").read_text())["measurement"]
    request = AnalysisRequest.model_validate(case["request"])
    observed = analyze(request)
    validate_report(request, observed)
    monkeypatch.setattr(DispatchFallback, "allows", lambda *_: True)
    predecessor = analyze(request)
    validate_report(request, predecessor)
    stable = predecessor.model_dump(mode="json")
    stable["stats"].pop("elapsed_ms")
    assert canonical_hash(stable) == old["analysis_sha256"][key]
    removed = set(old["classifications"][key]["false_positives"]) - set(
        new["classifications"][key]["false_positives"]
    )
    assert len(removed) == 66
    assert all(sid.startswith("tests/test_legacy.py::") for sid in removed)
    assert "tests/test_legacy.py::TestSlugify.test_accented_text" in removed
    assert observed.recommendations == [
        item for item in predecessor.recommendations if item.symbol not in removed
    ]
    selected = {item.symbol for item in observed.recommendations}
    assert case["expected_affected"].keys() <= selected
    assert not case["unclassified"].keys() & selected
    for field in ("nodes", "edges", "changed", "removed", "changes", "source_files", "warnings"):
        assert getattr(observed, field) == getattr(predecessor, field)
    assert observed.impacted == [sid for sid in predecessor.impacted if sid not in removed]


@pytest.mark.parametrize(
    ("dataset", "module", "evaluate"),
    [
        ("real-v2", fresh_evaluate, fresh_evaluate.evaluate_fresh),
        ("real-v3", holdout_evaluate, holdout_evaluate.evaluate_holdout),
    ],
)
def test_descriptor_receipt_is_checked_before_analysis(
    tmp_path, monkeypatch, dataset, module, evaluate
):
    directory = tmp_path / dataset
    shutil.copytree(ROOT / "corpus" / dataset, directory)
    with (directory / "baselines/descriptor-binding-v1.json").open("ab") as stream:
        stream.write(b"\n")
    monkeypatch.setattr(module, "evaluate_real", lambda *_a, **_k: pytest.fail("ran analysis"))
    with pytest.raises(ValueError, match="Preserved descriptor baseline changed"):
        evaluate(directory)
