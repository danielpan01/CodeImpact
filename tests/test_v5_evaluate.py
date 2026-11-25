import importlib
import json
import shutil
import socket
from pathlib import Path

import pytest

from codeimpact import v5_evaluate
from codeimpact.v4_evaluate import stable_bytes

CASE = "cached_property_coroutine_metadata"


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    return shutil.copytree(v5_evaluate.DIRECTORY, tmp_path / "v5")


def test_v5_replays_with_network_disabled(monkeypatch):
    def deny_network(*args, **kwargs):
        pytest.fail("Offline replay attempted to connect")

    monkeypatch.setattr(socket.socket, "connect", deny_network)
    report = v5_evaluate.evaluate_v5(v5_evaluate.DIRECTORY)
    assert report["evaluation"]["regressions"] == []
    assert report["summary"]["test_count"] == 239
    assert report["summary"]["selected_count"] == 102
    assert report["independent_review"] == "skipped"


def test_v5_rejects_frozen_source_tampering(dataset):
    path = dataset / "cases" / f"{CASE}.json"
    case = json.loads(path.read_bytes())
    case["request"]["head"]["files"]["cached_property.py"] += "\n# tampering"
    path.write_bytes(stable_bytes(case))

    with pytest.raises(ValueError, match="V5 frozen input changed"):
        v5_evaluate.evaluate_v5(dataset)


def test_v5_rejects_missing_snapshot_even_when_file_hash_is_refreshed(dataset):
    name = f"cases/{CASE}.json"
    path = dataset / name
    case = json.loads(path.read_bytes())
    del case["request"]["head"]["files"]["setup.py"]
    path.write_bytes(stable_bytes(case))
    freeze_path = dataset / v5_evaluate.FREEZE
    freeze = json.loads(freeze_path.read_bytes())
    freeze["files_sha256"][name] = v5_evaluate.file_hash(path)
    freeze_path.write_bytes(stable_bytes(freeze))

    v5_evaluate.validate_frozen(dataset)
    with pytest.raises(ValueError, match="complete|source inventory|snapshot"):
        v5_evaluate.collect(dataset)


def test_v5_rejects_invalid_evidence_before_comparing_baseline(monkeypatch):
    evaluator = importlib.import_module("codeimpact.evaluate")
    analyze = evaluator.analyze

    def invalid_analysis(*args, **kwargs):
        report = analyze(*args, **kwargs)
        recommendation = next(rec for rec in report.recommendations if rec.evidence_edges)
        recommendation.evidence_edges[0] = "unknown-edge"
        return report

    monkeypatch.setattr(evaluator, "analyze", invalid_analysis)
    with pytest.raises(ValueError, match="missing typed edge"):
        v5_evaluate.evaluate_v5(v5_evaluate.DIRECTORY)


def test_v5_detects_changed_recommendations_without_baseline_update(monkeypatch):
    evaluator = importlib.import_module("codeimpact.evaluate")
    analyze = evaluator.analyze

    def dropped_recommendation(*args, **kwargs):
        report = analyze(*args, **kwargs)
        report.recommendations.pop()
        return report

    monkeypatch.setattr(evaluator, "analyze", dropped_recommendation)
    report = v5_evaluate.evaluate_v5(v5_evaluate.DIRECTORY)

    assert report["evaluation"]["regressions"] == [
        "V5 report differs from the frozen first measurement",
        "V5 discrepancies differ from the recorded baseline",
    ]
