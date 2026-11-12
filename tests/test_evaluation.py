"""Metrics, drift checks and typed graph invariants have independent controls."""

import json
import subprocess
import sys

import pytest
from test_corpus import CASES, case_data

from codeimpact.analyzer import analyze
from codeimpact.corpus import CorpusCase, load_corpus
from codeimpact.evaluate import classify, evaluate, evaluate_case, validate_report


def test_metric_definitions_exclude_unclassified_recommendations():
    data = case_data()
    source = "\n".join(f"def test_{name}(): pass" for name in "abcde")
    data["request"] = {side: {"files": {"test_app.py": source}} for side in ("base", "head")}
    data["expected_affected"]["test_app.py::test_d"] = "Another affected test."
    data["expected_unaffected"]["test_app.py::test_e"] = "Another unaffected test."
    case = CorpusCase.model_validate(data)
    result = classify(case, {f"test_app.py::test_{name}" for name in "abc"})
    assert result.true_positives == ["test_app.py::test_a"]
    assert result.false_negatives == ["test_app.py::test_d"]
    assert result.false_positives == ["test_app.py::test_b"]
    assert result.true_negatives == ["test_app.py::test_e"]
    assert result.unclassified_recommendations == ["test_app.py::test_c"]
    assert result.metrics.precision.model_dump() == {"numerator": 1, "denominator": 2, "value": 0.5}
    assert result.metrics.recall.model_dump() == {"numerator": 1, "denominator": 2, "value": 0.5}


def test_zero_denominators_are_null_not_perfect_scores():
    data = case_data()
    data["expected_unaffected"].update(data["expected_affected"])
    data["expected_affected"] = {}
    result = classify(CorpusCase.model_validate(data), set())
    assert result.metrics.precision.value is None
    assert result.metrics.recall.value is None
    assert result.metrics.precision.denominator == result.metrics.recall.denominator == 0


@pytest.mark.parametrize("path", sorted(CASES.glob("*.json")), ids=lambda p: p.stem)
def test_every_case_matches_its_explicit_baseline_and_valid_graph(path):
    case = next(c for c in load_corpus(CASES) if c.id == path.stem)
    result = evaluate_case(case)
    assert result.regressions == [], f"{case.id}: {result.regressions}"


def test_case_order_input_order_and_repeated_evaluation_are_deterministic():
    cases = load_corpus(CASES)
    first = evaluate(cases)
    assert first.model_dump_json() == evaluate(list(reversed(cases))).model_dump_json()
    assert "elapsed_ms" not in first.model_dump_json()
    assert first.totals.counts.tp == sum(c.results.metrics.counts.tp for c in first.cases)
    assert first.totals.counts.fn == sum(c.results.metrics.counts.fn for c in first.cases)
    assert first.totals.counts.fp == sum(c.results.metrics.counts.fp for c in first.cases)
    assert first.totals.counts.tn == sum(c.results.metrics.counts.tn for c in first.cases)
    assert set(first.groups) == {"supported", "known_limitation"}
    reordered = []
    for case in cases:
        data = case.model_dump()
        for side in ("base", "head"):
            files = data["request"][side]["files"]
            data["request"][side]["files"] = dict(reversed(list(files.items())))
        reordered.append(CorpusCase.model_validate(data))
    assert json.dumps(first.model_dump(), sort_keys=True) == json.dumps(
        evaluate(reordered).model_dump(), sort_keys=True
    )


def test_known_discrepancy_changes_fail_including_improvements():
    case = next(c for c in load_corpus(CASES) if c.id == "pytest_fixtures")
    data = case.model_dump()
    data["known_discrepancies"]["false_negatives"] = {}
    result = evaluate_case(CorpusCase.model_validate(data))
    assert result.regressions
    # The comparison works both ways: claiming a known miss on a selected test fails too.
    # Reintroducing the former local-import miss must fail after its resolution fix.
    direct = next(c for c in load_corpus(CASES) if c.id == "local_import").model_dump()
    direct["category"] = "known_limitation"
    direct["limitations"] = ["Simulates a stale record after an analyzer improvement."]
    direct["known_discrepancies"]["false_negatives"] = direct["expected_affected"].copy()
    assert evaluate_case(CorpusCase.model_validate(direct)).regressions


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: setattr(r.recommendations[0], "evidence_path", ["missing"]),
        lambda r: setattr(r.recommendations[0], "evidence_edges", ["missing"]),
        lambda r: setattr(r.recommendations[0], "path_revision", "mixed"),
        lambda r: setattr(r.recommendations[0], "reason", "Conservative module/import dependency"),
        lambda r: setattr(r.recommendations[0], "distance", 99),
        lambda r: r.recommendations.append(r.recommendations[0]),
        lambda r: r.removed.append(r.recommendations[0].symbol),
        lambda r: r.edges[0].before.clear(),
        lambda r: setattr(r.edges[0], "revision", "after"),
        lambda r: setattr(r.edges[0], "target", "missing"),
        lambda r: r.edges.append(r.edges[0]),
        lambda r: setattr(r.edges[0].before[0].location, "line", 999),
        lambda r: setattr(r.edges[0].after[0], "text", "fabricated evidence"),
        lambda r: setattr(r.recommendations[0], "evidence_edges", [r.edges[0].id]),
        lambda r: r.recommendations[0].evidence_path.__setitem__(-1, "control.py::healthy"),
    ],
)
def test_malformed_evidence_cannot_pass_evaluation(mutation):
    case = next(c for c in load_corpus(CASES) if c.id == "direct_call")
    report = analyze(case.request)
    mutation(report)
    with pytest.raises(ValueError):
        validate_report(case.request, report)


