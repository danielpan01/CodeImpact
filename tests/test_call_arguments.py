"""Argument guards are analyzed as source data, never by executing fixture code."""

import json
from pathlib import Path

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot

CORE = """
def changed(text): return text + "old"
def worker(text, allow_unicode=False, max_length=0, separator='-'):
    if isinstance(max_length, bool) or not isinstance(max_length, int):
        raise TypeError('length')
    if not isinstance(separator, str):
        raise TypeError('separator')
    if allow_unicode:
        return text
    return changed(text)
def public(text, allow_unicode=False, max_length=0, separator='-', *, algorithm='legacy'):
    if algorithm == 'legacy':
        return text
    return worker(text, allow_unicode, max_length, separator)
"""
PRELUDE = (
    "from functools import partial\nfrom core import public\n"
    'slug = partial(public, algorithm="modern")\n'
)


def report_for(body, core=CORE, *, head_test=None, head_core=None):
    source = PRELUDE + body
    request = AnalysisRequest(
        base=Snapshot(files={"core.py": core, "test_use.py": source}),
        head=Snapshot(
            files={
                "core.py": head_core or core.replace('"old"', '"new"'),
                "test_use.py": head_test or source,
            }
        ),
    )
    report = analyze(request)
    validate_report(request, report)
    return report


def selected(report):
    return {r.symbol.split("::")[1] for r in report.recommendations}


@pytest.mark.parametrize(
    "argument",
    [
        "allow_unicode=True",
        "max_length=True",
        "max_length=1.5",
        "separator=None",
        'algorithm="legacy"',
        '**{"allow_unicode": True}',
    ],
)
def test_proven_bypass_or_early_raise_excludes_partial_call(argument):
    report = report_for(f'def test_bypass(): return slug("text", {argument})\n')
    assert not report.recommendations
    # Selection filtering does not rewrite the graph or manufacture new evidence.
    assert any(
        e.source == "test_use.py::test_bypass"
        and e.target == "core.py::public"
        and e.kind == "call"
        for e in report.edges
    )


@pytest.mark.parametrize(
    "argument",
    [
        "",
        "allow_unicode=False",
        "allow_unicode=unknown",
        "max_length=unknown",
        "separator=unknown",
        "algorithm=unknown",
        "**options",
        "*values",
        "allow_unicode=True, **options",
    ],
)
def test_unknown_and_affected_arguments_retain_calls(argument):
    report = report_for(
        'def test_keep(unknown, options, values): return slug("text"'
        + (", " + argument if argument else "")
        + ")\n"
    )
    assert selected(report) == {"test_keep"}


def test_partial_bound_keywords_can_be_overridden_by_call():
    source = PRELUDE.replace('algorithm="modern"', 'algorithm="modern", allow_unicode=True')
    source += 'def test_keep(): return slug("text", allow_unicode=False)\n'
    request = AnalysisRequest(
        base=Snapshot(files={"core.py": CORE, "test_use.py": source}),
        head=Snapshot(files={"core.py": CORE.replace('"old"', '"new"'), "test_use.py": source}),
    )
    report = analyze(request)
    validate_report(request, report)
    assert selected(report) == {"test_keep"}


def test_multiple_call_sites_require_all_sites_to_bypass():
    assert selected(
        report_for('def test_keep():\n    slug("a", allow_unicode=True)\n    return slug("b")\n')
    ) == {"test_keep"}


def test_same_line_call_sites_are_not_conflated():
    assert selected(report_for('def test_keep(): slug("a", allow_unicode=True); slug("b")\n')) == {
        "test_keep"
    }


@pytest.mark.parametrize(
    "rewrite",
    [
        "allow_unicode = unknown()\n    ",
        "if flag: allow_unicode = unknown()\n    ",
        'globals()["changed"] = replacement\n    ',
    ],
)
def test_rebinding_and_reflection_keep_uncertainty(rewrite):
    core = CORE.replace("    if allow_unicode:\n", "    " + rewrite + "if allow_unicode:\n")
    assert selected(
        report_for('def test_keep(): return slug("x", allow_unicode=True)\n', core)
    ) == {"test_keep"}


