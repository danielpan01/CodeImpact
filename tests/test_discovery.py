"""Discovery is a bounded source policy, never upstream test collection."""

import pytest

from codeimpact.analyzer import analyze, build_index
from codeimpact.corpus import discover_tests
from codeimpact.evaluate import validate_report
from codeimpact.holdout_evaluate import discovery_audit
from codeimpact.models import AnalysisRequest, Snapshot


@pytest.mark.parametrize(
    "path,supported",
    [
        ("test.py", True),
        ("nested/test.py", True),
        ("test_unit.py", True),
        ("nested/unit_test.py", True),
        ("tests.py", False),
        ("testing.py", False),
        ("test/unit.py", False),
        ("production.py", False),
        ("Test.py", False),
    ],
)
def test_filename_policy_agrees_with_index_and_audit(path, supported):
    snapshot = Snapshot(
        files={path: "raise RuntimeError('must not execute')\ndef test_value(): return 1\n"}
    )
    expected = {f"{path}::test_value"} if supported else set()
    assert discover_tests(snapshot) == expected
    assert {
        sid for sid, node in build_index(snapshot).nodes.items() if node.kind == "test"
    } == expected
    audit = discovery_audit(snapshot)
    assert set(audit["discovered_ids"]) == expected
    assert audit["outside_discovery"] == (
        {} if supported else {f"{path}::test_value": "unsupported_filename"}
    )


def test_scope_boundaries_are_static_and_auditable():
    snapshot = Snapshot(
        files={
            "test.py": """raise RuntimeError('never run')
def test_top(): pass
class NotPytestNamed:
    async def test_method(self): pass
def helper():
    def test_nested(): pass
if True:
    def test_conditional(): pass
for value in []:
    def test_loop(): pass
try:
    def test_try(): pass
except Exception:
    pass
""",
            "broken_test.py": "def test_broken(:",
        }
    )
    expected = {
        "test.py::test_top",
        "test.py::NotPytestNamed.test_method",
        "test.py::helper.test_nested",
    }
    assert discover_tests(snapshot) == expected
    audit = discovery_audit(snapshot)
    assert set(audit["discovered_ids"]) == expected
    assert audit["outside_discovery"] == {
        f"test.py::{name}": "compound_statement"
        for name in ("test_conditional", "test_loop", "test_try")
    }
    assert audit["unparseable_files"] == ["broken_test.py"]


def test_duplicate_qualified_names_keep_existing_index_semantics_but_reject_labels():
    snapshot = Snapshot(files={"test.py": "def test_same(): return 1\ndef test_same(): return 2\n"})
    index = build_index(snapshot)
    assert index.nodes["test.py::test_same"].kind == "test"
    assert index.nodes["test.py::test_same"].line == 2
    with pytest.raises(ValueError, match="Ambiguous duplicate head test"):
        discover_tests(snapshot)


def test_same_names_in_separate_files_and_scopes_remain_distinct():
    source = "def test_same(): pass\nclass Group:\n    def test_same(self): pass\n"
    snapshot = Snapshot(files={"test.py": source, "nested/test.py": source})
    assert len(discover_tests(snapshot)) == 4


def test_new_filename_preserves_deleted_targets_and_excludes_deleted_tests():
    request = AnalysisRequest(
        base=Snapshot(
            files={
                "app.py": "def old(): return 1\n",
                "test.py": (
                    "from app import old\ndef test_kept(): return old()\n"
                    "def test_removed(): return old()\n"
                ),
            }
        ),
        head=Snapshot(
            files={"app.py": "", "test.py": "from app import old\ndef test_kept(): return old()\n"}
        ),
    )
    report = analyze(request)
    validate_report(request, report)
    assert [item.symbol for item in report.recommendations] == ["test.py::test_kept"]
    assert "test.py::test_removed" in report.removed
    assert report.recommendations[0].path_revision == "before"
    assert report.recommendations[0].evidence_path == ["test.py::test_kept", "app.py::old"]


def test_invalid_base_and_valid_head_discovery_keeps_exact_sources():
    request = AnalysisRequest(
        base=Snapshot(files={"test.py": "def test_new(:"}),
        head=Snapshot(files={"test.py": "def test_new(): return 1\n"}),
    )
    report = analyze(request)
    validate_report(request, report)
    assert [item.symbol for item in report.recommendations] == ["test.py::test_new"]
    assert report.recommendations[0].evidence_path == ["test.py::test_new"]
    assert report.source_files[0].before.parse_status == "unparseable"
    assert report.source_files[0].before.text == request.base.files["test.py"]


def test_filename_extension_preserves_deterministic_results():
    base = {
        "app.py": "def value(): return 1\n",
        "test.py": "from app import value\ndef test_value(): return value()\n",
    }
    head = base | {"app.py": "def value(): return 2\n"}
    reports = []
    for files_before, files_after in (
        (base, head),
        (dict(reversed(base.items())), dict(reversed(head.items()))),
    ):
        request = AnalysisRequest(
            base=Snapshot(files=files_before), head=Snapshot(files=files_after)
        )
        report = analyze(request)
        validate_report(request, report)
        assert report.recommendations[0].symbol == "test.py::test_value"
        result = report.model_dump(mode="json")
        result["stats"].pop("elapsed_ms")
        reports.append(result)
    assert reports[0] == reports[1]
