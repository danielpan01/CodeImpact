"""Literal module-table dependency proofs read source without executing it."""

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot

LIB = """RULES = [('x', 'xs')]
def reader(word): return RULES[0][1]
def transitive(word): return reader(word)
def independent(word): return word.upper()
"""
TESTS = """import pytest
from lib import reader, transitive, independent
CASES = [('old', 'OLD')]
UNCHANGED = [('x', 'X')]
def test_reader(): assert reader('x') == 'xs'
def test_transitive(): assert transitive('x') == 'xs'
@pytest.mark.parametrize(('word', 'expected'), CASES)
def test_parameters(word, expected): assert independent(word) == expected
@pytest.mark.parametrize(('word', 'expected'), UNCHANGED)
def test_independent(word, expected): assert independent(word) == expected
"""


def review(lib=LIB, tests=TESTS, *, extra=None, head=None):
    base = {"lib.py": lib, "test_lib.py": tests, **(extra or {})}
    after = (
        base
        | {
            "lib.py": lib.replace("('x', 'xs')", "('y', 'ys')"),
            "test_lib.py": tests.replace("('old', 'OLD')", "('new', 'NEW')"),
        }
        | (head or {})
    )
    request = AnalysisRequest(base=Snapshot(files=base), head=Snapshot(files=after))
    report = analyze(request)
    validate_report(request, report)
    return report


def selected(report):
    return {r.symbol for r in report.recommendations}


def test_independent_test_excludes_both_changed_module_contributions():
    assert selected(review()) == {
        "test_lib.py::test_reader",
        "test_lib.py::test_transitive",
        "test_lib.py::test_parameters",
    }


def test_unrelated_test_sharing_its_changed_parameter_module():
    report = review(head={"lib.py": LIB})
    assert selected(report) == {"test_lib.py::test_parameters"}


def test_another_valid_dependency_survives_literal_module_filter():
    tests = TESTS + "\nfrom other import changed\ndef test_other(): changed(); independent('x')\n"
    report = review(
        tests=tests,
        extra={"other.py": "def changed(): return 1\n"},
        head={"other.py": "def changed(): return 2\n"},
    )
    assert "test_lib.py::test_other" in selected(report)
    assert (
        next(r for r in report.recommendations if r.symbol.endswith("test_other")).evidence_path[-1]
        == "other.py::changed"
    )


@pytest.mark.parametrize(
    "effect",
    [
        "RULES = unknown()\n",
        "RULES.append(unknown())\n",
        "publish(RULES)\n",
        "ALIAS = RULES\n",
        "startup()\n",
    ],
)
def test_unproven_initialization_retains_independent_test(effect):
    assert "test_lib.py::test_independent" in selected(review(lib=LIB + effect))


@pytest.mark.parametrize(
    "body",
    [
        "alias = RULES; return alias",
        "return RULES",
        "RULES.append(('z', 'zs')); return word",
        "global RULES; RULES = []; return word",
    ],
)
def test_data_alias_escape_mutation_and_rebinding_retain_readers(body):
    lib = LIB.replace("return word.upper()", body)
    assert "test_lib.py::test_independent" in selected(review(lib=lib))


@pytest.mark.parametrize(
    "imports",
    [
        "from exports import independent",
        "from lib import independent as renamed",
    ],
)
def test_aliases_and_reexports_stay_conservative(imports):
    tests = (
        "import pytest\n"
        + imports
        + "\ndef test_control(): "
        + ("renamed('x')\n" if "renamed" in imports else "independent('x')\n")
    )
    extra = {"exports.py": "from lib import independent\n"}
    assert selected(review(tests=tests, extra=extra)) == {"test_lib.py::test_control"}


def test_unknown_decorator_keeps_aggregate_path():
    tests = TESTS.replace("@pytest.mark.parametrize(('word', 'expected'), UNCHANGED)", "@unknown")
    assert "test_lib.py::test_independent" in selected(review(tests=tests))


def test_before_only_dependency_is_preserved():
    lib = LIB.replace("return word.upper()", "return RULES[0][0]")
    assert "test_lib.py::test_independent" in selected(
        review(lib=lib, head={"lib.py": LIB.replace("('x', 'xs')", "('y', 'ys')")})
    )


def test_deleted_binding_declines_proof():
    report = review(head={"lib.py": LIB.replace("RULES = [('x', 'xs')]\n", "")})
    assert "test_lib.py::test_independent" in selected(report)


def test_owned_literal_initialization_is_audited():
    lib = LIB + "\ndef install(word): RULES.insert(0, (word, word.upper()))\ninstall('extra')\n"
    assert "test_lib.py::test_independent" not in selected(review(lib=lib))


