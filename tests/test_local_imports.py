"""Local-import regression inputs are source strings, never imported or executed."""

import json
from pathlib import Path

import pytest

from codeimpact.analyzer import analyze, build_index
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot

CORE = "def price():\n    return 1\n"
OTHER = "def price():\n    return 9\n"


def index_worker(source, extra=None):
    return build_index(
        Snapshot(files={"core.py": CORE, "other.py": OTHER, "worker.py": source} | (extra or {}))
    )


def call_targets(index, source="worker.py::read"):
    return {
        edge.target
        for edge in index.edges.values()
        if edge.source == source and edge.kind == "call"
    }


@pytest.mark.parametrize("prefix", ["", "src/"])
@pytest.mark.parametrize(
    "statement,call",
    [
        ("from pkg.core import price", "price()"),
        ("from pkg.core import price as quote", "quote()"),
        ("import pkg.core as pricing", "pricing.price()"),
        ("import pkg.core", "pkg.core.price()"),
        ("from pkg import core", "core.price()"),
        ("from .core import price as quote", "quote()"),
        ("from . import core as pricing", "pricing.price()"),
    ],
)
def test_local_import_forms_and_layouts(prefix, statement, call):
    path = f"{prefix}pkg/worker.py"
    index = build_index(
        Snapshot(
            files={
                f"{prefix}pkg/__init__.py": "",
                f"{prefix}pkg/core.py": CORE,
                path: f"def read():\n    {statement}\n    return {call}\n",
            }
        )
    )
    edge = index.edges[(f"{path}::read", f"{prefix}pkg/core.py::price", "call")]
    assert edge.evidence[0].location.line == 3
    assert edge.evidence[0].target_location.path == f"{prefix}pkg/core.py"
    imported = index.edges[(f"{path}::read", f"{prefix}pkg/core.py::<module>", "import")]
    assert imported.evidence[0].location.line == 2
    assert (f"{path}::<module>", f"{prefix}pkg/core.py::<module>", "import") not in index.edges


@pytest.mark.parametrize("path", ["src/pkg/__init__.py", "src/pkg/sub/worker.py"])
def test_local_relative_import_uses_containing_package(path):
    statement = (
        "from .core import price" if path.endswith("__init__.py") else "from ..core import price"
    )
    index = build_index(
        Snapshot(
            files={
                "src/pkg/core.py": CORE,
                path: f"def read():\n    {statement}\n    return price()\n",
            }
        )
    )
    assert (f"{path}::read", "src/pkg/core.py::price", "call") in index.edges


def test_local_import_fixes_authored_corpus_miss_with_exact_evidence():
    data = json.loads((Path(__file__).parents[1] / "corpus/cases/local_import.json").read_text())
    request = AnalysisRequest.model_validate(data["request"])
    report = analyze(request)
    assert [rec.symbol for rec in report.recommendations] == ["tests/test_worker.py::test_read"]
    rec = report.recommendations[0]
    assert rec.evidence_path == [
        "tests/test_worker.py::test_read",
        "worker.py::read",
        "core.py::price",
    ]
    assert (rec.reason, rec.path_revision) == ("Resolved call path", "both")
    validate_report(request, report)


def test_local_import_is_scoped_and_does_not_replace_module_or_sibling_aliases():
    index = index_worker(
        "from other import price\n"
        "def read():\n    from core import price\n    return price()\n"
        "def sibling():\n    return price()\n"
        "def separate():\n    from other import price\n    return price()\n"
    )
    assert call_targets(index) == {"core.py::price"}
    assert call_targets(index, "worker.py::sibling") == {"other.py::price"}
    assert call_targets(index, "worker.py::separate") == {"other.py::price"}
    assert ("worker.py::<module>", "core.py::<module>", "import") not in index.edges


@pytest.mark.parametrize(
    "source,allowed_line",
    [
        (
            "from other import price\ndef read():\n    price()\n"
            "    from core import price\n    return price()\n",
            5,
        ),
        ("from other import price\ndef read():\n    price(); from core import price; price()\n", 3),
    ],
)
def test_calls_before_import_do_not_resolve_to_local_or_global_alias(source, allowed_line):
    index = index_worker(source)
    assert call_targets(index) == {"core.py::price"}
    evidence = index.edges[("worker.py::read", "core.py::price", "call")].evidence
    assert len(evidence) == 1 and evidence[0].location.line == allowed_line
    assert any("Unresolved call price" in warning for warning in index.warnings)


