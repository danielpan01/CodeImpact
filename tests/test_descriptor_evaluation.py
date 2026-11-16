"""Check the descriptor result against its frozen predecessor and evidence."""

import json
import shutil
from pathlib import Path

import pytest

from codeimpact import fresh_evaluate, holdout_evaluate
from codeimpact.analyzer import analyze
from codeimpact.descriptor_binding import DescriptorFallback
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest
from codeimpact.real_evaluate import canonical_hash

ROOT = Path(__file__).parents[1]
REMOVED = "tests/test_cachedmethod.py::UnboundMethodTest.test_class_call_without_instance"


def test_descriptor_exclusion_preserves_complete_retained_evidence(monkeypatch):
    dataset = ROOT / "corpus/real-v2"
    case = json.loads((dataset / "cases/cachetools_descriptor.json").read_text())
    receipt = json.loads((dataset / "baselines/lfu-callback-v1.json").read_text())
    request = AnalysisRequest.model_validate(case["request"])
    observed = analyze(request)
    validate_report(request, observed)
    monkeypatch.setattr(DescriptorFallback, "allows", lambda *_: True)
    predecessor = analyze(request)
    validate_report(request, predecessor)
    stable = predecessor.model_dump(mode="json")
    stable["stats"].pop("elapsed_ms")
    assert (
        canonical_hash(stable) == receipt["measurement"]["analysis_sha256"]["cachetools_descriptor"]
    )
    assert observed.recommendations == [
        r for r in predecessor.recommendations if r.symbol != REMOVED
    ]
    assert observed.impacted == [sid for sid in predecessor.impacted if sid != REMOVED]
    assert len(observed.recommendations) == 35
    assert len(case["unclassified"]) == 8
    assert len(case["unclassified"].keys() & {r.symbol for r in observed.recommendations}) == 5
    for field in ("nodes", "edges", "changed", "removed", "changes", "source_files", "warnings"):
        assert getattr(observed, field) == getattr(predecessor, field)


@pytest.mark.parametrize(
    ("dataset", "module", "evaluate"),
    [
        ("real-v2", fresh_evaluate, fresh_evaluate.evaluate_fresh),
        ("real-v3", holdout_evaluate, holdout_evaluate.evaluate_holdout),
    ],
)
def test_prior_lfu_baseline_is_checked_before_analysis(
    tmp_path, monkeypatch, dataset, module, evaluate
):
    directory = tmp_path / dataset
    shutil.copytree(ROOT / "corpus" / dataset, directory)
    with (directory / "baselines/lfu-callback-v1.json").open("ab") as stream:
        stream.write(b"\n")
    monkeypatch.setattr(module, "evaluate_real", lambda *_a, **_k: pytest.fail("ran analysis"))
    with pytest.raises(ValueError, match="Preserved LFU baseline changed"):
        evaluate(directory)
