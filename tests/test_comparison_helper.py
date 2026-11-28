"""Source-only regressions for comparison paths through an operator wrapper."""

import json
from pathlib import Path
from textwrap import dedent

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest

CORE = "src/items/core.py"
TEST_FILE = "tests/test_items.py"
TEST = f"{TEST_FILE}::test_compare"
HELPER = f"{CORE}::Item.helper"
SOURCE = dedent("""\
    from functools import wraps

    def checked(operator):
        @wraps(operator)
        def wrapper(self, other):
            if not isinstance(other, Item):
                return NotImplemented
            return operator(self, other)
        return wrapper

    def order(a, b):
        return (a > b) - (a < b)

    class Item:
        def __init__(self, major=1, tag=None):
            self._major = int(major)
            self._tag = tag

        @property
        def major(self):
            return self._major

        def as_tuple(self):
            return (self.major, self._tag)

        def compare(self, other):
            a = self.as_tuple()[:1]
            b = other.as_tuple()[:1]
            core = order(a, b)
            if core:
                return core
            name, other_name = self._tag, other._tag
            return self.helper(name, other_name)

        @classmethod
        def helper(cls, first, second):
            return 10

        @checked
        def __lt__(self, other):
            return self.compare(other) < 0

        @checked
        def __ne__(self, other):
            return self.compare(other) != 0
    """)
TESTS = dedent("""\
    from items.core import Item

    def test_compare():
        left = Item("01", tag="alpha")
        right = Item(tag="beta")
        assert left < right
    """)


def request_for(tests=TESTS, core=SOURCE):
    files = {CORE: core, TEST_FILE: tests}
    return AnalysisRequest.model_validate(
        {
            "base": {"files": files},
            "head": {"files": {**files, CORE: core.replace("return 10", "return 11")}},
        }
    )


def helper_edges(report, target=HELPER):
    return [
        edge
        for edge in report.edges
        if edge.target == target and edge.source.startswith("tests/") and edge.kind == "call"
    ]


@pytest.mark.parametrize(("symbol", "method"), [("<", "__lt__"), ("!=", "__ne__")])
def test_same_normalized_core_reaches_the_helper(symbol, method):
    tests = TESTS.replace("left < right", f"left {symbol} right")
    request = request_for(tests + "\ndef test_unequal():\n    assert Item(1) < Item(2)\n")
    request.head.files[TEST_FILE] = "\n" + request.head.files[TEST_FILE]
    report = analyze(request)
    validate_report(request, report)
    (edge,) = helper_edges(report)
    assert (edge.source, edge.revision) == (TEST, "both")
    for entries, line in ((edge.before, 6), (edge.after, 7)):
        (entry,) = entries
        assert (entry.location.line, entry.location.end_line) == (line, line)
        assert all(name in entry.text for name in ("wrapper", method, "compare", "helper"))
    rec = next(rec for rec in report.recommendations if rec.symbol == TEST)
    assert (rec.evidence_path, rec.path_revision, rec.reason) == (
        [TEST, HELPER],
        "both",
        "Resolved call path",
    )


@pytest.mark.parametrize(
    "tests",
    [
        TESTS.replace('Item("01", tag="alpha")', 'Item(2, tag="alpha")'),
        TESTS.replace('Item("01", tag="alpha")', 'Item(unknown(), tag="alpha")'),
        TESTS.replace('Item("01", tag="alpha")', 'Item(-1, tag="alpha")'),
        TESTS.replace('Item(tag="beta")', 'Item(**{"major": 1})'),
        TESTS + "    Item: type\n",
        TESTS.replace("    assert left", "    left = unknown()\n    assert left"),
        TESTS.replace("assert left < right", "assert left == right"),
        TESTS.replace("assert left < right", "assert left < right < Item(1)"),
        TESTS.replace("assert left < right", "assert True\n    assert left < right"),
        TESTS.replace("assert left < right", "if left:\n        assert left < right"),
    ],
)
def test_comparison_helper_declines_unproved_operands_or_assertions(tests):
    assert not helper_edges(analyze(request_for(tests=tests)))