def test_source_is_only_read_as_data(tmp_path):
    sentinel = tmp_path / "never-created"
    data = case_data()
    data["request"]["base"]["files"]["danger.py"] = (
        f"from pathlib import Path\nPath({str(sentinel)!r}).touch()\n"
    )
    data["request"]["head"]["files"]["danger.py"] = data["request"]["base"]["files"]["danger.py"]
    evaluate_case(CorpusCase.model_validate(data))
    assert not sentinel.exists()


def test_cli_text_json_determinism_and_invalid_input(tmp_path):
    output = tmp_path / "report.json"
    command = [
        sys.executable,
        "-m",
        "codeimpact.evaluate",
        "--corpus",
        str(CASES),
        "--output",
        str(output),
    ]
    first = subprocess.run(command, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr + first.stdout
    assert "Authored dependency-label agreement" in first.stdout
    assert "known_limitation" in first.stdout
    raw = output.read_bytes()
    report = json.loads(raw)
    assert report["schema_version"] == "1.0"
    assert report["analysis_schema_version"] == "2.0"
    assert report["regressions"] == []
    assert subprocess.run(command, capture_output=True).returncode == 0
    assert output.read_bytes() == raw
    bad = subprocess.run(command + ["--case", "does_not_exist"], capture_output=True, text=True)
    assert bad.returncode == 2 and "Unknown case" in bad.stderr


def test_cli_regression_exit_is_nonzero_and_still_writes_results(tmp_path):
    data = case_data()
    fixture = tmp_path / "cases"
    fixture.mkdir()
    (fixture / "example.json").write_text(json.dumps(data))
    output = tmp_path / "report.json"
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "codeimpact.evaluate",
            "--corpus",
            str(fixture),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert run.returncode == 1
    assert json.loads(output.read_text())["regressions"]


def test_cli_invalid_corpus_output_error_and_input_preservation(tmp_path):
    corpus = tmp_path / "cases"
    corpus.mkdir()
    case_file = corpus / "example.json"
    case_file.write_text("{invalid")
    command = [sys.executable, "-m", "codeimpact.evaluate", "--corpus", str(corpus)]
    output = tmp_path / "report.json"
    run = subprocess.run(command + ["--output", str(output)], capture_output=True, text=True)
    assert run.returncode == 2 and "Evaluation error" in run.stderr
    assert not output.exists()
    raw = json.dumps(case_data())
    case_file.write_text(raw)
    run = subprocess.run(command + ["--output", str(case_file)], capture_output=True, text=True)
    assert run.returncode == 2 and "outside the corpus" in run.stderr
    assert case_file.read_text() == raw
    # A file cannot be used as the report's parent directory.
    output.write_text("keep")
    run = subprocess.run(command + ["--output", str(output / "report.json")], capture_output=True)
    assert run.returncode == 2 and output.read_text() == "keep"


@pytest.mark.parametrize(
    "case_id,symbol,reason,revision",
    [
        ("direct_call", "tests/test_price.py::test_price", "Resolved call path", "both"),
        ("deleted_function", "tests/test_price.py::test_price", "Resolved call path", "before"),
        ("invalid_to_valid", "tests/test_price.py::test_price", "Resolved call path", "after"),
        ("mixed_revisions", "tests/test_bridge.py::test_g", "Resolved call path", "mixed"),
        ("changed_test", "tests/test_new.py::test_new", "Test itself changed", "after"),
        (
            "reexports",
            "tests/test_export.py::test_export",
            "Conservative module/import dependency",
            "both",
        ),
        (
            "inherited_dispatch",
            "tests/test_child.py::test_price",
            "Conservative module/import dependency",
            "both",
        ),
        (
            "conditional_definitions",
            "tests/test_price.py::test_price",
            "Conservative module/import dependency",
            "both",
        ),
        (
            "module_rebinding",
            "tests/test_price.py::test_price",
            "Resolved call path",
            "both",
        ),
    ],
)
def test_recorded_evidence_examples_require_deliberate_updates(case_id, symbol, reason, revision):
    """Selection alone cannot catch a stale explanation when resolution improves."""
    case = next(case for case in load_corpus(CASES) if case.id == case_id)
    report = analyze(case.request)
    item = next(rec for rec in report.recommendations if rec.symbol == symbol)
    assert (item.reason, item.path_revision) == (reason, revision)


def test_corpus_nested_resolution_shadowing_and_empty_module_contracts():
    cases = {case.id: case for case in load_corpus(CASES)}
    nested = analyze(cases["nested_functions"].request)
    assert any(
        (edge.source, edge.target, edge.kind) == ("core.py::price", "core.py::price.inner", "call")
        for edge in nested.edges
    )
    shadowed = analyze(cases["shadowed_names"].request)
    assert not any(
        edge.source in {"worker.py::parameter", "worker.py::local"}
        and edge.target == "core.py::price"
        and edge.kind == "call"
        for edge in shadowed.edges
    )
    empty = analyze(cases["empty_comments_movement"].request)
    assert empty.changed == []
    assert empty.recommendations == []