def test_shadowed_isinstance_does_not_prove_early_exit():
    core = "from custom import isinstance\n" + CORE
    assert selected(report_for('def test_keep(): return slug("x", max_length=True)\n', core)) == {
        "test_keep"
    }


def test_call_before_raise_remains_affected():
    core = CORE.replace(
        "raise TypeError('length')", "changed(text)\n        raise TypeError('length')"
    )
    assert selected(report_for('def test_keep(): return slug("x", max_length=True)\n', core)) == {
        "test_keep"
    }


def test_early_return_is_checked_before_later_calls():
    core = CORE.replace("raise TypeError('length')", "return text")
    assert not selected(report_for('def test_skip(): return slug("x", max_length=True)\n', core))


def test_caught_raise_does_not_hide_handler_dependency():
    core = CORE.replace(
        "    if allow_unicode:\n        return text\n    return changed(text)",
        "    try:\n        if allow_unicode: raise ValueError()\n"
        "    except ValueError:\n        return changed(text)\n    return changed(text)",
    )
    assert selected(
        report_for('def test_keep(): return slug("x", allow_unicode=True)\n', core)
    ) == {"test_keep"}


def test_deleted_changed_helper_retains_before_evidence():
    report = report_for(
        'def test_keep(): return slug("x")\n',
        head_core=CORE.replace('def changed(text): return text + "old"\n', ""),
    )
    assert selected(report) == {"test_keep"}


def test_changed_test_and_other_changed_module_are_not_hidden():
    body = 'def test_keep(): return slug("x", allow_unicode=True)\n'
    assert selected(report_for(body, head_test=PRELUDE + body.replace('"x"', '"y"'))) == {
        "test_keep"
    }
    request = AnalysisRequest(
        base=Snapshot(
            files={
                "core.py": CORE,
                "other.py": "def price(): return 1\n",
                "test_use.py": PRELUDE
                + "from other import price\n"
                + body.replace("return slug", "price(); return slug"),
            }
        ),
        head=Snapshot(
            files={
                "core.py": CORE.replace('"old"', '"new"'),
                "other.py": "def price(): return 2\n",
                "test_use.py": PRELUDE
                + "from other import price\n"
                + body.replace("return slug", "price(); return slug"),
            }
        ),
    )
    report = analyze(request)
    validate_report(request, report)
    assert selected(report) == {"test_keep"}


@pytest.mark.parametrize("case_id", ["slugify_ascii", "slugify_boundary"])
def test_seven_new_slugify_false_positives_removed_without_losing_affected(case_id):
    root = Path(__file__).parents[1] / "corpus/real-v2"
    data = json.loads((root / "cases" / f"{case_id}.json").read_text())
    baseline = json.loads((root / "baselines/module-partial-v1.json").read_text())
    previous = baseline["annotations"][case_id]["known_discrepancies"]["false_positives"]
    new = set(previous) - set(data["known_discrepancies"]["false_positives"])
    assert len(new) == (5 if case_id == "slugify_ascii" else 2)
    request = AnalysisRequest.model_validate(data["request"])
    report = analyze(request)
    validate_report(request, report)
    ids = {r.symbol for r in report.recommendations}
    assert not (new & ids)
    assert set(data["expected_affected"]) <= ids
    if case_id == "slugify_ascii":
        rec = next(
            r
            for r in report.recommendations
            if r.symbol.endswith(
                "ModernArgumentValidationTests.test_modern_accepts_valid_int_max_length"
            )
        )
        assert "slugify/slugify.py::_modern_slugify" in rec.evidence_path
        assert "slugify/_legacy.py::slugify" not in rec.evidence_path


@pytest.mark.parametrize("argument", ["True", "1.5", "None"])
def test_guard_type_checks_preserve_boolean_integer_distinction(argument):
    core = CORE.replace(
        "if isinstance(max_length, bool) or not isinstance(max_length, int):",
        "if not isinstance(max_length, int):",
    )
    report = report_for(f'def test_case(): return slug("x", max_length={argument})\n', core)
    assert selected(report) == ({"test_case"} if argument == "True" else set())