@pytest.mark.parametrize(
    "source",
    [
        SOURCE.replace("return operator(self, other)", "return NotImplemented"),
        SOURCE.replace("return operator(self, other)", "return operator(other, self)"),
        SOURCE.replace(
            "return operator(self, other)", "return False\n            return operator(self, other)"
        ),
        SOURCE.replace("if not isinstance(other, Item)", "if isinstance(other, Item)"),
        SOURCE + "\nisinstance = int\n",
        SOURCE + "\nint = str\n",
        SOURCE.replace("self._tag = tag", 'self._tag = int("unconvertible")'),
        SOURCE + "\nItem.compare = unknown\n",
        SOURCE + "\nItem.helper = unknown\n",
        SOURCE.replace("return (a > b) - (a < b)", "return 1"),
        SOURCE.replace("return self._major", "return self._missing"),
        SOURCE.replace("return self.compare(other) < 0", "return self.helper(None, None) < 0"),
        SOURCE.replace(
            "if core:\n            return core", "if not core:\n            return core"
        ),
        SOURCE.replace(
            "return self.helper(name, other_name)",
            "return 0\n        self.helper(name, other_name)",
        ),
    ],
)
def test_comparison_helper_declines_unproved_forwarding_or_core_checks(source):
    assert not helper_edges(analyze(request_for(core=source)))


@pytest.mark.parametrize("side", ["before", "after"])
def test_comparison_helper_proves_one_revision_independently(side):
    request = request_for()
    other = request.head if side == "before" else request.base
    other.files[CORE] = other.files[CORE].replace("major=1, tag=None", "major=2, tag=None")
    report = analyze(request)
    validate_report(request, report)
    (edge,) = helper_edges(report)
    assert (edge.source, edge.revision) == (TEST, side)
    assert bool(edge.before) == (side == "before")
    assert bool(edge.after) == (side == "after")


@pytest.mark.parametrize(
    ("name", "start", "end", "method"),
    [
        ("test_should_compare_prerelease_and_build_with_numbers", 299, 301, "__lt__"),
        ("test_should_compare_version_info_objects", 138, 138, "__ne__"),
        ("test_should_compare_prerelease_with_numbers_and_letters", 129, 129, "__lt__"),
    ],
)
def test_pinned_prerelease_comparisons_reach_changed_helper(name, start, end, method):
    case = Path("datasets/real-v5/cases/semver_prerelease_comparison.json")
    request = AnalysisRequest.model_validate(json.loads(case.read_bytes())["request"])
    report = analyze(request)
    validate_report(request, report)
    test = f"tests/test_compare.py::{name}"
    target = "src/semver/version.py::Version._nat_cmp"
    rec = next(r for r in report.recommendations if r.symbol == test)
    assert (rec.evidence_path, rec.path_revision, rec.reason) == (
        [test, target],
        "both",
        "Resolved call path",
    )
    (edge,) = [e for e in helper_edges(report, target) if e.source == test]
    for entries, helper_end in ((edge.before, 162), (edge.after, 160)):
        (entry,) = entries
        assert (entry.location.line, entry.location.end_line) == (start, end)
        assert (entry.target_location.line, entry.target_location.end_line) == (140, helper_end)
        assert all(
            name in entry.text
            for name in ("_comparator.wrapper", method, "Version.compare", "_nat_cmp")
        )


DICTIONARY_SOURCE = SOURCE.replace(
    "isinstance(other, Item)", "isinstance(other, (Item, dict))"
).replace(
    "        a = self.as_tuple()[:1]",
    "        cls = type(self)\n"
    "        if isinstance(other, str):\n"
    "            return NotImplemented\n"
    "        elif isinstance(other, dict):\n"
    "            other = cls(**other)\n"
    "        elif not isinstance(other, cls):\n"
    "            raise TypeError()\n"
    "        a = self.as_tuple()[:1]",
)
DICTIONARY_TESTS = TESTS.replace(
    'right = Item(tag="beta")', 'right = dict(major=1, tag="beta")'
).replace("assert left < right", "assert left != right")


def test_dictionary_comparison_reaches_helper_through_the_conversion():
    request = request_for(DICTIONARY_TESTS, DICTIONARY_SOURCE)
    report = analyze(request)
    validate_report(request, report)
    (edge,) = helper_edges(report)
    assert (edge.source, edge.revision) == (TEST, "both")
    for entries in (edge.before, edge.after):
        (site,) = entries
        assert site.location.path == TEST_FILE and site.location.line == 6
        assert "cls(**other) at line 31" in site.text
    rec = next(row for row in report.recommendations if row.symbol == TEST)
    assert (rec.evidence_path, rec.path_revision) == ([TEST, HELPER], "both")


