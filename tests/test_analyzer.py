import pytest

from codeimpact.analyzer import analyze, build_index
from codeimpact.demo import demo_request
from codeimpact.models import AnalysisRequest, Snapshot


def compare(base: dict[str, str], head: dict[str, str]):
    return analyze(AnalysisRequest(base=Snapshot(files=base), head=Snapshot(files=head)))


def test_demo_selects_only_relevant_tests_and_explains_path():
    report = analyze(demo_request())
    assert [r.symbol for r in report.recommendations] == [
        "tests/test_pricing.py::test_discount",
        "tests/test_cart.py::test_checkout",
        "tests/test_api.py::test_create_order",
    ]
    assert report.recommendations[-1].evidence_path == [
        "tests/test_api.py::test_create_order",
        "shop/api.py::create_order",
        "shop/cart.py::checkout",
        "shop/pricing.py::discount",
    ]
    assert "tests/test_health.py::test_health" not in report.impacted
    assert all(r.reason == "Resolved call path" for r in report.recommendations)


def test_whitespace_comments_and_line_moves_do_not_change_semantics():
    report = compare(
        {"a.py": "def f():\n    return 1\n"},
        {"a.py": "# comment\n\ndef f():\n    return 1 # same\n"},
    )
    assert report.changed == []
    assert report.recommendations == []


def test_deleted_function_preserves_old_callers_and_never_recommends_deleted_test():
    base = {
        "a.py": "def f(): return 1",
        "test_a.py": "from a import f\ndef test_a(): assert f() == 1",
    }
    report = compare(base, {"a.py": "", "test_a.py": base["test_a.py"]})
    assert "a.py::f" in report.removed
    assert report.recommendations[0].evidence_path[-1] == "a.py::f"
    report = compare(base, {"a.py": ""})
    assert report.recommendations == []


def test_rename_is_addition_and_removal():
    report = compare({"old.py": "def f(): return 1"}, {"new.py": "def f(): return 1"})
    assert "old.py::f" in report.removed
    assert "new.py::f" in report.changed


@pytest.mark.parametrize(
    "statement,call",
    [
        ("from .core import f as alias", "alias()"),
        ("import pkg.core as other", "other.f()"),
        ("import pkg.core", "pkg.core.f()"),
        ("from pkg import core", "core.f()"),
    ],
)
def test_import_forms_and_src_layout(statement, call):
    index = build_index(
        Snapshot(
            files={
                "src/pkg/core.py": "def f(): return 1",
                "src/pkg/consumer.py": f"{statement}\ndef g(): return {call}",
            }
        )
    )
    assert ("src/pkg/consumer.py::g", "src/pkg/core.py::f", "call") in index.edges


def test_package_init_relative_import():
    index = build_index(
        Snapshot(
            files={
                "pkg/__init__.py": "from .core import f\ndef g(): return f()",
                "pkg/core.py": "def f(): return 1",
            }
        )
    )
    assert ("pkg/__init__.py::g", "pkg/core.py::f", "call") in index.edges


def test_parameter_shadowing_does_not_claim_imported_call():
    index = build_index(
        Snapshot(
            files={
                "a.py": "def f(): return 1",
                "b.py": "from a import f\ndef g(f): return f()",
            }
        )
    )
    assert not any(e.kind == "call" for e in index.edges.values())
    assert any("Unresolved call f" in warning for warning in index.warnings)


def test_assignment_shadowing_does_not_claim_imported_call():
    index = build_index(
        Snapshot(
            files={
                "a.py": "def f(): return 1",
                "b.py": "from a import f\ndef g():\n    f = lambda: 2\n    return f()",
            }
        )
    )
    assert not any(e.kind == "call" for e in index.edges.values())


def test_cycle_terminates_and_deterministic_order():
    base = {"a.py": "def a(): return b()\ndef b(): return a()\ndef test(): return a()"}
    head = {"a.py": "def a(): return b() + 1\ndef b(): return a()\ndef test(): return a()"}
    report = compare(base, head)
    assert "a.py::b" in report.impacted
    again = compare(base, head)
    assert report.model_dump(exclude={"stats"}) == again.model_dump(exclude={"stats"})


def test_syntax_error_is_visible_and_still_propagates_module_impact():
    base = {"a.py": "def f(): return 1", "test_a.py": "from a import f\ndef test_a(): return f()"}
    report = compare(base, base | {"a.py": "def f(:"})
    assert any("Cannot parse a.py" in warning for warning in report.warnings)
    assert report.recommendations


def test_module_constant_change_uses_fallback():
    base = {
        "a.py": "VALUE = 1\ndef f(): return VALUE",
        "test_a.py": "from a import f\ndef test_a(): return f()",
    }
    report = compare(base, base | {"a.py": "VALUE = 2\ndef f(): return VALUE"})
    assert report.changed == ["a.py::<module>"]
    assert report.recommendations[0].reason.startswith("Conservative")


def test_top_level_source_is_never_executed(tmp_path):
    sentinel = tmp_path / "never-created"
    source = f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('executed')"
    compare({}, {"danger.py": source})
    assert not sentinel.exists()


def test_empty_snapshots():
    report = compare({}, {})
    assert not report.nodes and not report.edges and not report.changed


def test_nested_async_and_class_symbols():
    index = build_index(
        Snapshot(
            files={
                "test_a.py": "def outer():\n    def inner(): return 1\n    return inner()\n"
                "class TestThing:\n    async def test_async(self): return outer()\n"
            }
        )
    )
    assert "test_a.py::outer.inner" in index.nodes
    assert ("test_a.py::outer", "test_a.py::outer.inner", "call") in index.edges
    assert index.nodes["test_a.py::TestThing.test_async"].kind == "test"
    # Nested function names are resolved within the enclosing function.
    assert ("test_a.py::TestThing.test_async", "test_a.py::outer", "call") in index.edges


def test_duplicate_module_layout_rejected():
    with pytest.raises(ValueError, match="Ambiguous module"):
        build_index(Snapshot(files={"src/a.py": "", "a.py": ""}))


def test_changed_test_is_recommended_even_without_dependencies():
    report = compare(
        {"test_a.py": "def test_a(): assert True"}, {"test_a.py": "def test_a(): assert False"}
    )
    assert report.recommendations[0].reason == "Test itself changed"
    assert report.recommendations[0].distance == 0


def test_wildcard_and_dynamic_calls_report_uncertainty():
    index = build_index(
        Snapshot(files={"a.py": "from other import *\ndef f(): return factory()()"})
    )
    assert any("Wildcard" in w for w in index.warnings)
    assert any("Dynamic" in w for w in index.warnings)
