"""Verify v6 freeze, provenance, label and report integrity offline."""

import copy
import json
from pathlib import Path
from shutil import copytree

import pytest

from codeimpact import v6_evaluate as v6
from codeimpact.fresh_evaluate import file_hash

XML_CASE = "cases/xmltodict_doctype.json"


@pytest.fixture
def dataset(tmp_path):
    return copytree(v6.DIRECTORY, tmp_path / "real-v6")


@pytest.fixture(scope="module")
def report():
    return v6.collect(v6.DIRECTORY)


def load(path: Path):
    return json.loads(path.read_bytes())


def save(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def rehash_input(dataset: Path, name: str) -> None:
    manifest = load(dataset / v6.FREEZE)
    manifest["files_sha256"][name] = file_hash(dataset / name)
    save(dataset / v6.FREEZE, manifest)


def test_v6_replays_frozen_measurement(report, monkeypatch):
    monkeypatch.setattr(v6, "collect", lambda _: copy.deepcopy(report))
    replay = v6.evaluate_v6(v6.DIRECTORY)
    assert not replay["evaluation"]["regressions"]
    assert replay["independent_review"] == "pending"
    assert replay["summary"]["test_count"] == 399
    assert replay["summary"]["outside_discovery_count"] == 0
    assert len(replay["repositories"]) == 3
    assert replay["first_regressions"]


def test_v6_declines_an_unexpected_dataset_file(dataset):
    (dataset / "unreviewed.json").write_text("{}\n")
    with pytest.raises(ValueError, match="Unexpected or missing v6 files"):
        v6.validate_frozen(dataset)


def test_v6_freeze_detects_edited_snapshot(dataset):
    path = dataset / XML_CASE
    item = load(path)
    item["request"]["head"]["files"]["xmltodict.py"] += "\n"
    save(path, item)
    with pytest.raises(ValueError, match="V6 frozen input changed"):
        v6.validate_frozen(dataset)


def test_v6_provenance_detects_an_incomplete_snapshot(dataset):
    path = dataset / XML_CASE
    item = load(path)
    del item["request"]["head"]["files"]["xmltodict.py"]
    save(path, item)
    with pytest.raises(ValueError, match="complete supported Python tree"):
        v6.collect(dataset)


@pytest.mark.parametrize("mutation", ["missing", "overlapping"])
def test_v6_refuses_incomplete_or_overlapping_labels(dataset, mutation):
    path = dataset / XML_CASE
    item = load(path)
    sid = next(iter(item["expected_affected"]))
    if mutation == "missing":
        del item["expected_affected"][sid]
    else:
        item["expected_unaffected"][sid] = "Overlapping draft label"
    save(path, item)
    with pytest.raises(ValueError, match="Every head test needs|labels must be disjoint"):
        v6.collect(dataset)


def test_v6_engine_digest_is_verified(dataset):
    path = dataset / "analyzer.json"
    reference = load(path)
    reference["sources_sha256"]["src/codeimpact/analyzer.py"] = "0" * 64
    save(path, reference)
    rehash_input(dataset, "analyzer.json")
    with pytest.raises(ValueError, match="V6 reference source changed"):
        v6.validate_frozen(dataset)


def test_v6_exclusion_ledger_must_match_selection(dataset):
    path = dataset / "candidates.json"
    receipt = load(path)
    receipt["repositories"][0]["commits"][0]["reason"] = "Changed exclusion"
    save(path, receipt)
    rehash_input(dataset, "candidates.json")
    with pytest.raises(ValueError, match="V6 candidate decisions differ"):
        v6.validate_frozen(dataset)


def test_v6_first_run_receipt_is_pinned(dataset):
    path = dataset / v6.FIRST
    receipt = load(path)
    receipt["initial_regressions"] = []
    save(path, receipt)
    with pytest.raises(ValueError, match="V6 first run changed"):
        v6.evaluate_v6(dataset)


def test_v6_gate_detects_evidence_drift(report, monkeypatch):
    changed = copy.deepcopy(report)
    item = changed["evaluation"]["cases"][0]["analysis"]
    recommendation = next(row for row in item["recommendations"] if row["evidence_edges"])
    edge = next(edge for edge in item["edges"] if edge["id"] == recommendation["evidence_edges"][0])
    entry = (edge["before"] + edge["after"])[0]
    entry["text"] += " Changed evidence"
    monkeypatch.setattr(v6, "collect", lambda _: changed)
    replay = v6.evaluate_v6(v6.DIRECTORY)
    assert replay["evaluation"]["regressions"] == [
        "V6 report differs from the frozen first measurement"
    ]


def test_v6_gate_detects_changed_discrepancies(dataset, report, monkeypatch):
    path = dataset / v6.BASELINE
    baseline = load(path)
    baseline["expected"]["xmltodict_doctype"]["false_positives"].pop()
    save(path, baseline)
    monkeypatch.setattr(v6, "collect", lambda _: copy.deepcopy(report))
    replay = v6.evaluate_v6(dataset)
    assert replay["evaluation"]["regressions"] == [
        "V6 discrepancies differ from the recorded baseline"
    ]