def test_unknown_eager_call_in_unchanged_import_keeps_fallback():
    lib = "import effects\n" + LIB
    assert "test_lib.py::test_independent" in selected(
        review(lib=lib, extra={"effects.py": "startup()\n"})
    )


def test_query_budget_exhaustion_keeps_independent_test(monkeypatch):
    from codeimpact import module_data

    monkeypatch.setattr(module_data, "MAX_STEPS", 1)
    assert "test_lib.py::test_independent" in selected(review())


def test_parameter_table_decorator_reader_remains_selected_without_body_reader():
    report = review(head={"lib.py": LIB})
    item = next(r for r in report.recommendations if r.symbol == "test_lib.py::test_parameters")
    assert item.reason == "Conservative module/import dependency"
    assert item.evidence_path[-1] == "test_lib.py::<module>"


def test_recursive_reader_stays_selected():
    lib = LIB.replace("return word.upper()", "return reader(word) if word else independent(word)")
    assert "test_lib.py::test_independent" in selected(review(lib=lib))


def test_recursive_nonreader_can_be_excluded():
    lib = LIB.replace("return word.upper()", "return word.upper() if word else independent('x')")
    assert "test_lib.py::test_independent" not in selected(review(lib=lib))


def test_effectful_rule_initializer_cannot_escape_data():
    lib = LIB + "\ndef install(): publish(RULES)\ninstall()\n"
    assert "test_lib.py::test_independent" in selected(review(lib=lib))


def test_rule_reader_in_default_keeps_fallback():
    lib = LIB.replace("def independent(word):", "def independent(word, table=RULES):")
    assert "test_lib.py::test_independent" in selected(review(lib=lib))


def test_eager_rule_mutation_rejects_external_callback():
    lib = LIB + "\nRULES.insert(0, callback())\n"
    assert "test_lib.py::test_independent" in selected(review(lib=lib))


def test_parameter_table_filter_preserves_a_path_to_an_edited_function():
    report = review(head={"lib.py": LIB.replace("upper()", "lower()")})
    result = next(r for r in report.recommendations if r.symbol == "test_lib.py::test_independent")
    assert result.evidence_path == [result.symbol, "lib.py::independent"]
    assert result.path_revision == "both"


@pytest.mark.parametrize(
    "hook",
    [
        "pytest_plugins = ['extension']\n",
        "def pytest_runtest_setup(item): reader('x')\n",
    ],
)
def test_test_module_lifecycle_customization_keeps_fallback(hook):
    assert "test_lib.py::test_independent" in selected(review(tests=TESTS + hook))


@pytest.mark.parametrize(
    "initializer",
    [
        "for row in RULES: COPIED.append(row)",
        "if RULES[0][0]: COPIED.append(('derived', 'DERIVED'))",
    ],
)
def test_eager_derived_data_keeps_fallback(initializer):
    lib = LIB.replace("return word.upper()", "return COPIED[0][1]")
    lib += "\nCOPIED = []\ndef install():\n    " + initializer + "\ninstall()\n"
    assert "test_lib.py::test_independent" in selected(review(lib=lib))


def test_default_initializer_cannot_hide_changed_data_effects():
    lib = LIB + "\nCOPIED = []\ndef install(): COPIED.append(RULES[0])\n"
    lib += "def helper(unused=install()): return ''\n"
    assert "test_lib.py::test_independent" in selected(review(lib=lib))


@pytest.mark.parametrize("hook", ["setup_function", "teardown_function"])
def test_function_lifecycle_keeps_fallback(hook):
    tests = TESTS + f"\ndef {hook}(function): reader('x')\n"
    assert "test_lib.py::test_independent" in selected(review(tests=tests))


def test_captured_conftest_keeps_fallback():
    conftest = "import pytest\nfrom lib import reader\n"
    conftest += "@pytest.fixture(autouse=True)\ndef prepare(): reader('x')\n"
    assert "test_lib.py::test_independent" in selected(review(extra={"conftest.py": conftest}))


def test_rule_container_type_change_keeps_initialization_fallback():
    lib = LIB + "\nRULES.append(('extra', 'EXTRA'))\n"
    head = lib.replace("[('x', 'xs')]", "(('y', 'ys'),)")
    assert "test_lib.py::test_independent" in selected(review(lib=lib, head={"lib.py": head}))


def test_parameter_row_arity_change_keeps_collection_fallback():
    head = TESTS.replace("[('old', 'OLD')]", "[('new', 'NEW', 'extra')]")
    assert "test_lib.py::test_independent" in selected(review(head={"test_lib.py": head}))


def test_mutated_parameter_data_keeps_collection_fallback():
    tests = TESTS + "\nCASES.append(('wrong',))\n"
    assert "test_lib.py::test_independent" in selected(review(tests=tests))