def test_boolean_expression_argument_keeps_operand_value():
    assert not selected(
        report_for('def test_skip(): return slug("x", algorithm="legacy" or unknown)\n')
    )


def test_mutable_definition_defaults_do_not_prove_a_branch():
    core = CORE.replace("allow_unicode=False", "allow_unicode=[True]")
    assert selected(report_for('def test_keep(): return slug("x")\n', core)) == {"test_keep"}


@pytest.mark.parametrize(
    "statement",
    [
        "slug.keywords.update(allow_unicode=False)",
        "alias = slug\nalias.keywords.update(allow_unicode=False)",
        "mutate(slug)",
    ],
)
def test_partial_keyword_mutation_or_escape_keeps_path(statement):
    source = PRELUDE.replace('algorithm="modern"', 'algorithm="modern", allow_unicode=True')
    source += statement + '\ndef test_keep(): return slug("x")\n'
    request = AnalysisRequest(
        base=Snapshot(files={"core.py": CORE, "test_use.py": source}),
        head=Snapshot(files={"core.py": CORE.replace('"old"', '"new"'), "test_use.py": source}),
    )
    report = analyze(request)
    validate_report(request, report)
    assert selected(report) == {"test_keep"}


@pytest.mark.parametrize(
    "shape",
    [
        "with changed(text):\n        pass",
        "try:\n        pass\n    except changed(text):\n        pass",
    ],
)
def test_context_and_exception_expressions_are_not_ignored(shape):
    core = CORE.replace("    if allow_unicode:\n", "    " + shape + "\n    if allow_unicode:\n")
    assert selected(
        report_for('def test_keep(): return slug("x", allow_unicode=True)\n', core)
    ) == {"test_keep"}


@pytest.mark.parametrize("name", ["MAX_STEPS", "MAX_DEPTH", "MAX_ITEMS"])
def test_guard_budget_exhaustion_retains_path(monkeypatch, name):
    import codeimpact.call_arguments as guards

    monkeypatch.setattr(guards, name, 0)
    assert selected(report_for('def test_keep(): return slug("x", allow_unicode=True)\n')) == {
        "test_keep"
    }


def test_unknown_callable_and_relevant_callback_escape_retain_path():
    for statement in ["callback(text)", "consume(changed)"]:
        core = CORE.replace(
            "    if allow_unicode:\n", "    " + statement + "\n    if allow_unicode:\n"
        )
        if statement.startswith("callback"):
            core = core.replace("separator='-'):", "separator='-', callback=None):")
        assert selected(
            report_for('def test_keep(): return slug("x", allow_unicode=True)\n', core)
        ) == {"test_keep"}


def test_recursive_callable_is_not_excluded():
    core = CORE.replace(
        "    if allow_unicode:\n", "    worker(text, allow_unicode)\n    if allow_unicode:\n"
    )
    assert selected(
        report_for('def test_keep(): return slug("x", allow_unicode=True)\n', core)
    ) == {"test_keep"}


def test_ordinary_call_fallback_is_preserved_when_no_exclusion_proof_covers_it():
    body = 'def test_keep(): return public("x", allow_unicode=True, algorithm="modern")\n'
    assert selected(report_for(body)) == {"test_keep"}


def test_literal_loop_alias_is_safe_only_for_invocation():
    for suffix, expected in [
        ("", set()),
        ("\n    fn.keywords.update(allow_unicode=False)", {"test_case"}),
    ]:
        source = PRELUDE.replace('algorithm="modern"', 'algorithm="modern", allow_unicode=True')
        source += (
            'def unrelated():\n    for name, fn in (("label", slug),):\n        fn("value")'
            + suffix
            + "\n"
        )
        source += 'def test_case(): return slug("x")\n'
        request = AnalysisRequest(
            base=Snapshot(files={"core.py": CORE, "test_use.py": source}),
            head=Snapshot(files={"core.py": CORE.replace('"old"', '"new"'), "test_use.py": source}),
        )
        assert selected(analyze(request)) == expected


