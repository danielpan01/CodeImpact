"""Keep production evidence separate from literal test parameter evidence."""

import pytest

from codeimpact.analyzer import analyze, build_index
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot
from codeimpact.module_data import ModuleDataFallback

LIB = """def changed(value):
    return value.upper()
def wrapper(value):
    return changed(value)
def unrelated(value):
    return value.strip()
"""
TESTS = """import pytest
import lib
CASES = [('old', 'OLD')]
@pytest.mark.parametrize(('value', 'expected'), CASES)
def test_table(value, expected):
    assert lib.unrelated(value) == expected
def test_unrelated():
    assert lib.unrelated('unchanged')
def test_direct():
    assert lib.changed('direct')
def test_transitive():
    assert lib.wrapper('transitive')
"""
MODULE = "test_lib.py::<module>"


def review(*, lib=LIB, head_lib=None, tests=TESTS, head_tests=None, extra=None):
    base = {"lib.py": lib, "test_lib.py": tests, **(extra or {})}
    head = base | {
        "lib.py": lib.replace("return value.upper()", "return value.lower()")
        if head_lib is None
        else head_lib,
        "test_lib.py": tests.replace("[('old', 'OLD')]", "[('old', 'OLD'), ('new', 'NEW')]")
        if head_tests is None
        else head_tests,
    }
    request = AnalysisRequest(base=Snapshot(files=base), head=Snapshot(files=head))
    report = analyze(request)
    validate_report(request, report)
    return {r.symbol.split("::", 1)[1]: r for r in report.recommendations}


def test_mixed_change_preserves_direct_transitive_and_table_only_evidence():
    result = review()
    assert set(result) == {"test_table", "test_direct", "test_transitive"}
    assert result["test_table"].evidence_path == ["test_lib.py::test_table", MODULE]
    assert result["test_table"].reason == "Conservative module/import dependency"
    assert result["test_direct"].evidence_path == ["test_lib.py::test_direct", "lib.py::changed"]
    assert result["test_transitive"].evidence_path == [
        "test_lib.py::test_transitive",
        "lib.py::wrapper",
        "lib.py::changed",
    ]
    assert all(r.path_revision == "both" for r in result.values())


def test_shared_parameter_table_keeps_both_consumers():
    tests = TESTS.replace(
        "def test_unrelated():\n    assert lib.unrelated('unchanged')",
        "@pytest.mark.parametrize(('value', 'expected'), CASES)\n"
        "def test_unrelated(value, expected):\n    assert lib.unrelated(value)",
    )
    tests += "\ndef test_no_reader(): assert lib.unrelated('x')\n"
    result = review(tests=tests)
    assert "test_no_reader" not in result
    assert result["test_table"].evidence_path[-1] == MODULE
    assert result["test_unrelated"].evidence_path[-1] == MODULE


@pytest.mark.parametrize(
    "tests",
    [
        TESTS + "\nCASES.append(('new', 'NEW'))\n",
        TESTS + "\nALIAS = CASES\n",
        TESTS + "\ndef test_mutator(): CASES.append(('another', 'ANOTHER'))\n",
        TESTS + "\n@pytest.mark.parametrize(('value',), CASES)\ndef test_bad(value): pass\n",
        TESTS + "\n@unknown\ndef test_unknown(): pass\n",
        TESTS + "\ndef setup_function(fn): pass\n",
        TESTS + "\npytest_plugins = ['unknown']\n",
        TESTS + "\nlib.changed('eager')\n",
        TESTS + "\nBOOTSTRAP = lib.changed('default')\n",
        TESTS + "\ndef helper(flag=lib.wrapper('indirect')): pass\n",
        TESTS.replace(
            "def test_table(value, expected):", "def test_table(value, expected, *, fx):"
        ),
    ],
)
def test_incomplete_collection_keeps_module_evidence(tests):
    assert review(tests=tests)["test_unrelated"].evidence_path[-1] == MODULE


def test_malformed_new_row_keeps_module_evidence():
    head = TESTS.replace("[('old', 'OLD')]", "[('old', 'OLD'), ('new',)]")
    assert review(head_tests=head)["test_unrelated"].evidence_path[-1] == MODULE


def test_captured_conftest_keeps_module_evidence():
    result = review(extra={"conftest.py": "def pytest_runtest_setup(item): pass\n"})
    assert result["test_unrelated"].evidence_path[-1] == MODULE


def test_production_initializer_reaching_changed_function_declines():
    lib = LIB + "\nwrapper('during-import')\n"
    assert review(lib=lib)["test_unrelated"].evidence_path[-1] == MODULE


def test_an_edited_literal_table_without_parameter_registration_keeps_fallback():
    tests = TESTS.replace(
        "@pytest.mark.parametrize(('value', 'expected'), CASES)\n"
        "def test_table(value, expected):\n    assert lib.unrelated(value) == expected\n",
        "def test_table():\n    assert lib.unrelated(CASES[0][0])\n",
    )
    assert review(tests=tests)["test_unrelated"].evidence_path[-1] == MODULE


@pytest.mark.parametrize(
    "source",
    [
        LIB.replace("return value.upper()", "return value.lower()") + "\nunknown()\n",
        LIB.replace("def changed(value):", "def changed(value='x'):"),
        LIB.replace("def changed(value):", "@unknown\ndef changed(value):"),
        LIB + "\nALIAS = changed\n",
    ],
)
def test_other_production_change_shapes_keep_module_evidence(source):
    assert review(head_lib=source)["test_unrelated"].evidence_path[-1] == MODULE


def test_before_only_production_edge_survives_table_filter():
    tests = TESTS + "\ndef test_removed(): assert lib.removed()\n"
    result = review(lib=LIB + "\ndef removed(): return 1\n", head_lib=LIB, tests=tests)
    assert result["test_removed"].path_revision == "before"
    assert result["test_removed"].evidence_path == ["test_lib.py::test_removed", "lib.py::removed"]


@pytest.mark.parametrize("read_before", [True, False])
def test_table_read_in_only_one_revision_retains_the_table_contribution(read_before):
    prod = LIB.replace("return value.strip()", "from test_lib import CASES\n    return CASES[0][0]")
    old, new = (prod, LIB) if read_before else (LIB, prod)
    before = build_index(Snapshot(files={"lib.py": old, "test_lib.py": TESTS}))
    after = build_index(
        Snapshot(
            files={
                "lib.py": new,
                "test_lib.py": TESTS.replace("('old', 'OLD')", "('new', 'NEW')"),
            }
        )
    )
    fallback = ModuleDataFallback(before, after, {"lib.py", "test_lib.py"})
    assert fallback.allows("test_lib.py::test_unrelated", "test_lib.py")
