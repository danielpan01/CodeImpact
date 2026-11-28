"""Source-only regressions for keyed extrema called from pytest warning rows."""

import json
from pathlib import Path
from textwrap import dedent

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest

TEST_PATH = "tests/test_legacy.py"
CORE_PATH = "src/items/core.py"
TEST = f"{TEST_PATH}::test_choose"
HELPER = "src/items/helpers.py::choose"
TARGET = f"{CORE_PATH}::ordering.wrapper"
PINNED_PATH = "tests/test_deprecated_functions.py"
PINNED_TEST = f"{PINNED_PATH}::test_should_raise_deprecation_warnings"
PINNED_TARGET = "src/semver/version.py::_comparator.wrapper"
PINNED_HELPERS = {"max_ver": (44, 217, "__gt__"), "min_ver": (45, 236, "__lt__")}

TESTS = dedent("""\
    from items import choose, other
    import pytest

    @pytest.mark.parametrize("kwargs, func, args", [
        ({}, choose, ("1.2.3", "1.2.4")),
        ({}, other, ()),
    ])
    def test_choose(func, args, kwargs):
        with pytest.warns(DeprecationWarning, match="deprecated") as recorded:
            func(*args, **kwargs)
        assert recorded
    """)
CORE = dedent(r"""
    import re
    from functools import wraps

    def ordering(method):
        @wraps(method)
        def wrapper(self, other):
            return NotImplemented
        return wrapper

    class Item:
        pattern = re.compile(
            r"^(?P<major>0|[1-9]\d*)\."
            r"(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)$"
        )

        def __init__(self, major, minor, patch):
            self.major = int(major)
            self.minor = int(minor)
            self.patch = int(patch)

        @classmethod
        def parse(cls, text):
            match = cls.pattern.match(text)
            if match is None:
                raise ValueError("invalid")
            return cls(**match.groupdict())

        @ordering
        def __lt__(self, other):
            return self.major < other.major

        @ordering
        def __gt__(self, other):
            return self.major > other.major
    """).lstrip()
HELPERS = dedent("""\
    from functools import wraps
    from .core import Item

    def decorate(func):
        @wraps(func)
        def forward(*args, **kwargs):
            return func(*args, **kwargs)
        return forward

    @decorate
    def choose(left, right):
        return str(min(left, right, key=Item.parse))

    def other():
        return None
    """)


def request_for(tests=TESTS, helpers=HELPERS):
    files = {
        "src/items/__init__.py": "from .helpers import choose, other\n",
        CORE_PATH: CORE,
        "src/items/helpers.py": helpers,
        TEST_PATH: tests,
    }
    return AnalysisRequest.model_validate(
        {
            "base": {"files": files},
            "head": {
                "files": {
                    **files,
                    CORE_PATH: CORE.replace("return NotImplemented", "return False"),
                }
            },
        }
    )


def pinned_request():
    case = Path("datasets/real-v5/cases/semver_subclass_comparison.json")
    return AnalysisRequest.model_validate(json.loads(case.read_bytes())["request"])


def callback_edges(report, test=TEST):
    return [
        edge
        for edge in report.edges
        if edge.source == test
        and edge.kind == "call"
        and any("pytest.warns" in record.text for record in edge.before + edge.after)
    ]


def test_pinned_deprecation_warning_rows_reach_the_edited_comparator():
    request = pinned_request()
    report = analyze(request)
    validate_report(request, report)
    assert len(edges := callback_edges(report, PINNED_TEST)) == len(PINNED_HELPERS)
    for edge in edges:
        helper = edge.target.split("::")[1]
        row, builtin_line, method = PINNED_HELPERS[helper]
        assert edge.revision == "both"
        for revision, records in (("before", edge.before), ("after", edge.after)):
            (site,) = records
            assert (site.location.line, site.location.end_line) == (63, 63)
            assert f"row at line {row}" in site.text
            assert "at line 81" in site.text
            (comparison,) = [
                e for e in report.edges if e.source == edge.target and e.target == PINNED_TARGET
            ]
            (hop,) = getattr(comparison, revision)
            assert (hop.location.line, hop.location.end_line) == (builtin_line, builtin_line)
            assert method in hop.text
            assert (hop.target_location.line, hop.target_location.end_line) == (41, 52)
    rec = next(rec for rec in report.recommendations if rec.symbol == PINNED_TEST)
    assert (rec.evidence_path, rec.path_revision, rec.distance) == (
        [PINNED_TEST, "src/semver/_deprecated.py::max_ver", PINNED_TARGET],
        "both",
        2,
    )


