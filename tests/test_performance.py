"""Benchmark definitions are data, metrics are explicit, and old inputs stay frozen."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest

from codeimpact.fresh_evaluate import CURRENT_SOURCES

ROOT = Path(__file__).parents[1]


def benchmark(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("benchmark")


def test_benchmark_uses_explicit_nearest_rank_and_valid_bounded_inputs(monkeypatch):
    script = benchmark(monkeypatch)
    assert script.summarize(list(range(1, 21))) == {"median": 10.5, "p95": 19, "min": 1, "max": 20}
    inputs = script.inputs()
    assert set(inputs) == {
        "demo",
        "cachetools_lfu",
        "inflection_title",
        "iso8601_errors",
        "chain_180",
        "wide_200",
    }
    assert "def f179(): return 2" in inputs["chain_180"].head.files["chain.py"]
    assert len(inputs["wide_200"].head.files["test_wide.py"].splitlines()) == 201
    for request in inputs.values():
        assert len(request.model_dump_json().encode()) < 6_000_000


def test_benchmark_cannot_write_into_historical_corpus(monkeypatch):
    with pytest.raises(SystemExit) as failure:
        benchmark(monkeypatch).main(["--output", str(ROOT / "corpus/measurement.json")])
    assert failure.value.code == 2
    assert not (ROOT / "corpus/measurement.json").exists()


def test_historical_corpus_engine_and_evaluators_remain_preserved():
    receipt = json.loads((ROOT / "benchmarks/preservation.json").read_text())
    current = json.loads((ROOT / "benchmarks/test-discovery-v1-preservation.json").read_text())
    assert (
        hashlib.sha256((ROOT / "benchmarks/preservation.json").read_bytes()).hexdigest()
        == (current["previous_receipt_sha256"])
    )
    corpus = {p.relative_to(ROOT).as_posix() for p in (ROOT / "corpus").rglob("*") if p.is_file()}
    historical = {p for p in receipt["files_sha256"] if p.startswith("corpus/")}
    assert len(historical) == 106
    assert set(current["added_corpus_sha256"]) == {
        "corpus/real-v2/baselines/test-discovery-v1.json",
        "corpus/real-v3/baselines/test-discovery-v1.json",
        "corpus/real-v3/baselines/test-discovery-v1-labels.json",
    }
    assert corpus == historical | current["added_corpus_sha256"].keys()
    assert CURRENT_SOURCES <= current["current_sources_sha256"].keys()
    assert set(current["current_sources_sha256"]) == {
        p for p in receipt["files_sha256"] if p.startswith("src/")
    } | {"src/codeimpact/discovery.py"}
    assert set(current["changed_historical_sources"]) == {
        "src/codeimpact/analyzer.py",
        "src/codeimpact/corpus.py",
        "src/codeimpact/fresh_evaluate.py",
        "src/codeimpact/holdout_evaluate.py",
        "src/codeimpact/real_evaluate.py",
    }
    for path, expected in receipt["files_sha256"].items():
        if path not in current["changed_historical_sources"]:
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
    for path, expected in (
        current["added_corpus_sha256"] | current["current_sources_sha256"]
    ).items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