@pytest.mark.parametrize(
    "body",
    [
        "from core import price\nprice = lambda: 42\nreturn price()",
        "price = lambda: 42\nfrom core import price\nreturn price()",
        "from core import price\nreturn price()\nprice = lambda: 42",
        "from core import price\ndel price\nreturn price()",
        "from core import price\nfrom other import price\nreturn price()",
        "from core import price\nfrom core import price\nreturn price()",
        "from core import price\ndef price(): return 42\nreturn price()",
        "from core import price\nclass price: pass\nreturn price()",
        "from core import price\nfor price in []: pass\nreturn price()",
        "from core import price\nwith manager() as price: pass\nreturn price()",
        "from core import price\ntry: pass\nexcept Exception as price: pass\nreturn price()",
        "from core import price\nmatch value:\n    case {'x': price}: pass\nreturn price()",
        "from core import price\n(price := other)\nreturn price()",
        "global price\nfrom core import price\nreturn price()",
        "nonlocal price\nfrom core import price\nreturn price()",
        "if enabled:\n    from core import price\nreturn price()",
        "try:\n    from core import price\nexcept ImportError: pass\nreturn price()",
        "for item in []:\n    from core import price\nreturn price()",
        "from core import price\nif enabled:\n    from other import price\nreturn price()",
    ],
)
def test_ambiguous_local_bindings_never_fall_back_to_same_named_global(body):
    source = "from other import price\ndef read():\n" + "\n".join(
        "    " + line for line in body.splitlines()
    )
    assert not (call_targets(index_worker(source)) & {"core.py::price", "other.py::price"})


@pytest.mark.parametrize("args", ["price", "price, /", "*, price", "*price", "**price"])
def test_parameter_collision_conservatively_suppresses_local_alias(args):
    index = index_worker(f"def read({args}):\n    from core import price\n    return price()\n")
    assert not call_targets(index)


@pytest.mark.parametrize(
    "mutation", ["pricing.price = lambda: 42", "del pricing.price", "pricing = other"]
)
def test_local_module_alias_mutation_does_not_claim_original_function(mutation):
    index = index_worker(
        f"def read():\n    import core as pricing\n    {mutation}\n    return pricing.price()\n"
    )
    assert "core.py::price" not in call_targets(index)


def test_nested_bindings_do_not_contaminate_outer_local_imports():
    index = index_worker(
        "def read():\n    from core import price\n"
        "    def inner():\n        price = lambda: 42\n        return price()\n"
        "    return price()\n"
    )
    assert call_targets(index) == {"core.py::price"}
    assert not call_targets(index, "worker.py::read.inner")


def test_nested_nonlocal_assignment_prevents_precise_outer_import_resolution():
    index = index_worker(
        "def read():\n    from core import price\n"
        "    def change():\n        nonlocal price\n        price = lambda: 42\n"
        "    change()\n    return price()\n"
    )
    assert "core.py::price" not in call_targets(index)


@pytest.mark.parametrize(
    "definition",
    [
        "def inner(value=(price := replacement)): pass",
        "def inner(*, value=(price := replacement)): pass",
        "@(price := replacement)\ndef inner(): pass",
        "class Inner((price := replacement)): pass",
        "callback = lambda value=(price := replacement): value",
    ],
)
def test_nested_definition_headers_can_rebind_the_enclosing_import(definition):
    # Defaults, decorators and class bases run in the enclosing scope, unlike
    # ordinary stores inside the nested function/class/lambda body.
    body = "\n".join("    " + line for line in definition.splitlines())
    index = index_worker(
        "def read(replacement):\n    from core import price\n" + body + "\n    return price()\n"
    )
    assert "core.py::price" not in call_targets(index)


def test_enclosing_local_import_does_not_create_false_global_closure_edge():
    index = index_worker(
        "from other import price\ndef read():\n    from core import price\n"
        "    def inner():\n        return price()\n    return inner()\n"
    )
    # Closure propagation is deliberately outside this bounded resolver.
    assert not call_targets(index, "worker.py::read.inner")


def test_nested_functions_and_async_methods_resolve_their_own_local_aliases():
    index = index_worker(
        "def outer():\n    from other import price\n"
        "    def inner():\n        from core import price\n        return price()\n"
        "    return inner()\n"
        "class Reader:\n    async def read(self):\n"
        "        from core import price\n        return price()\n"
    )
    assert call_targets(index, "worker.py::outer.inner") == {"core.py::price"}
    assert call_targets(index, "worker.py::Reader.read") == {"core.py::price"}


