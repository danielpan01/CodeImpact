"""Literal module-table dependency proofs read source without executing it."""

from textwrap import indent

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


FINITE_LIB = r"""import re
RULES = [('x', 'xs')]
EXEMPT = {'fish', 'rice'}
def plural(word):
    if not word or word.lower() in EXEMPT:
        return word
    return RULES[0][1]
def singular(word):
    for exception in EXEMPT:
        if re.search(r'(?i)\b(%s)\Z' % exception, word):
            return word
    return RULES[0][0]
"""
FINITE_TESTS = """import pytest
import lib
CASES = [('old', 'OLD')]
@pytest.mark.parametrize(('word',), [(item,) for item in lib.EXEMPT])
def test_members(word):
    assert lib.plural(word) == word
    assert lib.singular(word) == word
    assert lib.singular(lib.plural(word)) == word
"""
FINITE_TEST = "test_lib.py::test_members"


def test_finite_members_bypass_edited_rules_including_nested_call():
    assert FINITE_TEST not in selected(review(lib=FINITE_LIB, tests=FINITE_TESTS))


def test_a_member_can_reach_edited_rules_through_one_callee():
    library = FINITE_LIB.replace("def singular", "SINGULAR_EXEMPT = {'fish'}\ndef singular")
    library = library.replace("for exception in EXEMPT", "for exception in SINGULAR_EXEMPT")
    report = review(lib=library, tests=FINITE_TESTS)
    item = next(r for r in report.recommendations if r.symbol == FINITE_TEST)
    assert item.evidence_path[-1] == "lib.py::<module>"
    assert item.path_revision == "both"


@pytest.mark.parametrize(
    "library",
    [
        FINITE_LIB.replace("{'fish', 'rice'}", "unknown()"),
        FINITE_LIB.replace("'rice'", "'r.ce'"),
        FINITE_LIB + "EXEMPT.add('oil')\n",
        FINITE_LIB.replace("import re", "re = 'shadowed'"),
        FINITE_LIB.replace("return RULES[0][0]", "re = 'local'; return RULES[0][0]"),
        FINITE_LIB.replace("(?i)", "(?im)"),
        FINITE_LIB.replace("% exception, word)", "% exception, word, flags=0)"),
        FINITE_LIB.replace("return word", "return 'changed'", 1),
    ],
)
def test_unproved_collection_regex_or_return_stays_conservative(library):
    report = review(lib=library, tests=FINITE_TESTS, head={"test_lib.py": FINITE_TESTS})
    assert FINITE_TEST in selected(report)


@pytest.mark.parametrize(
    "peer",
    [
        "def test_peer(): lib.EXEMPT.add('oil')\n",
        "def test_peer(): lib.EXEMPT.remove('fish')\n",
        "def test_peer(): mutate(lib.EXEMPT)\n",
        "def setup_function(fn): pass\n",
    ],
)
def test_unproved_peer_or_lifecycle_effects_keep_fallback(peer):
    tests = FINITE_TESTS + peer
    report = review(lib=FINITE_LIB, tests=tests, head={"test_lib.py": tests})
    assert FINITE_TEST in selected(report)


def test_parameter_shadows_qualified_module_binding():
    tests = (
        FINITE_TESTS.split("@pytest")[0]
        + """@pytest.mark.parametrize(('lib',), [(item,) for item in lib.EXEMPT])
def test_members(lib): assert lib.plural(lib) == lib
"""
    )
    assert FINITE_TEST in selected(review(lib=FINITE_LIB, tests=tests))


def test_captured_collection_hook_blocks_finite_proof():
    report = review(
        lib=FINITE_LIB,
        tests=FINITE_TESTS,
        extra={"conftest.py": "def pytest_collection_modifyitems(items): pass\n"},
        head={"test_lib.py": FINITE_TESTS},
    )
    assert FINITE_TEST in selected(report)


def test_balanced_sibling_insertion_keeps_the_original_members():
    sibling = """
def test_peer():
    extra = 'oil'
    lib.EXEMPT.add(extra)
    try:
        assert lib.plural('different')
    finally:
        lib.EXEMPT.remove(extra)
"""
    report = review(lib=FINITE_LIB, tests=FINITE_TESTS + sibling)
    assert FINITE_TEST not in selected(report)
    assert "test_lib.py::test_peer" in selected(report)


def test_finite_bypass_preserves_an_independent_path():
    tests = FINITE_TESTS + "    assert CASES[0][0]\n"
    report = review(lib=FINITE_LIB, tests=tests)
    item = next(r for r in report.recommendations if r.symbol == FINITE_TEST)
    assert item.evidence_path == [FINITE_TEST, "test_lib.py::<module>"]
    assert item.path_revision == "both"


