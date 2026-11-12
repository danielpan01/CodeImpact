"""Partial-call inputs are source strings, never executed or imported."""

import json
from pathlib import Path

import pytest

from codeimpact.analyzer import analyze, build_index
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot


def indexed(source, extra=None):
    return build_index(
        Snapshot(
            files={
                "core.py": "def price(value=0, mode='modern'): return value + 1\n",
                "test_use.py": source,
            }
            | (extra or {})
        )
    )


def targets(index, sid="test_use.py::test_read"):
    return {e.target for e in index.edges.values() if e.source == sid and e.kind == "call"}


@pytest.mark.parametrize(
    "factory",
    [
        ("from functools import partial", "partial"),
        ("from functools import partial as bind", "bind"),
        ("import functools", "functools.partial"),
        ("import functools as ft", "ft.partial"),
    ],
)
def test_module_partial_targets_callable_not_factory(factory):
    statement, name = factory
    index = indexed(
        f"{statement}\nfrom core import price as original\n"
        f"quote = {name}(original, 3, mode='modern')\n"
        "def test_read(): return quote()\n"
    )
    assert targets(index) == {"core.py::price"}
    edge = index.edges[("test_use.py::test_read", "core.py::price", "call")]
    assert edge.evidence[0].location.line == 4
    assert "partial" in edge.evidence[0].text
    assert not any(
        e.source == "test_use.py::<module>" and e.kind == "call" for e in index.edges.values()
    )


@pytest.mark.parametrize("prefix", ["", "src/"])
@pytest.mark.parametrize("target", ["from .core import price", "from . import core"])
def test_relative_src_and_reexported_targets(prefix, target):
    value = "price" if target.endswith("price") else "core.price"
    path = prefix + "pkg/test_use.py"
    index = build_index(
        Snapshot(
            files={
                prefix + "pkg/core.py": "def price(): return 1\n",
                prefix + "pkg/__init__.py": "from .core import price as public\n",
                path: f"from functools import partial\n{target}\nquote = partial({value})\n"
                "def test_read(): return quote()\n",
                "test_export.py": "from functools import partial\nfrom pkg import public\n"
                "quote = partial(public)\ndef test_read(): return quote()\n",
            }
        )
    )
    assert targets(index, path + "::test_read") == {prefix + "pkg/core.py::price"}
    assert targets(index, "test_export.py::test_read") == {prefix + "pkg/core.py::price"}


def test_package_reexport_wins_over_same_named_submodule():
    index = indexed(
        "from functools import partial\nfrom pkg import api as public\n"
        "quote = partial(public, mode='modern')\ndef test_read(): return quote()\n",
        {
            "pkg/__init__.py": "from .api import api\n",
            "pkg/api.py": "def api(mode='legacy'): return 1\n",
        },
    )
    assert targets(index) == {"pkg/api.py::api"}


def test_same_module_target_and_annotated_binding():
    index = indexed(
        "from functools import partial\ndef price(): return 1\n"
        "quote: object = partial(price)\ndef test_read(): return quote()\n"
    )
    assert targets(index) == {"test_use.py::price"}


@pytest.mark.parametrize(
    "extra",
    [
        "quote = other",
        "del quote",
        "if enabled: quote = other",
        "for quote in values: pass",
        "def quote(): return 5",
        "quote = partial(price)",
        "partial = other",
        "price = other",
        "def mutate():\n    global quote\n    quote = other",
        "def mutate():\n    global price\n    price = other",
        "from unknown import *",
    ],
)
def test_ambiguous_module_bindings_never_resolve(extra):
    source = (
        "from functools import partial\nfrom core import price\nquote = partial(price)\n"
        + extra
        + "\ndef test_read(): return quote()\n"
    )
    assert targets(indexed(source)) == set()


@pytest.mark.parametrize(
    "expression",
    [
        "partial(make_target())",
        "partial(obj.method)",
        "partial(lambda: 1)",
        "partial(*values)",
        "partial(price, **options)",
        "partial(price, *values)",
        "partial(price, mutate())",
    ],
)
def test_dynamic_partial_construction_is_not_guessed(expression):
    assert not targets(
        indexed(
            "from functools import partial\nfrom core import price\n"
            f"quote = {expression}\ndef test_read(): return quote()\n"
        )
    )


