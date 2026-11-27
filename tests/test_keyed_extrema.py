"""Initial keyed min/max comparisons are proved from snapshot source."""

import json
from pathlib import Path
from textwrap import dedent

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest

CORE = "src/items/core.py"
HELPERS = "src/items/helpers.py"
TESTS = "tests/test_choose.py"
TEST = f"{TESTS}::test_choose"
HELPER = f"{HELPERS}::choose"
TARGET = f"{CORE}::ordering.wrapper"
ORDERING = dedent("""\
    from functools import wraps

    def ordering(method):
        @wraps(method)
        def wrapper(self, other):
            return NotImplemented
        return wrapper

    class Item:
        def __init__(self, value):
            self.value = value

        @classmethod
        def parse(cls, value):
            return cls(value)

        @ordering
        def __lt__(self, other):
            return self.value < other.value

        @ordering
        def __gt__(self, other):
            return self.value > other.value
    """)
CHOICE = dedent("""\
    from functools import wraps
    from .core import Item

    def deprecated(func):
        @wraps(func)
        def forward(*args, **kwargs):
            return func(*args, **kwargs)
        return forward

    @deprecated
    def choose(left, right):
        return str(min(
            left, right, key=Item.parse
        ))
    """)
CHECK = 'from items import choose\n\ndef test_choose():\n    assert choose("a", "b") == "a"\n'
PARAMETERIZED_CHECK = dedent("""\
    import pytest
    from items import choose

    @pytest.mark.parametrize("expected, right, left", [("a", "b", "a"), ["c", "c", "c"]])
    def test_choose(left, expected, right):
        assert choose(left, right) == expected
    """)


def request_for(helper=CHOICE, *, tests=CHECK, core=ORDERING):
    files = {
        CORE: core,
        HELPERS: helper,
        TESTS: tests,
        "src/items/__init__.py": "from .helpers import choose\n",
    }
    return AnalysisRequest.model_validate(
        {
            "base": {"files": files},
            "head": {
                "files": {**files, CORE: core.replace("return NotImplemented", "return False")}
            },
        }
    )


def keyed_edges(report):
    return [
        edge
        for edge in report.edges
        if any("key results" in entry.text for entry in edge.before + edge.after)
    ]


@pytest.mark.parametrize(
    ("operator", "method", "right"),
    [
        ("min", "__lt__", "b"),
        ("max", "__gt__", "b"),
        ("min", "__lt__", "a"),
        ("max", "__gt__", "a"),
    ],
)
def test_keyed_builtin_records_test_and_helper_hops(operator, method, right):
    helper = CHOICE.replace("str(min(", f"str({operator}(")
    request = request_for(helper, tests=CHECK.replace('"b"', f'"{right}"'))
    request.head.files[HELPERS] = "\n" + helper
    report = analyze(request)
    validate_report(request, report)
    (edge,) = keyed_edges(report)
    assert (edge.source, edge.target, edge.kind, edge.revision) == (HELPER, TARGET, "call", "both")
    for evidence, start in ((edge.before, 12), (edge.after, 13)):
        (site,) = evidence
        assert method in site.text
        assert (site.location.path, site.location.line, site.location.end_line) == (
            HELPERS,
            start,
            start + 2,
        )
        assert (site.target_location.path, site.target_location.line) == (CORE, 4)
    (rec,) = report.recommendations
    assert rec.evidence_path == [TEST, HELPER, TARGET]
    assert (rec.reason, rec.path_revision, rec.distance) == ("Resolved call path", "both", 2)
    first, second = (next(e for e in report.edges if e.id == eid) for eid in rec.evidence_edges)
    assert second == edge
    assert (first.source, first.target, first.kind) == (TEST, HELPER, "call")
    assert {item.location.line for item in first.before + first.after} == {4}


@pytest.mark.parametrize(
    "helper",
    [
        CHOICE + "\nmin = choose\n",
        CHOICE.replace("str(min", "str(max") + "\nmax = choose\n",
        CHOICE.replace("return str(min", "min = select\n    return str(min"),
        CHOICE.replace("Item.parse", "unknown"),
        CHOICE.replace("Item.parse", "Item.parse if left else opaque"),
        CHOICE + "\nItem.parse = choose\n",
        CHOICE.replace("left, right, key", "[left, right], key"),
        CHOICE.replace("left, right, key", "*left, right, key"),
        CHOICE.replace("left, right, key", "left, right, left, key"),
        CHOICE.replace("key=Item.parse", "key=Item.parse, default=None"),
        CHOICE.replace("key=Item.parse", "**Item.parse"),
        CHOICE.replace("key=Item.parse", "key=None"),
        CHOICE.replace("left, right, key", "left, opaque(), key"),
        CHOICE.replace("return str(min", "return alternate(min"),
        CHOICE.replace("func(*args, **kwargs)", "func(*kwargs, **args)"),
        CHOICE.replace("        return func", "        raise TypeError()\n        return func"),
    ],
)
def test_keyed_builtin_declines_ambiguous_or_unsupported_helper(helper):
    request = request_for(helper)
    report = analyze(request)
    validate_report(request, report)
    assert not keyed_edges(report)