def test_deleted_finite_callee_retains_its_before_only_path():
    report = review(
        lib=FINITE_LIB,
        tests=FINITE_TESTS,
        head={"lib.py": FINITE_LIB.split("def singular(")[0]},
    )
    item = next(r for r in report.recommendations if r.symbol == FINITE_TEST)
    edge = next(e for e in report.edges if e.id in item.evidence_edges)
    assert item.evidence_path == [FINITE_TEST, "lib.py::singular"]
    assert item.path_revision == edge.revision == "before" and not edge.after
    assert "lib.py::singular" in report.removed


GUARDED_LIB = """RULES = [('x', 'xs')]
EXCEPTIONS = {'yes'}
def guarded(word):
    if not word or word.lower() in EXCEPTIONS:
        return word
    else:
        return RULES[0][1]
"""
GUARDED_TESTS = """import pytest
import lib
CASES = [('old', 'OLD')]
@pytest.mark.parametrize(('word', 'expected'), CASES)
def test_parameters(word, expected): assert word != expected
"""
GUARDED_TEST = "test_lib.py::test_guard"


def guard_review(
    body="assert lib.guarded('') == ''", *, library=GUARDED_LIB, extra=None, test_table=True
):
    test = "def test_guard():\n" + indent(body, "    ") + "\n"
    tests = GUARDED_TESTS + test
    head = None if test_table else {"test_lib.py": tests}
    return review(lib=library, tests=tests, extra=extra, head=head)


@pytest.mark.parametrize("condition", ["not word", "not word or word.lower() in EXCEPTIONS"])
def test_literal_empty_string_bypasses_the_edited_rule_table(condition):
    library = GUARDED_LIB.replace("not word or word.lower() in EXCEPTIONS", condition)
    assert selected(guard_review(library=library)) == {"test_lib.py::test_parameters"}


@pytest.mark.parametrize(
    "body",
    [
        "assert lib.guarded('x') == 'xs'",
        "assert lib.guarded('') == ''; assert lib.guarded('x') == 'xs'",
        "word = ''; word = 'x'; assert lib.guarded(word) == 'xs'",
        "word = ''; assert lib.guarded(word) == ''",
        "assert lib.guarded(unknown())",
        "assert lib.guarded(*('',)) == ''",
        "assert lib.guarded(word='') == ''",
    ],
)
def test_nonempty_mixed_or_unproved_arguments_keep_rule_dependency(body):
    report = guard_review(body, test_table=False)
    rec = next(item for item in report.recommendations if item.symbol == GUARDED_TEST)
    assert rec.evidence_path[-1] == "lib.py::<module>"
    assert rec.path_revision == "both"


@pytest.mark.parametrize(
    "library",
    [
        GUARDED_LIB.replace("not word", "not probe(word)"),
        GUARDED_LIB.replace("word.lower() in EXCEPTIONS", "probe(word)"),
        GUARDED_LIB.replace("    if", "    rules = RULES\n    if"),
        GUARDED_LIB.replace("    if", "    word = 'x'\n    if"),
        GUARDED_LIB.replace("return RULES", "yield RULES"),
        GUARDED_LIB + "configure()\n",
        GUARDED_LIB + "def setup_module(module): pass\n",
    ],
)
def test_unproved_guard_prefix_body_or_initialization_keeps_fallback(library):
    assert GUARDED_TEST in selected(guard_review(library=library, test_table=False))


def test_captured_collection_hook_keeps_empty_call_conservative():
    report = guard_review(
        extra={"conftest.py": "def pytest_collection_modifyitems(items): pass\n"},
        test_table=False,
    )
    assert GUARDED_TEST in selected(report)


def test_empty_bypass_keeps_independent_test_table_path():
    report = guard_review("assert lib.guarded('') == '' and CASES[0][0]")
    rec = next(item for item in report.recommendations if item.symbol == GUARDED_TEST)
    assert rec.evidence_path == [GUARDED_TEST, "test_lib.py::<module>"]
    assert rec.path_revision == "both"


def test_before_only_guard_read_retains_its_typed_evidence():
    before = GUARDED_LIB.replace("    if", "    rules = RULES\n    if")
    tests = GUARDED_TESTS + "def test_guard(): assert lib.guarded('') == ''\n"
    report = review(lib=before, tests=tests)
    result = next(item for item in report.recommendations if item.symbol == GUARDED_TEST)
    assert result.evidence_path[-1] == "lib.py::<module>"
    changed = GUARDED_LIB.replace("('x', 'xs')", "('y', 'ys')")
    report = review(lib=before, tests=tests, head={"lib.py": changed})
    result = next(item for item in report.recommendations if item.symbol == GUARDED_TEST)
    assert result.evidence_path == [GUARDED_TEST, "lib.py::guarded"]
    assert result.path_revision == "both"

    deleted = changed.split("def guarded(")[0]
    report = review(lib=before, tests=tests, head={"lib.py": deleted})
    result = next(item for item in report.recommendations if item.symbol == GUARDED_TEST)
    call = next(edge for edge in report.edges if edge.id in result.evidence_edges)
    assert result.evidence_path == [GUARDED_TEST, "lib.py::guarded"]
    assert "lib.py::guarded" in report.removed
    assert result.path_revision == call.revision == "before"
    assert call.before[0].location.path == "test_lib.py" and not call.after