@pytest.mark.parametrize(
    "body",
    [
        "return quote()\n    quote = other",
        "quote: object\n    return quote()",
        "del quote\n    return quote()",
        "from other import quote\n    return quote()",
        "global quote\n    return quote()",
        "def quote(): return 5\n    return quote()",
        "return (lambda quote: quote())(other)",
        "return [quote() for quote in values]",
    ],
)
def test_local_scopes_do_not_leak_module_partial(body):
    index = indexed(
        "from functools import partial\nfrom core import price\n"
        "quote = partial(price)\ndef test_read():\n    " + body + "\n"
    )
    assert "core.py::price" not in targets(index)


def test_enclosing_parameter_shadows_module_partial():
    index = indexed(
        "from functools import partial\nfrom core import price\nquote = partial(price)\n"
        "def outer(quote):\n    def inner(): return quote()\n    return inner\n"
    )
    assert not targets(index, "test_use.py::outer.inner")


def test_separate_function_scope_does_not_rebind_partial():
    index = indexed(
        "from functools import partial\nfrom core import price\nquote = partial(price)\n"
        "def separate(quote): return quote\ndef test_read(): return quote()\n"
    )
    assert targets(index) == {"core.py::price"}


@pytest.mark.parametrize(
    "setup",
    [
        "quote = partial(price)\nfrom core import price",
        "quote = partial(price)\ndef price(): return 1",
        "from core import price\nquote = partial(price)\nfrom functools import partial",
    ],
)
def test_capture_requires_bindings_to_precede_construction(setup):
    prefix = "" if setup.endswith("import partial") else "from functools import partial\n"
    assert not targets(indexed(prefix + setup + "\ndef test_read(): return quote()\n"))


def test_function_defined_before_partial_remains_conservative():
    index = indexed(
        "from functools import partial\nfrom core import price\n"
        "def test_read(): return quote()\nquote = partial(price)\n"
    )
    assert not targets(index)


@pytest.mark.parametrize(
    "extra",
    [
        {"functools.py": "def partial(*args, **kwargs): return other\n"},
        {"core.py": "@decorate\ndef price(): return 1\n"},
        {"core.py": "def price(): return 1\nprice = other\n"},
        {"core.py": "def price(): return 1\nif enabled:\n    def price(): return 2\n"},
    ],
)
def test_shadowed_stdlib_or_ambiguous_target_is_not_resolved(extra):
    assert not targets(
        indexed(
            "from functools import partial\nfrom core import price\n"
            "quote = partial(price)\ndef test_read(): return quote()\n",
            extra,
        )
    )


def test_before_only_partial_call_keeps_deleted_target_evidence():
    test = (
        "from functools import partial\nfrom core import price\n"
        "quote = partial(price)\ndef test_read(): return quote()\n"
    )
    base = {"core.py": "def price(): return 1\n", "test_use.py": test}
    request = AnalysisRequest(
        base=Snapshot(files=base), head=Snapshot(files=base | {"core.py": ""})
    )
    report = analyze(request)
    validate_report(request, report)
    rec = next(r for r in report.recommendations if r.symbol == "test_use.py::test_read")
    edge = next(e for e in report.edges if e.source == rec.symbol and e.kind == "call")
    assert edge.target == "core.py::price" and edge.revision == "before"
    assert rec.path_revision == "before"


@pytest.mark.parametrize("case_id", ["slugify_ascii", "slugify_boundary"])
def test_all_frozen_slugify_misses_are_selected(case_id):
    root = Path(__file__).parents[1] / "corpus/real-v2"
    data = json.loads((root / "cases" / f"{case_id}.json").read_text())
    request = AnalysisRequest.model_validate(data["request"])
    report = analyze(request)
    validate_report(request, report)
    selected = {r.symbol for r in report.recommendations}
    assert set(data["known_discrepancies"]["false_negatives"]) <= selected
    target = "slugify/slugify.py::slugify"
    assert any(
        e.target == target and e.kind == "call" and "partial" in e.after[0].text
        for e in report.edges
        if e.after
    )