def test_unknown_named_callable_keeps_potential_dependency():
    core = CORE.replace(
        "    if allow_unicode:\n", "    unknown_callback()\n    if allow_unicode:\n"
    )
    assert selected(
        report_for('def test_keep(): return slug("x", allow_unicode=True)\n', core)
    ) == {"test_keep"}


def test_function_default_mutation_is_not_assumed_immutable():
    core = CORE.replace("allow_unicode=False", "allow_unicode=True")
    core = core.replace("def public(text, ", "def public(text, *, ").replace(
        ", *, algorithm=", ", algorithm="
    )
    core += "\npublic.__kwdefaults__.update(allow_unicode=False)\n"
    assert selected(report_for('def test_keep(): return slug("x")\n', core)) == {"test_keep"}


def test_list_is_not_misclassified_as_tuple_in_guard():
    core = CORE.replace("if allow_unicode:", "if isinstance(allow_unicode, tuple):")
    assert selected(
        report_for('def test_keep(): return slug("x", allow_unicode=[True])\n', core)
    ) == {"test_keep"}


def test_unknown_mapping_contents_do_not_prove_inequality():
    core = CORE.replace("if allow_unicode:", 'if allow_unicode != {"skip": False}:')
    assert selected(
        report_for('def test_keep(value): return slug("x", allow_unicode={"skip": value})\n', core)
    ) == {"test_keep"}


@pytest.mark.parametrize(
    "call",
    [
        "slug(allow_unicode=True)",
        'slug("x", False, allow_unicode=True)',
        'slug("x", unknown_option=True, allow_unicode=True)',
    ],
)
def test_invalid_or_incomplete_argument_binding_keeps_uncertainty(call):
    assert selected(report_for("def test_keep(): return " + call + "\n")) == {"test_keep"}


@pytest.mark.parametrize(
    "extra",
    [
        'class Hook:\n    def __init__(self): changed("x")\n',
        "@decorate\ndef Hook(): pass\n",
        "def Hook(): pass\nHook = external\n",
    ],
)
def test_customized_or_ambiguous_other_calls_do_not_disappear(extra):
    core = CORE.replace("    if allow_unicode:\n", "    Hook()\n    if allow_unicode:\n") + extra
    assert selected(
        report_for('def test_keep(): return slug("x", allow_unicode=True)\n', core)
    ) == {"test_keep"}


@pytest.mark.parametrize(
    "mutation",
    [
        'options.pop("allow_unicode")',
        "mutate(options)",
        "alias = options\n    mutate(alias)",
    ],
)
def test_forwarded_mutable_options_keep_unknown_changes(mutation):
    prefix = CORE[: CORE.index("def public(")]
    core = prefix + 'def mutate(options): options.pop("allow_unicode")\n'
    core += (
        'def public(text, *, algorithm="legacy", **options):\n    '
        + mutation
        + "\n    return worker(text, **options)\n"
    )
    assert selected(
        report_for('def test_keep(): return slug("x", allow_unicode=True)\n', core)
    ) == {"test_keep"}


def test_mutable_guard_value_escaping_to_source_call_keeps_path():
    core = CORE.replace(
        "    if allow_unicode:\n", "    mutate(allow_unicode)\n    if allow_unicode:\n"
    )
    core += "\ndef mutate(flag): flag.clear()\n"
    assert selected(
        report_for('def test_keep(): return slug("x", allow_unicode=[True])\n', core)
    ) == {"test_keep"}


def test_relevant_callee_cannot_leave_mutable_guard_assumed_unchanged():
    core = CORE.replace(
        "    if allow_unicode:\n", "    inner(allow_unicode)\n    if allow_unicode:\n"
    )
    core += (
        "\ndef mutate(flag): flag.clear()\ndef inner(flag):\n"
        '    if flag: return mutate(flag)\n    return changed("x")\n'
    )
    assert selected(
        report_for('def test_keep(): return slug("x", allow_unicode=[True])\n', core)
    ) == {"test_keep"}