SET_LIB = """WORDS = {'existing'}
OTHER = {'existing'}
def reader(word): return word in WORDS
def changed(word): return word.upper()
"""
SET_TESTS = """import pytest
import lib
CASES = [('old', 'OLD')]
@pytest.mark.parametrize(('word', 'expected'), CASES)
def test_changed(word, expected): assert lib.changed(word) == expected
"""
SET_TEST = "test_lib.py::test_set"


def set_test(
    *,
    prefix="key = 'new'",
    receiver="lib.WORDS",
    body="assert lib.reader(key)",
    cleanup="lib.WORDS.remove(key)",
    clause="",
):
    return (
        "def test_set():\n"
        + indent(f"{prefix}\n{receiver}.add(key)\ntry:\n", "    ")
        + indent(body, "        ")
        + "\n"
        + indent(clause, "    ")
        + "    finally:\n"
        + indent(cleanup, "        ")
        + "\n"
    )


def set_review(*, lib=SET_LIB, test=None, production_head=None):
    return review(
        lib=lib,
        tests=SET_TESTS + (test or set_test()),
        head={"lib.py": production_head or lib.replace("word.upper()", "word.lower()")},
    )


def test_restored_set_reader_sheds_only_unrelated_parameter_table():
    report = set_review()
    assert selected(report) == {"test_lib.py::test_changed"}
    item = report.recommendations[0]
    assert item.evidence_path == [item.symbol, "lib.py::changed"]
    assert item.path_revision == "both"


@pytest.mark.parametrize(
    "shape",
    [
        {"prefix": "key = 'existing'"},
        {"prefix": "key = unknown()"},
        {
            "prefix": "key = 'new'\nalias = lib.WORDS",
            "receiver": "alias",
            "cleanup": "alias.remove(key)",
        },
        {"cleanup": "lib.OTHER.remove(key)"},
        {"cleanup": "lib.WORDS.remove('other')"},
        {"cleanup": "lib.WORDS.discard(key)"},
        {"cleanup": "lib.WORDS.remove(key)\nunknown(key)"},
        {"body": "assert lib.reader(key)\nkey = 'other'"},
        {"clause": "except Exception:\n    pass\n"},
        {"clause": "except Exception:\n    pass\nelse:\n    pass\n"},
        {"body": "assert CASES and lib.reader(key)"},
        {"body": "assert unknown(lib.WORDS)"},
    ],
)
def test_incomplete_set_restoration_or_table_read_keeps_fallback(shape):
    item = next(
        r for r in set_review(test=set_test(**shape)).recommendations if r.symbol == SET_TEST
    )
    assert item.evidence_path == [SET_TEST, "test_lib.py::<module>"]
    assert item.path_revision == "both"


@pytest.mark.parametrize(
    "library",
    [
        SET_LIB.replace("{'existing'}", "['existing']"),
        SET_LIB + "WORDS.add('new')\n",
        SET_LIB + "WORDS = {'other'}\n",
        SET_LIB.replace("return word in WORDS", "WORDS.remove(word); return True"),
        SET_LIB.replace("return word in WORDS", "return publish(WORDS)"),
    ],
)
def test_unproved_literal_set_binding_or_transitive_effect_keeps_fallback(library):
    assert SET_TEST in selected(set_review(lib=library))


def test_reaching_edited_body_inside_guard_preserves_resolved_evidence():
    report = set_review(test=set_test(body="assert lib.changed(key)"))
    item = next(r for r in report.recommendations if r.symbol == SET_TEST)
    assert item.evidence_path == [SET_TEST, "lib.py::changed"]
    assert item.path_revision == "both"


def test_unproved_cleanup_on_one_revision_keeps_fallback():
    test = SET_TESTS + set_test()
    after_test = test.replace("('old', 'OLD')", "('new', 'NEW')").replace(
        "WORDS.remove(key)", "WORDS.remove('other')"
    )
    report = review(
        lib=SET_LIB,
        tests=test,
        head={"lib.py": SET_LIB.replace("upper()", "lower()"), "test_lib.py": after_test},
    )
    assert SET_TEST in selected(report)