@pytest.mark.parametrize("inventory", ["__all__ = ['api']\n", ""])
def test_complete_unique_wildcard_export(inventory):
    index = indexed(
        "from functools import partial\nfrom pkg import api\n"
        "quote = partial(api)\ndef test_read(): return quote()\n",
        {
            "pkg/__init__.py": "from .api import *\nfrom .other import *\n",
            "pkg/api.py": inventory + "def api(): return 1\n",
            "pkg/other.py": "PUBLIC = 1\n",
        },
    )
    assert targets(index) == {"pkg/api.py::api"}


@pytest.mark.parametrize(
    "extra",
    [
        {"pkg/other.py": "def api(): return 2\n"},
        {"pkg/other.py": "from external import *\n"},
        {"pkg/other.py": "__all__ = compute_exports()\n"},
        {"pkg/other.py": "__all__ = []\n__all__.append('api')\n"},
        {"pkg/other.py": "__all__ = []\nalias = __all__\nalias.append('api')\n"},
        {"pkg/other.py": "def __getattr__(name): return value\n"},
        {"pkg/other.py": "globals()['api'] = other\n"},
        {"pkg/__init__.py": "from .api import *\nfrom unknown import *\n"},
        {"pkg/__init__.py": "from .api import *\nif condition:\n    from .other import *\n"},
        {"pkg/__init__.py": "from .api import *\napi = other\n"},
        {"pkg/__init__.py": "from ...api import *\n"},
        {"pkg/api.py": "from .other import api\n", "pkg/other.py": "from .api import api\n"},
    ],
)
def test_wildcard_export_ambiguity_is_never_guessed(extra):
    index = indexed(
        "from functools import partial\nfrom pkg import api\n"
        "quote = partial(api)\ndef test_read(): return quote()\n",
        {
            "pkg/__init__.py": "from .api import *\nfrom .other import *\n",
            "pkg/api.py": "__all__ = ['api']\ndef api(): return 1\n",
            "pkg/other.py": "PUBLIC = 1\n",
        }
        | extra,
    )
    assert not targets(index)


@pytest.mark.parametrize(
    "expression",
    [
        "[quote(x) for x in values]",
        "(lambda x: quote(x))(3)",
        "(quote(x) for x in values)",
    ],
)
def test_unshadowed_partial_in_inner_expression_scope(expression):
    index = indexed(
        "from functools import partial\nfrom core import price\n"
        "quote = partial(price)\ndef test_read(): return " + expression + "\n"
    )
    assert targets(index) == {"core.py::price"}


def test_partial_calls_keep_stable_ids_and_revision_specific_targets():
    source = (
        "from functools import partial\nfrom core import price\nquote = partial(price)\n"
        "def test_read(): return quote()\n"
    )
    first = indexed(source)
    second = indexed("\n\n" + source)
    assert set(first.nodes) == set(second.nodes)
    assert set(first.edges) == set(second.edges)
    request = AnalysisRequest(
        base=Snapshot(files={"core.py": "def price(): return 1\n", "test_use.py": source}),
        head=Snapshot(
            files={
                "core.py": "def price(): return 2\n",
                "test_use.py": source.replace(
                    "quote = partial(price)", "quote = partial(price)\nquote = other"
                ),
            }
        ),
    )
    report = analyze(request)
    validate_report(request, report)
    edge = next(
        e
        for e in report.edges
        if e.source == "test_use.py::test_read"
        and e.target == "core.py::price"
        and e.kind == "call"
    )
    assert edge.revision == "before"


@pytest.mark.parametrize(
    "bindings",
    [
        "quote = partial(price)\nquote = other()",
        "quote = partial(price)\nfrom unknown import partial",
        "if enabled:\n    quote = partial(price)",
        "quote = another = partial(price)",
        "if enabled:\n    from functools import partial\nquote = partial(price)",
    ],
)
def test_unsupported_partial_never_falls_back_to_same_named_definition(bindings):
    index = indexed(
        "from functools import partial\nfrom core import price\n"
        "def quote(): return 1\n" + bindings + "\ndef test_read(): return quote()\n"
    )
    assert not targets(index)
