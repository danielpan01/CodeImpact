"""Mixed-case unittest method discovery and revision-aware evidence."""

import pytest

from codeimpact.analyzer import analyze
from codeimpact.corpus import discover_tests
from codeimpact.evaluate import validate_report
from codeimpact.holdout_evaluate import discovery_audit
from codeimpact.models import AnalysisRequest, Snapshot

SOURCE = """import unittest
from lib import check
def testModuleLevel(): check()
class Example(unittest.TestCase):
    def testDirect(self): check()
    def test_snake(self): check()
    def helper(self):
        def testNested(): check()
        return testNested
class Unrelated:
    def testOther(self): check()
class Inherited(Example):
    def testInherited(self): check()
"""


def review(source=SOURCE, *, path="tests/test_checks.py", head_source=None, extra=None):
    files = {path: source, "lib.py": "def check(): return 1\n", **(extra or {})}
    head = files | {
        "lib.py": "def check(): return 2\n",
        path: source if head_source is None else head_source,
    }
    request = AnalysisRequest(base=Snapshot(files=files), head=Snapshot(files=head))
    report = analyze(request)
    validate_report(request, report)
    return request, report


@pytest.mark.parametrize("path", ["tests/test_checks.py", "suite/checks_test.py", "test.py"])
def test_direct_method_has_exact_resolved_evidence(path):
    req, report = review(path=path)
    direct = f"{path}::Example.testDirect"
    assert discover_tests(req.head) == {direct, f"{path}::Example.test_snake"}
    selected = {r.symbol: r for r in report.recommendations}
    assert set(selected) == discover_tests(req.head)
    assert selected[direct].evidence_path == [direct, "lib.py::check"]
    assert selected[direct].path_revision == "both"
    edge = next(e for e in report.edges if e.id == selected[direct].evidence_edges[0])
    assert edge.kind == "call" and edge.before and edge.after


def test_unsupported_filename_keeps_all_functions_outside_discovery():
    req, report = review(path="tests/checks.py")
    assert not discover_tests(req.head)
    assert report.recommendations == []


def test_current_audit_counts_unsupported_mixed_case_definitions():
    audit = discovery_audit(
        Snapshot(files={"test.py": SOURCE, "utility.py": "def testElsewhere(): pass\n"})
    )
    assert audit["test_shaped_definition_count"] == 7
    assert audit["discovered_ids"] == ["test.py::Example.testDirect", "test.py::Example.test_snake"]
    assert audit["outside_discovery"] == {
        "test.py::Example.helper.testNested": "unsupported_unittest_scope",
        "test.py::Inherited.testInherited": "unsupported_unittest_scope",
        "test.py::Unrelated.testOther": "unsupported_unittest_scope",
        "test.py::testModuleLevel": "unsupported_unittest_scope",
        "utility.py::testElsewhere": "unsupported_filename",
    }


@pytest.mark.parametrize(
    "source",
    [
        SOURCE.replace("import unittest", "import unittest as u").replace(
            "unittest.TestCase", "u.TestCase"
        ),
        SOURCE.replace("import unittest", "from unittest import TestCase").replace(
            "unittest.TestCase", "TestCase"
        ),
        SOURCE.replace("import unittest", "if flag:\n    import unittest"),
        SOURCE.replace("import unittest", "") + "\nimport unittest\n",
        SOURCE.replace("class Example", "unittest = proxy\nclass Example"),
        SOURCE + "\nunittest = proxy\n",
        SOURCE + "\nif flag:\n    unittest = proxy\n",
        SOURCE.replace("class Example", "unittest.TestCase = replacement\nclass Example"),
        SOURCE.replace(
            "class Example", "setattr(unittest, 'TestCase', replacement)\nclass Example"
        ),
        SOURCE.replace("class Example", "from unknown import *\nclass Example"),
        SOURCE.replace("class Example", "@decorate\nclass Example"),
        SOURCE.replace("unittest.TestCase):", "unittest.TestCase, Mixin):"),
        SOURCE.replace("unittest.TestCase):", "unittest.TestCase, metaclass=Meta):"),
        SOURCE.replace("unittest.TestCase):", "getattr(unittest, 'TestCase')):"),
        SOURCE.replace("    def testDirect", "    @wrap\n    def testDirect"),
        SOURCE.replace("    def testDirect", "    async def testDirect"),
        SOURCE.replace("    def test_snake", "    testDirect = None\n    def test_snake"),
        SOURCE + "\nclass Example: pass\n",
    ],
)
def test_ambiguous_subclasses_do_not_expand_existing_discovery(source):
    assert all(
        not node.name.endswith(".testDirect") or node.kind != "test"
        for node in review(source)[1].nodes
    )


@pytest.mark.parametrize("local", ["unittest.py", "src/unittest/__init__.py", "tests/unittest.py"])
def test_a_captured_shadow_blocks_the_proof(local):
    req, report = review(extra={local: "class TestCase: pass\n"})
    assert discover_tests(req.head) == {"tests/test_checks.py::Example.test_snake"}
    assert {r.symbol for r in report.recommendations} == discover_tests(req.head)


def test_nested_class_and_conditional_method_remain_outside_expansion():
    source = (
        SOURCE
        + """
def helper():
    class Local(unittest.TestCase):
        def testHidden(self): check()
class Conditional(unittest.TestCase):
    if flag:
        def testConditional(self): check()
"""
    )
    req, _ = review(source)
    assert discover_tests(req.head) == {
        "tests/test_checks.py::Example.testDirect",
        "tests/test_checks.py::Example.test_snake",
    }


def test_removed_method_stays_a_removed_test_without_recommendation():
    _, report = review(head_source=SOURCE.replace("    def testDirect(self): check()\n", ""))
    sid = "tests/test_checks.py::Example.testDirect"
    assert sid in report.removed
    assert next(n.kind for n in report.nodes if n.id == sid) == "test"
    assert all(r.symbol != sid for r in report.recommendations)


def test_rebound_head_class_keeps_before_node_but_is_no_longer_a_test():
    req, report = review(head_source=SOURCE + "\nunittest = object()\n")
    sid = "tests/test_checks.py::Example.testDirect"
    assert sid in discover_tests(req.base)
    assert sid not in discover_tests(req.head)
    assert next(n.kind for n in report.nodes if n.id == sid) == "function"
    assert all(r.symbol != sid for r in report.recommendations)


def test_mixed_case_method_retains_a_before_only_dependency():
    path = "test_checks.py"
    tests = "import unittest\nfrom lib import gone\nclass Example(unittest.TestCase):\n"
    tests += "    def testDeletion(self): gone()\n"
    request = AnalysisRequest(
        base=Snapshot(files={path: tests, "lib.py": "def gone(): pass\n"}),
        head=Snapshot(files={path: tests, "lib.py": "# removed\n"}),
    )
    report = analyze(request)
    validate_report(request, report)
    assert len(report.recommendations) == 1
    rec = report.recommendations[0]
    assert rec.evidence_path == [f"{path}::Example.testDeletion", "lib.py::gone"]
    assert rec.path_revision == "before"