def test_dictionary_comparison_accepts_inline_literal_keywords():
    tests = DICTIONARY_TESTS.replace('    right = dict(major=1, tag="beta")\n', "").replace(
        "assert left != right", 'assert left != dict(major=1, tag="beta")'
    )
    report = analyze(request_for(tests, DICTIONARY_SOURCE))
    (edge,) = helper_edges(report)
    assert (edge.source, edge.revision) == (TEST, "both")
    assert edge.before[0].location.line == edge.after[0].location.line == 5


@pytest.mark.parametrize(
    "tests",
    [
        DICTIONARY_TESTS.replace('dict(major=1, tag="beta")', 'dict(major=1 + 0, tag="beta")'),
        DICTIONARY_TESTS.replace('dict(major=1, tag="beta")', 'dict(**{"major": 1})'),
        DICTIONARY_TESTS.replace('dict(major=1, tag="beta")', 'dict({"major": 1})'),
        DICTIONARY_TESTS.replace('dict(major=1, tag="beta")', '{"major": 1}'),
        DICTIONARY_TESTS.replace('dict(major=1, tag="beta")', "dict(unknown=1)"),
        DICTIONARY_TESTS.replace('dict(major=1, tag="beta")', "dict(major=1, major=1)"),
        DICTIONARY_TESTS.replace('dict(major=1, tag="beta")', 'dict(major=2, tag="beta")'),
        DICTIONARY_TESTS.replace("    assert", "    right = unknown()\n    assert"),
        DICTIONARY_TESTS.replace("    assert", "    right = dict(major=2)\n    assert"),
        "dict = int\n" + DICTIONARY_TESTS,
        DICTIONARY_TESTS + "    dict: type\n",
        DICTIONARY_TESTS.replace("assert left != right", "assert right != left"),
        DICTIONARY_TESTS.replace("assert left != right", "assert left < right"),
    ],
)
def test_dictionary_comparison_declines_unproved_input(tests):
    assert not helper_edges(analyze(request_for(tests, DICTIONARY_SOURCE)))


@pytest.mark.parametrize(
    "core",
    [
        DICTIONARY_SOURCE.replace("isinstance(other, (Item, dict))", "isinstance(other, Item)"),
        DICTIONARY_SOURCE.replace("cls(**other)", "cls(**unproved)"),
        DICTIONARY_SOURCE.replace("cls(**other)", "cls(**other, tag=None)"),
        DICTIONARY_SOURCE.replace("type(self)", "type(other)"),
        DICTIONARY_SOURCE.replace("major=1, tag=None", "major=1, /, tag=None"),
        DICTIONARY_SOURCE.replace("isinstance(other, str)", "isinstance(other, (str, dict))"),
        DICTIONARY_SOURCE + "\ndict = int\n",
    ],
)
def test_dictionary_comparison_declines_unproved_guard_or_conversion(core):
    assert not helper_edges(analyze(request_for(DICTIONARY_TESTS, core)))


@pytest.mark.parametrize("side", ["before", "after"])
def test_dictionary_comparison_proves_conversion_in_one_revision(side):
    request = request_for(DICTIONARY_TESTS, DICTIONARY_SOURCE)
    other = request.head if side == "before" else request.base
    other.files[CORE] = other.files[CORE].replace("cls(**other)", "cls(**unproved)")
    report = analyze(request)
    validate_report(request, report)
    (edge,) = helper_edges(report)
    assert (edge.source, edge.revision) == (TEST, side)
    assert bool(edge.before) == (side == "before")
    assert bool(edge.after) == (side == "after")


def test_pinned_prerelease_dictionary_comparison_at_line_167():
    case = Path("datasets/real-v5/cases/semver_prerelease_comparison.json")
    request = AnalysisRequest.model_validate(json.loads(case.read_bytes())["request"])
    report = analyze(request)
    validate_report(request, report)
    sid = "tests/test_compare.py::test_should_compare_version_dictionaries"
    target = "src/semver/version.py::Version._nat_cmp"
    rec = next(row for row in report.recommendations if row.symbol == sid)
    assert (rec.evidence_path, rec.path_revision, rec.reason) == (
        [sid, target],
        "both",
        "Resolved call path",
    )
    (edge,) = [edge for edge in helper_edges(report, target) if edge.source == sid]
    assert rec.evidence_edges == [edge.id]
    for entries, line, end in ((edge.before, 400, 162), (edge.after, 396, 160)):
        (site,) = entries
        assert (site.location.line, site.location.end_line) == (167, 167)
        assert (site.target_location.line, site.target_location.end_line) == (140, end)
        assert f"cls(**other) at line {line}" in site.text