@pytest.mark.parametrize(
    "expression",
    [
        "(lambda price: price())(lambda: 42)",
        "[price() for price in callbacks]",
        "(price() for price in callbacks)",
    ],
)
def test_nested_expression_scopes_do_not_reuse_a_local_alias(expression):
    index = index_worker(f"def read():\n    from core import price\n    return {expression}\n")
    assert not call_targets(index)


def test_overdeep_relative_and_wildcard_local_imports_remain_unresolved():
    index = index_worker(
        "from other import price\n"
        "def read():\n    from ..core import price\n    return price()\n"
        "def star():\n    from core import price\n    from other import *\n    return price()\n"
    )
    assert not call_targets(index)
    assert not call_targets(index, "worker.py::star")
    assert any("Wildcard" in warning for warning in index.warnings)


def test_local_import_module_fallback_does_not_select_sibling_test():
    base = {
        "core.py": "VALUE = 1\n",
        "worker.py": "def read():\n    import core\n    return core.VALUE\n"
        "\ndef healthy():\n    return True\n",
        "test_worker.py": "from worker import read, healthy\n"
        "def test_read(): return read()\ndef test_healthy(): return healthy()\n",
    }
    request = AnalysisRequest(
        base=Snapshot(files=base), head=Snapshot(files=base | {"core.py": "VALUE = 2\n"})
    )
    report = analyze(request)
    assert [rec.symbol for rec in report.recommendations] == ["test_worker.py::test_read"]
    rec = report.recommendations[0]
    assert rec.evidence_path == [
        "test_worker.py::test_read",
        "worker.py::read",
        "core.py::<module>",
    ]
    assert rec.reason == "Conservative module/import dependency"
    validate_report(request, report)


def test_local_import_deleted_dependency_and_line_movement_keep_revision_evidence():
    base = {
        "core.py": CORE,
        "worker.py": "def read():\n    from core import price\n    return price()\n",
        "test_worker.py": "from worker import read\ndef test_read(): return read()\n",
        "test_removed.py": "from worker import read\ndef test_removed(): return read()\n",
    }
    head = {path: source for path, source in base.items() if path != "test_removed.py"}
    head |= {"core.py": "", "worker.py": "# moved\n\n" + base["worker.py"]}
    request = AnalysisRequest(base=Snapshot(files=base), head=Snapshot(files=head))
    report = analyze(request)
    assert [rec.symbol for rec in report.recommendations] == ["test_worker.py::test_read"]
    assert report.recommendations[0].path_revision == "before"
    call = next(
        edge for edge in report.edges if edge.source == "worker.py::read" and edge.kind == "call"
    )
    assert call.before[0].location.line == 3 and call.after == []
    imported = next(
        edge for edge in report.edges if edge.source == "worker.py::read" and edge.kind == "import"
    )
    assert imported.before[0].location.line == 2 and imported.after[0].location.line == 4
    validate_report(request, report)
    reordered = AnalysisRequest(
        base=Snapshot(files=dict(reversed(list(base.items())))),
        head=Snapshot(files=dict(reversed(list(head.items())))),
    )
    assert report.model_dump(exclude={"stats"}) == analyze(reordered).model_dump(exclude={"stats"})


def test_local_import_source_is_never_executed(tmp_path):
    sentinel = tmp_path / "never-created"
    source = f"from pathlib import Path\nPath({str(sentinel)!r}).touch()\n" + CORE
    index = index_worker(
        "def read():\n    from core import price\n    return price()\n", {"core.py": source}
    )
    assert call_targets(index) == {"core.py::price"}
    assert not sentinel.exists()


def test_local_import_cycle_retains_finite_deterministic_paths():
    base = {
        "first.py": "def first(n):\n    from second import second\n"
        "    return second(n - 1) if n else 1\n",
        "second.py": "def second(n):\n    from first import first\n"
        "    return first(n - 1) if n else 1\n",
        "test_cycle.py": "from second import second\ndef test_cycle(): return second(1)\n",
    }
    request = AnalysisRequest(
        base=Snapshot(files=base),
        head=Snapshot(files=base | {"first.py": base["first.py"].replace("else 1", "else 2")}),
    )
    report = analyze(request)
    assert report.recommendations[0].evidence_path == [
        "test_cycle.py::test_cycle",
        "second.py::second",
        "first.py::first",
    ]
    assert {
        ("first.py::first", "second.py::second"),
        ("second.py::second", "first.py::first"),
    } <= {(edge.source, edge.target) for edge in report.edges if edge.kind == "call"}
    validate_report(request, report)
    assert report.model_dump(exclude={"stats"}) == analyze(request).model_dump(exclude={"stats"})