def test_keyed_builtin_declines_key_with_unproved_receiver_binding():
    core = ORDERING + "\n    def bad_key(self):\n        return Item('key')\n"
    request = request_for(CHOICE.replace("Item.parse", "Item(left).bad_key"), core=core)
    assert not keyed_edges(analyze(request))


@pytest.mark.parametrize("alias", [False, True])
def test_keyed_builtin_declines_helper_with_unproved_receiver_binding(alias):
    source = (
        CHOICE
        + "\nclass Picker:\n"
        + "\n".join("    " + line for line in CHOICE[CHOICE.index("def choose") :].splitlines())
    )
    name, call = ("pick", "pick") if alias else ("Picker", "Picker().choose")
    if alias:
        source += "\n\npick = Picker().choose\n"
    request = request_for(
        source,
        tests=CHECK.replace(
            "from items import choose", f"from items.helpers import {name}"
        ).replace("assert choose(", f"assert {call}("),
    )
    assert not keyed_edges(analyze(request))


def test_keyed_builtin_declines_mixed_key_result_classes():
    core = (
        ORDERING.replace(
            "        return cls(value)",
            "        if value:\n            return cls(value)\n        return Other()",
        )
        + "\nclass Other:\n    pass\n"
    )
    assert not keyed_edges(analyze(request_for(core=core)))


def test_keyed_builtin_keeps_changed_test_evidence():
    request = request_for()
    request.head.files[TESTS] = CHECK.replace('== "a"', '== "b"')
    report = analyze(request)
    validate_report(request, report)
    assert keyed_edges(report)
    (rec,) = report.recommendations
    assert rec.evidence_path == [TEST]
    assert rec.reason == "Test itself changed"


@pytest.mark.parametrize("side", ["before", "after"])
def test_keyed_builtin_records_only_the_proved_revision(side):
    request = request_for()
    other = request.head if side == "before" else request.base
    other.files[HELPERS] += "\nmin = choose\n"
    report = analyze(request)
    validate_report(request, report)
    (edge,) = keyed_edges(report)
    assert edge.revision == side
    assert bool(edge.before) == (side == "before")
    assert bool(edge.after) == (side == "after")
    (rec,) = report.recommendations
    assert (rec.evidence_path, rec.path_revision) == ([TEST, HELPER, TARGET], side)


def test_keyed_builtin_does_not_borrow_revision_proof_from_another_test():
    # Ordinary import resolution still indexes the call in the revision with
    # opaque setup. Only the other test can prove the whole path there.
    tests = CHECK.replace("from items import", "from items.helpers import")
    request = request_for(CHOICE.replace("@deprecated\n", ""), tests=tests)
    other_path = "tests/test_other.py"
    request.base.files[other_path] = tests
    request.head.files[other_path] = tests
    request.head.files[TESTS] += "\nsetup()\n"
    report = analyze(request)
    validate_report(request, report)
    (edge,) = keyed_edges(report)
    assert edge.revision == "both"
    recs = {rec.symbol: rec for rec in report.recommendations}
    assert recs[f"{other_path}::test_choose"].path_revision == "both"
    assert TEST not in recs or recs[TEST].reason != "Resolved call path"


@pytest.mark.parametrize(
    "test",
    [
        CHECK.replace('"a", "b"', '*("a", "b")'),
        CHECK.replace('"a", "b"', 'left="a", right="b"'),
        CHECK.replace("def test_choose():", "def test_choose(unknown):"),
        CHECK.replace("def test_choose():", "def test_choose():\n    return"),
        CHECK + "    choose = opaque\n",
        CHECK.replace("    assert", "    if unknown:\n        assert"),
    ],
)
def test_keyed_builtin_declines_unsupported_test(test):
    assert not keyed_edges(analyze(request_for(tests=test)))