def test_removing_both_qualifying_pinned_rows_removes_the_path():
    request = pinned_request()
    for snapshot in (request.base, request.head):
        source = snapshot.files[PINNED_PATH]
        lines = source.splitlines(keepends=True)
        assert all(f"({name}," in lines[row - 1] for name, (row, _, _) in PINNED_HELPERS.items())
        snapshot.files[PINNED_PATH] = "".join(lines[:43] + lines[45:])
    report = analyze(request)
    validate_report(request, report)
    assert not callback_edges(report, PINNED_TEST)
    assert PINNED_TEST not in {rec.symbol for rec in report.recommendations}


@pytest.mark.parametrize("rev", ["before", "after"])
def test_warning_callback_uses_only_the_revision_with_a_proved_row(rev):
    request = request_for()
    other = request.head if rev == "before" else request.base
    other.files[CORE_PATH] = other.files[CORE_PATH].replace("(?P<major>0|[1-9]", "(?P<major>[1-9]")
    report = analyze(request)
    validate_report(request, report)
    (edge,) = callback_edges(report)
    assert (edge.target, edge.revision) == (HELPER, rev)
    (rec,) = (rec for rec in report.recommendations if rec.symbol == TEST)
    assert (rec.evidence_path, rec.path_revision) == ([TEST, HELPER, TARGET], rev)


def test_each_pinned_warning_row_has_its_own_revision_evidence():
    request = pinned_request()
    for snapshot, removed in ((request.base, "min_ver"), (request.head, "max_ver")):
        lines = snapshot.files[PINNED_PATH].splitlines(keepends=True)
        del lines[PINNED_HELPERS[removed][0] - 1]
        snapshot.files[PINNED_PATH] = "".join(lines)
    report = analyze(request)
    validate_report(request, report)
    assert {
        edge.target.split("::")[1]: edge.revision for edge in callback_edges(report, PINNED_TEST)
    } == {"max_ver": "before", "min_ver": "after"}
    rec = next(rec for rec in report.recommendations if rec.symbol == PINNED_TEST)
    assert rec.evidence_path == [PINNED_TEST]
    assert rec.reason == "Test itself changed"


@pytest.mark.parametrize(
    "tests",
    [
        TESTS.replace("import pytest\n", "import pytest\npytest = other\n"),
        TESTS.replace("import pytest\n", "import pytest\nDeprecationWarning = other\n"),
        TESTS.replace("import pytest\n", "import pytest\nchoose = other\n"),
        TESTS.replace("    assert recorded", "    pytest = other"),
        TESTS.replace("    assert recorded", "    DeprecationWarning: type"),
        TESTS.replace("    assert recorded", "    args = other"),
        TESTS.replace("as recorded:", "as args:"),
        TESTS.replace("func(*args, **kwargs)", "func(*kwargs, **args)"),
        TESTS.replace("func(*args, **kwargs)", "func(*args, **kwargs, extra=0)"),
        TESTS.replace(
            '({}, choose, ("1.2.3", "1.2.4"))', '({"extra": 1}, choose, ("1.2.3", "1.2.4"))'
        ),
        TESTS.replace('"1.2.3"', '"1.2" + ".3"'),
        TESTS.replace('"1.2.3"', '"not-a-version"'),
        TESTS.replace("({}, other, ())", "({}, other, (unknown(),))"),
        TESTS.replace('match="deprecated"', 'match="["'),
        TESTS.replace('match="deprecated"', "match=unknown"),
        TESTS.replace('match="deprecated"', 'other="deprecated"'),
        TESTS.replace("        func(", "        if False: return\n        func("),
        TESTS.replace("    assert recorded", "    yield recorded"),
        TESTS + "\ndef pytest_generate_tests(meta): pass\n",
    ],
)
def test_warning_callback_declines_ambiguous_setup_or_binding(tests):
    assert not callback_edges(analyze(request_for(tests)))


@pytest.mark.parametrize(
    "helpers",
    [
        HELPERS.replace("return func(*args, **kwargs)", "return None"),
        HELPERS.replace("return func(*args, **kwargs)", "return other(*args, **kwargs)"),
        HELPERS.replace(
            "return func(*args, **kwargs)",
            'if True:\n            raise ValueError("stop")\n        return func(*args, **kwargs)',
        ),
        HELPERS.replace("return str(min(left, right, key=Item.parse))", "return left"),
        HELPERS + "\nmin = other\n",
    ],
)
def test_warning_callback_declines_ambiguous_forwarding(helpers):
    assert not callback_edges(analyze(request_for(helpers=helpers)))
