"""Module-binding inputs are source strings; never import or execute these fixtures."""

import json
from pathlib import Path

import pytest

from codeimpact.analyzer import analyze, build_index
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot

CORE = "def price():\n    return 1\n"
OTHER = "def price():\n    return 9\n"
CASES = Path(__file__).parents[1] / "corpus/cases"


def index_worker(source):
    return build_index(Snapshot(files={"core.py": CORE, "other.py": OTHER, "worker.py": source}))


def call_targets(index, source="worker.py::read"):
    return {
        edge.target
        for edge in index.edges.values()
        if edge.source == source and edge.kind == "call"
    }


@pytest.mark.parametrize(
    "binding",
    [
        "run = replacement",
        "run = alias = replacement",
        "run, alias = replacements",
        "[alias, *run] = replacements",
        "run: object = replacement",
        "run += replacement",
        "(run := replacement)",
        "del run",
        "def run(): return 42",
        "async def run(): return 42",
        "class run: pass",
        "type run = int",
        "from core import price as run",
        "from other import price as run",
        "import other as run",
        "if enabled:\n    run = replacement",
        "if enabled:\n    from other import price as run",
        "if enabled:\n    def run(): return 42",
        "for run in replacements: pass",
        "while enabled:\n    del run",
        "with manager() as run: pass",
        "try: pass\nexcept Exception as run: pass",
        "try: pass\nexcept* Exception as run: pass",
        "try: pass\nfinally:\n    run = replacement",
        "match value:\n    case {'x': run}: pass",
        "match value:\n    case [*run]: pass",
        "match value:\n    case {**run}: pass",
        "[(run := replacement) for item in values]",
        "((run := replacement) for item in values)",
        "def other(value=(run := replacement)): pass",
        "def other(*, value=(run := replacement)): pass",
        "@(run := replacement)\ndef other(): pass",
        "class Other((run := replacement)): pass",
        "other = lambda value=(run := replacement): value",
        "from other import *",
    ],
)
def test_module_function_alias_competing_bindings_suppress_precise_edges(binding):
    index = index_worker(f"from core import price as run\n{binding}\ndef read(): return run()\n")
    # Also reject a guessed replacement (e.g. the conflicting import or def).
    assert call_targets(index) == set()
    assert ("worker.py::<module>", "core.py::<module>", "import") in index.edges
    assert any("module import binding" in warning for warning in index.warnings)


@pytest.mark.parametrize(
    "binding",
    [
        "dep = replacement",
        "dep: object = replacement",
        "del dep",
        "class dep:\n    def price(): return 42",
        "import other as dep",
        "if enabled:\n    import other as dep",
    ],
)
def test_module_alias_rebinding_suppresses_attribute_call(binding):
    index = index_worker(f"import core as dep\n{binding}\ndef read(): return dep.price()\n")
    assert call_targets(index) == set()


@pytest.mark.parametrize(
    "source",
    [
        "run = replacement\nfrom core import price as run\ndef read(): return run()",
        "from core import price as run\ndef read(): return run()\nrun = replacement",
        "def run(): return 42\nif enabled:\n    from core import price as run\n"
        "def read(): return run()",
        "if enabled:\n    from core import price as run\nelse:\n"
        "    from other import price as run\ndef read(): return run()",
        "from core import price as run, price as run\ndef read(): return run()",
    ],
)
def test_module_binding_ambiguity_is_not_guessed_from_source_order(source):
    assert call_targets(index_worker(source)) == set()


@pytest.mark.parametrize("prefix", ["", "src/"])
@pytest.mark.parametrize(
    "statement,call",
    [
        ("from .core import price as run", "run()"),
        ("from . import core as run", "run.price()"),
        ("import pkg.core as run", "run.price()"),
        ("from pkg.core import price as run", "run()"),
    ],
)
@pytest.mark.parametrize("rebind", [False, True])
def test_module_import_aliases_relative_imports_and_src_layouts(prefix, statement, call, rebind):
    path = f"{prefix}pkg/worker.py"
    source = statement + "\n" + ("run = replacement\n" if rebind else "")
    index = build_index(
        Snapshot(
            files={f"{prefix}pkg/core.py": CORE, path: source + f"def read(): return {call}\n"}
        )
    )
    assert call_targets(index, f"{path}::read") == (
        set() if rebind else {f"{prefix}pkg/core.py::price"}
    )


@pytest.mark.parametrize(
    "separate_binding",
    [
        "def separate(run): return run",
        "def separate():\n    run = replacement\n    return run",
        "def separate():\n    del run",
        "def separate():\n    from other import price as run",
        "class Separate:\n    run = replacement",
        "class Separate:\n    from other import price as run",
        "class Separate:\n    def run(self): return 42",
        "other = lambda run: run",
        "other = lambda: (run := replacement)",
        "values = [run for run in replacements]",
        "values = {run for run in replacements}",
        "values = {run: run for run in replacements}",
        "values = (run for run in replacements)",
        "run: object",
        "run: 'description only'",
        "object.run = replacement",
        "run.description = 'metadata'",
        "slots[run] = replacement",
    ],
)
def test_separate_scopes_and_nonbinding_targets_preserve_module_alias(separate_binding):
    index = index_worker(
        f"from core import price as run\n{separate_binding}\ndef read(): return run()\n"
    )
    assert call_targets(index) == {"core.py::price"}
    assert not any("module import binding" in warning for warning in index.warnings)