def test_pinned_semver_keyed_extrema_use_the_two_builtin_sites():
    case = Path("datasets/real-v5/cases/semver_subclass_comparison.json")
    request = AnalysisRequest.model_validate(json.loads(case.read_bytes())["request"])
    report = analyze(request, equality="keyed-extrema")
    validate_report(request, report, equality="keyed-extrema")
    from_tests = "tests/test_max-min.py"
    selected = {r.symbol: r for r in report.recommendations if r.symbol.startswith(from_tests)}
    for short, helper_line, test_lines in (("max", 217, [7, 11]), ("min", 236, [15, 19])):
        helper = f"src/semver/_deprecated.py::{short}_ver"
        for suffix, test_line in zip(("", "_same"), test_lines, strict=True):
            sid = f"{from_tests}::test_should_get_{short}{suffix}"
            rec = selected.pop(sid)
            assert rec.evidence_path == [sid, helper, "src/semver/version.py::_comparator.wrapper"]
            assert rec.path_revision == "both"
            first, second = (
                next(e for e in report.edges if e.id == eid) for eid in rec.evidence_edges
            )
            for evidence in first.before, first.after:
                (site,) = evidence
                assert (site.location.line, site.location.end_line) == (test_line, test_line)
            for evidence in second.before, second.after:
                (site,) = evidence
                assert (site.location.line, site.location.end_line) == (helper_line, helper_line)
                assert (site.target_location.line, site.target_location.end_line) == (41, 52)
    assert not selected


@pytest.mark.parametrize(("builtin", "method"), [("min", "__lt__"), ("max", "__gt__")])
def test_parameterized_keyed_builtin_resolves_named_columns(builtin, method):
    request = request_for(CHOICE.replace("str(min(", f"str({builtin}("), tests=PARAMETERIZED_CHECK)
    request.head.files[TESTS] = "\n" + PARAMETERIZED_CHECK
    report = analyze(request)
    validate_report(request, report)
    (rec,) = report.recommendations
    assert (rec.evidence_path, rec.path_revision, rec.distance) == (
        [TEST, HELPER, TARGET],
        "both",
        2,
    )
    first, second = (next(e for e in report.edges if e.id == eid) for eid in rec.evidence_edges)
    assert any("'left' and 'right'" in site.text for site in first.before)
    assert any("'left' and 'right'" in site.text for site in first.after)
    for evidence, line in ((first.before, 6), (first.after, 7)):
        (site,) = evidence
        assert (site.location.path, site.location.line, site.location.end_line) == (
            TESTS,
            line,
            line,
        )
    (edge,) = keyed_edges(report)
    assert edge == second
    assert all(method in site.text for site in edge.before + edge.after)


@pytest.mark.parametrize(
    "test",
    [
        PARAMETERIZED_CHECK.replace('["c", "c", "c"]', '["c", "c"]'),
        PARAMETERIZED_CHECK.replace('["c", "c", "c"]', '["c", "c", "c", "c"]'),
        PARAMETERIZED_CHECK.replace('["c", "c", "c"]', "('c' + '', 'c', 'c')"),
        PARAMETERIZED_CHECK.replace('["c", "c", "c"]', '["c", "c", 1]'),
        PARAMETERIZED_CHECK.replace('["c", "c", "c"]', "pytest.param('c', 'c', 'c')"),
        PARAMETERIZED_CHECK.replace('[("a", "b", "a"), ["c", "c", "c"]]', "[]"),
        PARAMETERIZED_CHECK.replace("expected, right, left", "expected, right, right"),
        PARAMETERIZED_CHECK.replace("expected, right, left", "expected, right, missing"),
        PARAMETERIZED_CHECK.replace("expected, right, left", "expected, right, , left"),
        PARAMETERIZED_CHECK.replace("test_choose(left,", "test_choose(*, left,"),
        PARAMETERIZED_CHECK.replace(
            "test_choose(left, expected, right)", "test_choose(left, expected, right='x')"
        ),
        PARAMETERIZED_CHECK.replace("import pytest", "import pytest as pytest"),
        PARAMETERIZED_CHECK.replace("import pytest", "import pytest\npytest = 1"),
        PARAMETERIZED_CHECK + "\ndef mutate():\n    pytest.mark.parametrize = alternate\n",
        PARAMETERIZED_CHECK + "    left = 'later'\n",
        PARAMETERIZED_CHECK + "    choose: str\n",
        PARAMETERIZED_CHECK.replace("expected", "choose"),
        PARAMETERIZED_CHECK.replace("expected", "request"),
        PARAMETERIZED_CHECK.replace("@pytest", "@other\n@pytest", 1),
        PARAMETERIZED_CHECK.replace('["c", "c", "c"]])', '["c", "c", "c"]], indirect=True)'),
        PARAMETERIZED_CHECK.replace("choose(left, right)", "choose(left, unrelated)"),
        PARAMETERIZED_CHECK.replace("choose(left, right)", "choose(left, right.upper())"),
        PARAMETERIZED_CHECK.replace("choose(left, right)", "choose(left, right=right)"),
    ],
)
def test_parameterized_keyed_builtin_declines_unproved_tables_or_bindings(test):
    report = analyze(request_for(tests=test))
    assert not keyed_edges(report)


