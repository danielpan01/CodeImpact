"""Source-only tests for callbacks from literal pytest namespace rows."""

import json
from pathlib import Path
from textwrap import dedent

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest

TEST_PATH = "tests/test_items.py"
TEST = TEST_PATH + "::test_run"
TARGET = "src/items/cli.py::Item.helper"
TESTS = dedent("""\
    from argparse import Namespace
    from contextlib import contextmanager
    from items import run
    import pytest

    @contextmanager
    def expecting(value):
        yield value

    @pytest.mark.parametrize("callback,arguments,context", [
        (run, Namespace(first="1.2.3", second="1.2.3"), expecting("0")),
    ])
    def test_run(callback, arguments, context):
        with context as expected:
            result = callback(arguments)
            assert result == expected
    """)
CLI = dedent(r"""
    import re
    from argparse import Namespace

    def order(a, b):
        return (a > b) - (a < b)

    class Item:
        pattern = re.compile(
            r"^(?P<major>0|[1-9]\d*)\."
            r"(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)$"
        )

        def __init__(self, major, minor=0, patch=0):
            self._major = int(major)
            self._minor = int(minor)
            self._patch = int(patch)

        @classmethod
        def parse(cls, value):
            match = cls.pattern.match(value)
            if match is None:
                raise ValueError("invalid")
            return cls(**match.groupdict())

        def as_tuple(self):
            return (self._major, self._minor, self._patch)

        def compare(self, other):
            cls = type(self)
            if isinstance(other, str):
                other = cls.parse(other)
            elif not isinstance(other, cls):
                raise TypeError("invalid")
            a = self.as_tuple()[:3]
            b = other.as_tuple()[:3]
            result = order(a, b)
            if result:
                return result
            first, second = self._major, other._major
            return self.helper(first, second)

        @classmethod
        def helper(cls, first, second):
            return 7

    def run(args: Namespace):
        lhs = Item.parse(args.first)
        return str(lhs.compare(args.second))
    """).lstrip()
WRAPPER = dedent("""\
    from functools import wraps
    from . import cli

    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    run = decorate(cli.run)
    """)


def snapshot(tests=TESTS, cli=CLI, wrapper=WRAPPER):
    return {
        TEST_PATH: tests,
        "src/items/__init__.py": "from .public import run\n",
        "src/items/public.py": wrapper,
        "src/items/cli.py": cli,
    }


def request_for(tests=TESTS, cli=CLI, wrapper=WRAPPER):
    return AnalysisRequest.model_validate(
        {
            "base": {"files": snapshot(tests, cli, wrapper)},
            "head": {"files": snapshot(tests, cli.replace("return 7", "return 8"), wrapper)},
        }
    )


def callback_edge(report, sid=TEST, target=TARGET):
    return [edge for edge in report.edges if edge.source == sid and edge.target == target]


def test_callback_reaches_helper_for_equal_cores():
    request = request_for()
    report = analyze(request)
    validate_report(request, report)
    (edge,) = callback_edge(report)
    assert edge.revision == "both"
    (before,) = edge.before
    (after,) = edge.after
    assert before.location.line == after.location.line == 15
    assert "wrapper" in before.text
    assert "compare" in before.text
    rec = next(rec for rec in report.recommendations if rec.symbol == TEST)
    assert (rec.evidence_path, rec.path_revision) == ([TEST, TARGET], "both")


@pytest.mark.parametrize("revision", ["before", "after"])
def test_callback_proves_only_the_supported_revision(revision):
    request = request_for()
    other = request.head if revision == "before" else request.base
    other.files[TEST_PATH] = other.files[TEST_PATH].replace('second="1.2.3"', 'second="2.1.3"')
    report = analyze(request)
    validate_report(request, report)
    (edge,) = callback_edge(report)
    assert edge.revision == revision
    assert bool(edge.before) == (revision == "before")
    assert bool(edge.after) == (revision == "after")


@pytest.mark.parametrize(
    "tests",
    [
        TESTS.replace('second="1.2.3"', 'second="2.1.3"'),
        TESTS.replace('second="1.2.3"', 'second="2.4.0"'),
        TESTS.replace('second="1.2.3"', 'second="1." + "2.3"'),
        TESTS.replace('second="1.2.3"', 'second="invalid"'),
        TESTS.replace('second="1.2.3"', 'absent="1.2.3"'),
        TESTS.replace('second="1.2.3"', 'second="1.2.3", second="1.2.3"'),
        TESTS.replace('first="1.2.3", ', '**{"first": "1.2.3"}, '),
        TESTS.replace("import pytest\n", "import pytest\nNamespace = unknown\n"),
        TESTS.replace("import pytest\n", "import pytest\ncontextmanager = unknown\n"),
        TESTS.replace("import pytest\n", "import pytest\npytest = unknown\n"),
        TESTS.replace("import pytest\n", "import pytest\nrun = unknown\n"),
        TESTS.replace("    yield value", "    before_entry()\n    yield value"),
        TESTS.replace("    yield value", "    return value\n    yield value"),
        TESTS.replace('expecting("0")', "pytest.raises(ValueError)"),
        TESTS.replace("    with context", "    arguments = unknown\n    with context"),
        TESTS.replace(
            "        result = callback", "        callback = unknown\n        result = callback"
        ),
        TESTS.replace(
            '"callback,arguments,context"', '"callback,arguments,context", indirect=True,'
        ),
    ],
)
def test_callback_declines_unsupported_table_or_entry(tests):
    assert not callback_edge(analyze(request_for(tests)))