def test_attribute_write_does_not_rebind_module_alias_or_other_imports():
    index = index_worker(
        "import core as dep\nfrom core import price as run\n"
        "dep.description = 'metadata'\nrun = replacement\n"
        "def read(): return dep.price()\ndef other(): return run()\n"
    )
    assert call_targets(index) == {"core.py::price"}
    assert call_targets(index, "worker.py::other") == set()


def test_local_import_can_resolve_despite_ambiguous_same_named_module_import():
    index = index_worker(
        "from other import price as run\nrun = replacement\n"
        "def read():\n    from core import price as run\n    return run()\n"
        "def sibling(): return run()\n"
    )
    assert call_targets(index) == {"core.py::price"}
    assert call_targets(index, "worker.py::sibling") == set()


def test_module_rebinding_corpus_removes_unrelated_selection_and_stale_call():
    data = json.loads((CASES / "module_rebinding.json").read_text())
    request = AnalysisRequest.model_validate(data["request"])
    report = analyze(request)
    validate_report(request, report)
    assert {rec.symbol for rec in report.recommendations} == {
        "tests/test_price.py::test_price",
    }
    assert not any(
        edge.source == "worker.py::read" and edge.kind == "call" for edge in report.edges
    )
    assert any(
        edge.source == "worker.py::<module>"
        and edge.target == "core.py::<module>"
        and edge.kind == "import"
        for edge in report.edges
    )  # Selection filtering must not erase graph evidence.
    affected = next(item for item in report.recommendations if item.symbol.endswith("::test_price"))
    assert affected.reason == "Resolved call path"
    assert affected.evidence_path == ["tests/test_price.py::test_price", "core.py::price"]
    assert affected.score == 81


@pytest.mark.parametrize("rebound_revision", ["base", "head"])
def test_rebinding_preserves_valid_other_revision_call_and_stable_ids(rebound_revision):
    plain = "from core import price as run\ndef read(): return run()\n"
    rebound = "from core import price as run\nrun = replacement\ndef read(): return run()\n"
    shared = {
        "core.py": CORE,
        "test_worker.py": "from worker import read\ndef test_read(): return read()\n",
        "test_control.py": "def test_control(): return True\n",
    }
    request = AnalysisRequest(
        base=Snapshot(
            files=shared | {"worker.py": rebound if rebound_revision == "base" else plain}
        ),
        head=Snapshot(
            files=shared
            | {"core.py": CORE.replace("return 1", "return 2")}
            | {"worker.py": rebound if rebound_revision == "head" else plain}
        ),
    )
    report = analyze(request)
    validate_report(request, report)
    edge = next(e for e in report.edges if e.source == "worker.py::read" and e.kind == "call")
    assert edge.revision == ("after" if rebound_revision == "base" else "before")
    assert bool(edge.before) == (rebound_revision == "head")
    assert bool(edge.after) == (rebound_revision == "base")
    assert {rec.symbol for rec in report.recommendations} == {"test_worker.py::test_read"}
    both_plain = analyze(
        AnalysisRequest(base=Snapshot(files=shared | {"worker.py": plain}), head=request.head)
    )
    old_edge = next(
        e for e in both_plain.edges if e.source == "worker.py::read" and e.kind == "call"
    )
    assert edge.id == old_edge.id


def test_rebound_deleted_target_and_removed_test_keep_only_justified_evidence():
    worker = "from core import price as run\nrun = replacement\ndef read(): return run()\n"
    base = {
        "core.py": CORE,
        "worker.py": worker,
        "test_worker.py": "from worker import read\ndef test_read(): return read()\n",
        "test_removed.py": "from core import price\ndef test_removed(): return price()\n",
    }
    head = {path: source for path, source in base.items() if path != "test_removed.py"}
    head["core.py"] = ""
    request = AnalysisRequest(base=Snapshot(files=base), head=Snapshot(files=head))
    report = analyze(request)
    validate_report(request, report)
    assert "core.py::price" in report.removed
    assert report.recommendations == []
    assert not any(e.source == "worker.py::read" and e.kind == "call" for e in report.edges)


def test_module_rebinding_reports_are_deterministic_and_source_is_data(tmp_path):
    marker = tmp_path / "never-created"
    base = {
        "core.py": CORE,
        "worker.py": "from core import price as run\nfrom pathlib import Path\n"
        f"Path({str(marker)!r}).touch()\nrun = replacement\ndef read(): return run()\n",
        "test_worker.py": "from worker import read\ndef test_read(): return read()\n",
    }
    head = base | {"core.py": CORE.replace("return 1", "return 2")}
    request = AnalysisRequest(base=Snapshot(files=base), head=Snapshot(files=head))
    report = analyze(request)
    validate_report(request, report)
    reordered = AnalysisRequest(
        base=Snapshot(files=dict(reversed(list(base.items())))),
        head=Snapshot(files=dict(reversed(list(head.items())))),
    )
    stable = report.model_dump()
    stable["stats"].pop("elapsed_ms")
    for other in (analyze(request), analyze(reordered)):
        validate_report(reordered, other)
        result = other.model_dump()
        result["stats"].pop("elapsed_ms")
        assert result == stable
    assert not marker.exists()