@pytest.mark.parametrize(("rows", "columns"), [(65, 3), (64, 5)])
def test_parameterized_keyed_builtin_declines_oversized_tables(rows, columns):
    names = ["left", "right", "expected", *[f"extra{i}" for i in range(columns - 3)]]
    literals = [tuple("a" for _ in names)] * rows
    names_arg = ", ".join(names)
    tests = PARAMETERIZED_CHECK.split("@pytest", 1)[0] + dedent(f"""\
        @pytest.mark.parametrize({names_arg!r}, {literals!r})
        def test_choose({names_arg}):
            assert choose(left, right) == expected
        """)
    assert not keyed_edges(analyze(request_for(tests=tests)))


def test_parameterized_keyed_builtin_declines_unsupported_key():
    helper = CHOICE.replace("key=Item.parse", "key=Item.parse if left else unknown")
    request = request_for(helper, tests=PARAMETERIZED_CHECK)
    assert not keyed_edges(analyze(request))


@pytest.mark.parametrize("side", ["before", "after"])
def test_parameterized_keyed_builtin_requires_both_hops_in_each_revision(side):
    request = request_for(tests=PARAMETERIZED_CHECK)
    other = request.head if side == "before" else request.base
    other.files[HELPERS] += "\nmin = choose\n"
    report = analyze(request)
    validate_report(request, report)
    (edge,) = keyed_edges(report)
    (rec,) = report.recommendations
    assert edge.revision == side
    assert (rec.evidence_path, rec.path_revision) == ([TEST, HELPER, TARGET], side)


@pytest.mark.parametrize("unproved", ["base", "head"])
def test_parameterized_keyed_builtin_does_not_borrow_proof_from_another_test(unproved):
    tests = PARAMETERIZED_CHECK.replace("from items import", "from items.helpers import")
    request = request_for(CHOICE.replace("@deprecated\n", ""), tests=tests)
    other_path = "tests/test_other.py"
    request.base.files[other_path] = tests
    request.head.files[other_path] = tests
    getattr(request, unproved).files[TESTS] += "\nsetup()\n"
    report = analyze(request)
    validate_report(request, report)
    (edge,) = keyed_edges(report)
    assert edge.revision == "both"
    caller = next(e for e in report.edges if (e.source, e.target, e.kind) == (TEST, HELPER, "call"))
    assert caller.revision == "both"
    assert any("literal pytest columns" in site.text for site in caller.before + caller.after)
    unproved_sites = caller.before if unproved == "base" else caller.after
    assert all("literal pytest columns" not in site.text for site in unproved_sites)
    recs = {rec.symbol: rec for rec in report.recommendations}
    assert recs[f"{other_path}::test_choose"].path_revision == "both"
    assert TEST not in recs or recs[TEST].reason != "Resolved call path"


def test_pinned_semver_parameterized_keyed_min_records_one_test_definition():
    case = Path("datasets/real-v5/cases/semver_subclass_comparison.json")
    request = AnalysisRequest.model_validate(json.loads(case.read_bytes())["request"])
    report = analyze(request)
    validate_report(request, report)
    test_path = "tests/test_max-min.py"
    test = f"{test_path}::test_prerelease_order"
    helper = "src/semver/_deprecated.py::min_ver"
    target = "src/semver/version.py::_comparator.wrapper"
    (rec,) = [rec for rec in report.recommendations if rec.symbol == test]
    assert (rec.evidence_path, rec.path_revision, rec.score) == ([test, helper, target], "both", 72)
    first, second = (next(e for e in report.edges if e.id == eid) for eid in rec.evidence_edges)
    for caller, comparison in ((first.before, second.before), (first.after, second.after)):
        (site,) = caller
        assert (site.location.path, site.location.line, site.location.end_line) == (
            test_path,
            43,
            43,
        )
        assert "literal pytest columns 'left' and 'right'" in site.text
        (site,) = comparison
        assert (site.location.line, site.location.end_line) == (236, 236)
        assert (site.target_location.line, site.target_location.end_line) == (41, 52)
