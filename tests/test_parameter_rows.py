"""Source-only controls for an added inline parameter row."""

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot

TESTS = """import datetime as dt
import pytest
from lib import changed, other

@pytest.mark.parametrize("value, expected", [(dt.timedelta(seconds=1), 1)])
def test_rows(value, expected):
    assert changed(value) == expected

def test_unrelated():
    assert other() == 3

def test_direct():
    assert changed(1) == 1

def wrapper():
    return changed(2)

def test_transitive():
    assert wrapper() == 2
"""
ROW = "(dt.timedelta(seconds=0.01), 0)"
LIB = """def changed(value):
    return value

def other():
    return 3
"""
PREFIX = "test_values.py::"


def request(*, source=TESTS, row=ROW, library=LIB, extra=None, base_extra=None, head_extra=None):
    head_tests = source.replace("), 1)])", f"), 1), {row}])", 1)
    assert head_tests != source
    base = {"test_values.py": source, "lib.py": library} | (extra or {})
    head = base | {
        "test_values.py": head_tests,
        "lib.py": library.replace("return value\n", "return value + 1\n", 1),
    }
    return AnalysisRequest(
        base=Snapshot(files=base | (base_extra or {})),
        head=Snapshot(files=head | (head_extra or {})),
    )


def selected(**options):
    req = request(**options)
    report = analyze(req)
    validate_report(req, report)
    return {rec.symbol: rec for rec in report.recommendations}


def test_added_safe_row_drops_unrelated_test_module_path():
    found = selected()
    assert set(found) == {PREFIX + test for test in ("test_rows", "test_direct", "test_transitive")}
    assert found[PREFIX + "test_rows"].reason == "Test itself changed"
    assert found[PREFIX + "test_direct"].evidence_path == [
        PREFIX + "test_direct",
        "lib.py::changed",
    ]
    assert found[PREFIX + "test_transitive"].evidence_path == [
        PREFIX + "test_transitive",
        PREFIX + "wrapper",
        "lib.py::changed",
    ]
    assert all(rec.path_revision == "both" for rec in found.values())


def test_literal_row_has_the_same_isolated_scope():
    assert PREFIX + "test_unrelated" not in selected(row="(0, 0)")


def test_separate_changed_dependency_keeps_exact_evidence():
    source = TESTS.replace("import pytest", "import pytest\nfrom side import separate")
    source = source.replace("assert other() == 3", "assert other() == separate()")
    found = selected(
        source=source,
        base_extra={"side.py": "def separate(): return 3\n"},
        head_extra={"side.py": "def separate(): return 4\n"},
    )
    rec = found[PREFIX + "test_unrelated"]
    assert rec.evidence_path == [PREFIX + "test_unrelated", "side.py::separate"]
    assert rec.path_revision == "both"


@pytest.mark.parametrize(
    "row",
    [
        "(opaque(), 0)",
        "(dt.timedelta(seconds=hook()), 0)",
        "(dt.timedelta(seconds=shared), 0)",
        "(dt.timedelta(**options), 0)",
        "(dt.timedelta(seconds=0.01),)",
        "(dt.timedelta(seconds=True), 0)",
        "(dt.timedelta(seconds=1e308), 0)",
    ],
)
def test_unknown_effectful_or_invalid_new_rows_keep_fallback(row):
    assert PREFIX + "test_unrelated" in selected(row=row)


@pytest.mark.parametrize(
    "source",
    [
        TESTS.replace("import pytest", "import pytest\npytest = replacement"),
        TESTS.replace("import datetime as dt", "import datetime as dt\ndt = replacement"),
        TESTS.replace("import datetime as dt", "import datetime as dt\ndt.timedelta = replacement"),
        TESTS.replace("import datetime as dt", "import datetime as dt\nexternal(dt)"),
        TESTS.replace("import pytest", "import pytest\nexternal(pytest)"),
        TESTS.replace(
            "def test_unrelated():",
            "def pytest_generate_tests(metafunc): pass\n\ndef test_unrelated():",
        ),
        TESTS.replace("def test_unrelated():", "@unknown\ndef test_unrelated():"),
        TESTS.replace("def test_unrelated():", "shared = []\n\ndef test_unrelated():").replace(
            "assert other() == 3", "shared.append(1)"
        ),
        TESTS.replace("assert other() == 3", "pytest.mark.parametrize('value', [(0,)])(test_rows)"),
    ],
)
def test_ambiguous_bindings_hooks_or_shared_state_keep_fallback(source):
    assert PREFIX + "test_unrelated" in selected(source=source)


@pytest.mark.parametrize("file", ["conftest.py", "datetime.py", "src/pytest/__init__.py"])
def test_captured_hook_or_import_shadow_retains_fallback(file):
    assert PREFIX + "test_unrelated" in selected(extra={file: "pass\n"})


def test_dependency_present_only_before_keeps_fallback():
    source = TESTS.replace("import pytest", "import pytest\nfrom prior import inspect_it")
    source = source.replace("assert other() == 3", "inspect_it()")
    found = selected(source=source, base_extra={"prior.py": "def inspect_it(): pass\n"})
    assert PREFIX + "test_unrelated" in found
