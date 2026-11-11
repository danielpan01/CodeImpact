"""The corpus is bounded JSON data, not a Python test suite to execute."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from codeimpact.corpus import CorpusCase, discover_tests, load_corpus

CASES = Path(__file__).resolve().parents[1] / "corpus/cases"


def case_data():
    source = "def test_a(): pass\ndef test_b(): pass\ndef test_c(): pass\n"
    return {
        "schema_version": "1.0",
        "id": "example",
        "description": "An authored example.",
        "category": "supported",
        "features": ["direct_calls"],
        "request": {
            "base": {"files": {"test_app.py": source}},
            "head": {"files": {"test_app.py": source}},
        },
        "expected_affected": {"test_app.py::test_a": "Calls the changed function."},
        "expected_unaffected": {"test_app.py::test_b": "Independent of the change."},
        "unclassified": {
            "test_app.py::test_c": "Dependency behavior is intentionally unspecified."
        },
        "known_discrepancies": {"false_positives": {}, "false_negatives": {}},
        "expected_unclassified_recommendations": [],
        "limitations": [],
    }


def test_checked_in_corpus_is_complete_and_sorted():
    cases = load_corpus(CASES)
    assert 20 <= len(cases) <= 25
    assert [c.id for c in cases] == sorted({c.id for c in cases})
    for case in cases:
        assert set(case.expected_affected).isdisjoint(case.expected_unaffected)
        assert set(case.expected_affected) | set(case.expected_unaffected) | set(
            case.unclassified
        ) == discover_tests(case.request.head)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda c: c.update(description="  "),
        lambda c: c.update(features=[]),
        lambda c: c.update(features=["calls", "calls"]),
        lambda c: c["expected_affected"].update({"test_app.py::test_a": " "}),
        lambda c: c["expected_unaffected"].update({"test_app.py::test_a": "Overlap."}),
        lambda c: c["expected_affected"].update({"test_app.py::missing": "Missing symbol."}),
        lambda c: c["unclassified"].clear(),
        lambda c: c.update(expected_unclassified_recommendations=["test_app.py::test_a"]),
        lambda c: c.update(expected_unclassified_recommendations=["test_app.py::test_c"] * 2),
        lambda c: c["known_discrepancies"]["false_positives"].update(
            {"test_app.py::test_a": "Wrong label."}
        ),
        lambda c: c["known_discrepancies"]["false_negatives"].update(
            {"test_app.py::test_b": "Wrong label."}
        ),
        lambda c: c["known_discrepancies"]["false_negatives"].update(
            {"test_app.py::test_a": "Supported case cannot hide a miss."}
        ),
        lambda c: c.update(category="known_limitation"),
        lambda c: c["request"]["head"]["files"].update({"../unsafe.py": ""}),
        lambda c: c["request"]["head"]["files"].update({"large.py": "x" * 200_001}),
        lambda c: c.update(extra="typo"),
    ],
)
def test_invalid_corpus_metadata_is_rejected(mutation):
    data = case_data()
    mutation(data)
    with pytest.raises((ValidationError, ValueError)):
        CorpusCase.model_validate(data)


def test_discovery_matches_documented_rule_without_executing_source():
    data = case_data()
    data["request"]["head"]["files"] = {
        "tests/test_app.py": (
            "class TestGroup:\n    async def test_async(self): pass\n"
            "def outer():\n    def test_nested(): pass\n"
            "if True:\n    def test_conditional(): pass\n"
        ),
        "sample_test.py": "def test_suffix(): pass\n",
        "app.py": "def test_not_collected(): pass\n",
        "test_invalid.py": "def test_broken(:\n",
    }
    from codeimpact.models import Snapshot

    assert discover_tests(Snapshot.model_validate(data["request"]["head"])) == {
        "tests/test_app.py::TestGroup.test_async",
        "tests/test_app.py::outer.test_nested",
        "sample_test.py::test_suffix",
    }


def test_removed_and_non_test_labels_are_rejected():
    for source in ("", "def helper(): pass\n", "if True:\n    def test_a(): pass\n"):
        data = case_data()
        data["request"]["head"]["files"]["test_app.py"] = source
        with pytest.raises(ValueError, match="head test"):
            CorpusCase.model_validate(data)


def test_loader_rejects_empty_duplicate_ids_duplicate_json_keys_and_bad_files(tmp_path):
    with pytest.raises(ValueError, match="No corpus cases"):
        load_corpus(tmp_path)
    (tmp_path / "one.json").write_text(json.dumps(case_data()))
    (tmp_path / "two.json").write_text(json.dumps(case_data()))
    with pytest.raises(ValueError, match="Duplicate case ID"):
        load_corpus(tmp_path)
    (tmp_path / "two.json").unlink()
    (tmp_path / "one.json").write_text('{"id":"one","id":"two"}')
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        load_corpus(tmp_path)
    (tmp_path / "one.json").write_text("{broken")
    with pytest.raises(ValueError):
        load_corpus(tmp_path)


def test_loader_rejects_symlinks_and_size_limits(tmp_path, monkeypatch):
    import codeimpact.corpus as corpus

    case_file = tmp_path / "one.json"
    case_file.write_text(json.dumps(case_data()))
    monkeypatch.setattr(corpus, "MAX_CASE_BYTES", 10)
    with pytest.raises(ValueError, match="size"):
        load_corpus(tmp_path)
    case_file.unlink()
    case_file.symlink_to(CASES / "direct_call.json")
    with pytest.raises(ValueError, match="symlink"):
        load_corpus(tmp_path)


def test_loader_enforces_case_count_and_aggregate_size(tmp_path, monkeypatch):
    import codeimpact.corpus as corpus

    raw = json.dumps(case_data())
    (tmp_path / "one.json").write_text(raw)
    second = case_data() | {"id": "second"}
    (tmp_path / "two.json").write_text(json.dumps(second))
    monkeypatch.setattr(corpus, "MAX_CASES", 1)
    with pytest.raises(ValueError, match="exceeds 1 cases"):
        load_corpus(tmp_path)
    monkeypatch.setattr(corpus, "MAX_CASES", 100)
    monkeypatch.setattr(corpus, "MAX_CORPUS_BYTES", len(raw.encode()) + 1)
    with pytest.raises(ValueError, match="size"):
        load_corpus(tmp_path)


def test_duplicate_test_definitions_are_not_ambiguous_labels():
    data = case_data()
    data["request"]["head"]["files"]["test_app.py"] += "def test_a(): pass\n"
    with pytest.raises(ValueError, match="duplicate head test"):
        CorpusCase.model_validate(data)
