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
    latest = json.loads((ROOT / "benchmarks/lfu-callback-v1-preservation.json").read_text())
    assert (
        hashlib.sha256(
            (ROOT / "benchmarks/test-discovery-v1-preservation.json").read_bytes()
        ).hexdigest()
        == latest["previous_receipt_sha256"]
    )
    assert set(latest["changed_historical_sources"]) == {
        "src/codeimpact/mapping_protocols.py",
        "src/codeimpact/fresh_evaluate.py",
        "src/codeimpact/holdout_evaluate.py",
    }
    assert set(latest["added_corpus_sha256"]) == {
        "corpus/real-v2/baselines/lfu-callback-v1.json",
        "corpus/real-v3/baselines/lfu-callback-v1.json",
    }
    assert set(latest["current_sources_sha256"]) == set(current["current_sources_sha256"])
    descriptor = json.loads(
        (ROOT / "benchmarks/descriptor-binding-v1-preservation.json").read_text()
    )
    assert (
        hashlib.sha256(
            (ROOT / "benchmarks/lfu-callback-v1-preservation.json").read_bytes()
        ).hexdigest()
        == descriptor["previous_receipt_sha256"]
    )
    changed = set(descriptor["changed_historical_sources"])
    assert changed == {
        "src/codeimpact/analyzer.py",
        "src/codeimpact/fresh_evaluate.py",
        "src/codeimpact/holdout_evaluate.py",
    }
    assert set(descriptor["added_corpus_sha256"]) == {
        "corpus/real-v2/baselines/descriptor-binding-v1.json",
        "corpus/real-v3/baselines/descriptor-binding-v1.json",
    }
    assert set(descriptor["current_sources_sha256"]) == set(latest["current_sources_sha256"]) | {
        "src/codeimpact/descriptor_binding.py"
    }
    dispatch = json.loads((ROOT / "benchmarks/legacy-dispatch-v1-preservation.json").read_text())
    assert (
        hashlib.sha256(
            (ROOT / "benchmarks/descriptor-binding-v1-preservation.json").read_bytes()
        ).hexdigest()
        == dispatch["previous_receipt_sha256"]
    )
    assert set(dispatch["changed_historical_sources"]) == changed
    assert set(dispatch["added_corpus_sha256"]) == {
        "corpus/real-v2/baselines/legacy-dispatch-v1.json",
        "corpus/real-v3/baselines/legacy-dispatch-v1.json",
    }
    assert set(dispatch["current_sources_sha256"]) == set(descriptor["current_sources_sha256"]) | {
        "src/codeimpact/dispatch_fallback.py"
    }
    tables = json.loads((ROOT / "benchmarks/literal-tables-v1-preservation.json").read_text())
    assert (
        hashlib.sha256(
            (ROOT / "benchmarks/legacy-dispatch-v1-preservation.json").read_bytes()
        ).hexdigest()
        == tables["previous_receipt_sha256"]
    )
    assert set(tables["changed_historical_sources"]) == changed
    assert set(tables["added_corpus_sha256"]) == {
        "corpus/real-v2/baselines/literal-tables-v1.json",
        "corpus/real-v3/baselines/literal-tables-v1.json",
    }
    assert set(tables["current_sources_sha256"]) == set(dispatch["current_sources_sha256"]) | {
        "src/codeimpact/module_data.py"
    }
    corpus = {p.relative_to(ROOT).as_posix() for p in (ROOT / "corpus").rglob("*") if p.is_file()}
    historical = {p for p in receipt["files_sha256"] if p.startswith("corpus/")}
    assert len(historical) == 106
    assert set(current["added_corpus_sha256"]) == {
        "corpus/real-v2/baselines/test-discovery-v1.json",
        "corpus/real-v3/baselines/test-discovery-v1.json",
        "corpus/real-v3/baselines/test-discovery-v1-labels.json",
    }
    exports = json.loads((ROOT / "benchmarks/additive-exports-v1-preservation.json").read_text())
    assert (
        hashlib.sha256(
            (ROOT / "benchmarks/literal-tables-v1-preservation.json").read_bytes()
        ).hexdigest()
        == exports["previous_receipt_sha256"]
    )
    assert set(exports["changed_historical_sources"]) == changed
    assert set(exports["added_corpus_sha256"]) == {
        "corpus/real-v2/baselines/additive-exports-v1.json",
        "corpus/real-v3/baselines/additive-exports-v1.json",
    }
    assert set(exports["current_sources_sha256"]) == set(tables["current_sources_sha256"]) | {
        "src/codeimpact/additive_exports.py"
    }
    params = json.loads((ROOT / "benchmarks/parameter-tables-v1-preservation.json").read_text())
    assert (
        hashlib.sha256(
            (ROOT / "benchmarks/additive-exports-v1-preservation.json").read_bytes()
        ).hexdigest()
        == params["previous_receipt_sha256"]
    )
    assert set(params["changed_historical_sources"]) == {
        "src/codeimpact/module_data.py",
        "src/codeimpact/fresh_evaluate.py",
        "src/codeimpact/holdout_evaluate.py",
    }
    assert set(params["added_corpus_sha256"]) == {
        "corpus/real-v2/baselines/parameter-tables-v1.json",
        "corpus/real-v3/baselines/parameter-tables-v1.json",
    }
    assert set(params["current_sources_sha256"]) == set(exports["current_sources_sha256"])
    v4 = json.loads((ROOT / "benchmarks/fresh-v4-preservation.json").read_text())
    assert (
        hashlib.sha256(
            (ROOT / "benchmarks/parameter-tables-v1-preservation.json").read_bytes()
        ).hexdigest()
        == v4["previous_receipt_sha256"]
    )
    assert set(v4["changed_historical_sources"]) == {
        "src/codeimpact/holdout_evaluate.py",
        "src/codeimpact/real_evaluate.py",
    }
    assert all(path.startswith("corpus/real-v4/") for path in v4["added_corpus_sha256"])
    assert set(v4["current_sources_sha256"]) == set(params["current_sources_sha256"]) | {
        "src/codeimpact/v4_evaluate.py"
    }
    unittest = json.loads((ROOT / "benchmarks/unittest-discovery-v1-preservation.json").read_text())
    assert (
        hashlib.sha256((ROOT / "benchmarks/fresh-v4-preservation.json").read_bytes()).hexdigest()
        == unittest["previous_receipt_sha256"]
    )
    assert set(unittest["changed_historical_sources"]) == {
        "src/codeimpact/analyzer.py",
        "src/codeimpact/corpus.py",
        "src/codeimpact/discovery.py",
        "src/codeimpact/evaluate.py",
        "src/codeimpact/fresh_evaluate.py",
        "src/codeimpact/holdout_evaluate.py",
        "src/codeimpact/real_evaluate.py",
        "src/codeimpact/v4_evaluate.py",
    }
    assert set(unittest["added_corpus_sha256"]) == {
        f"corpus/real-v4-successors/unittest-discovery-v1/{file}"
        for file in ("baseline.json", "labels.json")
    }
    assert set(unittest["current_sources_sha256"]) == set(v4["current_sources_sha256"]) | {
        "src/codeimpact/unittest_evaluate.py"
    }
    variadic = json.loads((ROOT / "benchmarks/variadic-dispatch-v1-preservation.json").read_text())
    assert (
        hashlib.sha256(
            (ROOT / "benchmarks/unittest-discovery-v1-preservation.json").read_bytes()
        ).hexdigest()
        == variadic["previous_receipt_sha256"]
    )
    assert set(variadic["changed_historical_sources"]) == {
        f"src/codeimpact/{name}.py"
        for name in (
            "analyzer",
            "evaluate",
            "fresh_evaluate",
            "holdout_evaluate",
            "real_evaluate",
            "unittest_evaluate",
            "v4_evaluate",
        )
    }
    assert set(variadic["added_corpus_sha256"]) == {
        "corpus/real-v4-successors/variadic-dispatch-v1/baseline.json",
    }
    assert set(variadic["current_sources_sha256"]) == set(unittest["current_sources_sha256"]) | {
        "src/codeimpact/variadic_fallback.py",
        "src/codeimpact/variadic_evaluate.py",
    }
    rows = json.loads((ROOT / "benchmarks/parameter-rows-v1-preservation.json").read_text())
    assert (
        hashlib.sha256(
            (ROOT / "benchmarks/variadic-dispatch-v1-preservation.json").read_bytes()
        ).hexdigest()
        == rows["previous_receipt_sha256"]
    )
    assert set(rows["changed_historical_sources"]) == {
        f"src/codeimpact/{name}.py"
        for name in (
            "analyzer",
            "evaluate",
            "fresh_evaluate",
            "holdout_evaluate",
            "real_evaluate",
            "unittest_evaluate",
            "v4_evaluate",
            "variadic_evaluate",
        )
    }
    assert set(rows["added_corpus_sha256"]) == {
        "corpus/real-v4-successors/parameter-rows-v1/baseline.json",
    }
    assert set(rows["current_sources_sha256"]) == set(variadic["current_sources_sha256"]) | {
        "src/codeimpact/parameter_rows.py",
        "src/codeimpact/parameter_rows_evaluate.py",
    }
    reexports = json.loads(
        (ROOT / "benchmarks/explicit-reexports-v1-preservation.json").read_text()
    )
    assert (
        hashlib.sha256(
            (ROOT / "benchmarks/parameter-rows-v1-preservation.json").read_bytes()
        ).hexdigest()
        == reexports["previous_receipt_sha256"]
    )
    assert set(reexports["changed_historical_sources"]) == {
        f"src/codeimpact/{name}.py"
        for name in (
            "analyzer",
            "evaluate",
            "fresh_evaluate",
            "holdout_evaluate",
            "parameter_rows_evaluate",
            "real_evaluate",
            "unittest_evaluate",
            "v4_evaluate",
        )
    }
    assert set(reexports["added_corpus_sha256"]) == {
        "corpus/real-v4-successors/explicit-reexports-v1/baseline.json",
    }
    assert set(reexports["current_sources_sha256"]) == set(rows["current_sources_sha256"]) | {
        "src/codeimpact/explicit_reexports.py",
        "src/codeimpact/explicit_reexports_evaluate.py",
    }
    extensions = (
        current,
        latest,
        descriptor,
        dispatch,
        tables,
        exports,
        params,
        v4,
        unittest,
        variadic,
        rows,
        reexports,
    )
    assert corpus == historical.union(*(r["added_corpus_sha256"] for r in extensions))
    assert CURRENT_SOURCES <= params["current_sources_sha256"].keys()
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
    source_inventories = [
        receipt["files_sha256"],
        *(r["current_sources_sha256"] for r in extensions),
    ]
    for i, hashes in enumerate(source_inventories):
        superseded = {p for r in extensions[i:] for p in r["changed_historical_sources"]}
        for path, expected in hashes.items():
            if path not in superseded:
                assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
    for receipt in extensions:
        for path, expected in receipt["added_corpus_sha256"].items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