@pytest.mark.parametrize(
    "wrapper",
    [
        WRAPPER.replace("return func(*args, **kwargs)", "return None"),
        WRAPPER.replace("return func(*args, **kwargs)", "return func()"),
        WRAPPER.replace(
            "return func(*args, **kwargs)", "return None\n        return func(*args, **kwargs)"
        ),
        WRAPPER.replace(
            "return func(*args, **kwargs)", "func = unknown\n        return func(*args, **kwargs)"
        ),
        WRAPPER.replace(
            "return func(*args, **kwargs)",
            'if True:\n            raise ValueError("stop")\n        return func(*args, **kwargs)',
        ),
    ],
)
def test_callback_declines_a_wrapper_that_does_not_forward(wrapper):
    assert not callback_edge(analyze(request_for(wrapper=wrapper)))


def test_callback_declines_a_template_declared_after_pattern_compilation():
    cli = CLI.replace(
        "class Item:\n    pattern = re.compile(",
        'TEMPLATE = r"^unmatched{suffix}$"\n\n'
        "class Item:\n"
        '    pattern = re.compile(TEMPLATE.format(suffix=""))\n'
        "    TEMPLATE = (",
    ).replace(r'\.(?P<patch>0|[1-9]\d*)$"', r'\.(?P<patch>0|[1-9]\d*){suffix}$"')
    report = analyze(request_for(cli=cli))
    assert not callback_edge(report)


def test_pinned_semver_callback_at_line_104():
    case = Path("datasets/real-v5/cases/semver_prerelease_comparison.json")
    request = AnalysisRequest.model_validate(json.loads(case.read_bytes())["request"])
    report = analyze(request)
    validate_report(request, report)
    sid = "tests/test_pysemver-cli.py::test_should_process_parsed_cli_arguments"
    target = "src/semver/version.py::Version._nat_cmp"
    (edge,) = callback_edge(report, sid, target)
    assert edge.revision == "both"
    for evidence, call_line, end in ((edge.before, 416, 162), (edge.after, 412, 160)):
        (site,) = evidence
        assert (site.location.line, site.location.end_line) == (104, 104)
        assert (site.target_location.line, site.target_location.end_line) == (140, end)
        assert "row at line 71" in site.text
        assert f"Version.compare at line {call_line}" in site.text
    rec = next(rec for rec in report.recommendations if rec.symbol == sid)
    assert rec.evidence_edges == [edge.id]
    assert (rec.evidence_path, rec.path_revision) == ([sid, target], "both")


@pytest.mark.parametrize("version2", ["2.1.3", "2.4.0"])
def test_pinned_neighboring_rows_do_not_reach_helper(version2):
    case = Path("datasets/real-v5/cases/semver_prerelease_comparison.json")
    request = AnalysisRequest.model_validate(json.loads(case.read_bytes())["request"])
    path = "tests/test_pysemver-cli.py"
    for revision in (request.base, request.head):
        equal = 'Namespace(version1="1.2.3", version2="1.2.3")'
        assert revision.files[path].count(equal) == 1
        revision.files[path] = revision.files[path].replace(
            equal, f'Namespace(version1="1.2.3", version2="{version2}")'
        )
    report = analyze(request)
    validate_report(request, report)
    sid = path + "::test_should_process_parsed_cli_arguments"
    assert not callback_edge(report, sid, "src/semver/version.py::Version._nat_cmp")


@pytest.mark.parametrize("module", ["argparse", "contextlib", "re", "functools", "pytest"])
def test_callback_declines_source_shadowing_a_runtime_module(module):
    request = request_for()
    request.base.files[f"{module}.py"] = request.head.files[f"{module}.py"] = "pass\n"
    assert not callback_edge(analyze(request))


@pytest.mark.parametrize("path", [TEST_PATH, "tests/conftest.py", "conftest.py"])
def test_callback_declines_captured_pytest_hooks(path):
    request = request_for()
    for revision in (request.base, request.head):
        revision.files[path] = (
            revision.files.get(path, "") + "\ndef pytest_generate_tests(meta): pass\n"
        )
    assert not callback_edge(analyze(request))
