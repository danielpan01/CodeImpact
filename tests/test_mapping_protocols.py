"""Bounded mapping fallback keeps evidence and unknown receiver cases conservative."""

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot

CORE = """class Edited:
    def __setitem__(self, key, value): self.value = 1
    def __delitem__(self, key): self.value = 1
    def __getitem__(self, key): return 1
class Other:
    def __setitem__(self, key, value): self.value = value
    def __delitem__(self, key): pass
    def __getitem__(self, key): return 0
"""


def compare(tests, before=CORE, after=None, extra=None):
    files = {"app.py": before, "test_app.py": tests, **(extra or {})}
    request = AnalysisRequest(
        base=Snapshot(files=files),
        head=Snapshot(
            files=files | {"app.py": after or before.replace("self.value = 1", "self.value = 2")}
        ),
    )
    report = analyze(request)
    validate_report(request, report)
    return report


def selected(report):
    return {r.symbol.split("::")[1] for r in report.recommendations}


@pytest.mark.parametrize("operation", ["obj[0] = 3", "del obj[0]", "obj[0] += 3", "return obj[0]"])
def test_known_mapping_receiver_excludes_sibling_class(operation):
    tests = (
        "from app import Edited, Other\n"
        f"def test_edited():\n    obj = Edited()\n    {operation}\n"
        f"def test_other():\n    obj = Other()\n    {operation}\n"
    )
    report = compare(tests)
    assert selected(report) == {"test_edited"}
    assert report.recommendations[0].reason.startswith("Conservative")
    assert report.recommendations[0].evidence_path[-1] == "app.py::<module>"
    assert "app.py::<module>" in report.changed


@pytest.mark.parametrize(
    "operation", ["obj[0] = 3", "del obj[0]", "obj[0] += 3", "return obj[0]", "obj.update({0: 3})"]
)
def test_unknown_receiver_keeps_fallback(operation):
    report = compare(f"from app import Edited\ndef test_unknown(obj):\n    {operation}\n")
    assert selected(report) == {"test_unknown"}


def test_alias_factory_and_inherited_mapping_receivers():
    core = (
        CORE
        + "class Child(Edited): pass\nclass Control(Other): pass\ndef factory(): return Control()\n"
    )
    tests = (
        "from app import Child, factory\n"
        "def test_child():\n    obj=Child()\n    obj[0]=1\n"
        "def test_control():\n    obj=factory()\n    alias=obj\n    alias[0]=1\n"
    )
    assert selected(compare(tests, core)) == {"test_child"}


@pytest.mark.parametrize(
    "binding", ["obj = unknown()", "if flag: obj = Edited()", "obj = values[0]"]
)
def test_uncertain_rebinding_and_container_elements_retain_fallback(binding):
    tests = (
        "from app import Edited, Other\ndef test_keep(values, flag):\n"
        f"    obj=Other()\n    {binding}\n    obj[0]=1\n"
    )
    assert selected(compare(tests)) == {"test_keep"}


@pytest.mark.parametrize(
    "custom",
    [
        "@decorate\nclass Other:",
        "class Other(metaclass=Meta):",
        "class Other(External):",
        "class Other:\n    def __new__(cls): return unknown()",
    ],
)
def test_custom_or_external_receiver_does_not_prove_exclusion(custom):
    core = CORE.replace("class Other:", custom)
    tests = "from app import Other\ndef test_keep():\n    obj=Other()\n    obj[0]=3\n"
    assert selected(compare(tests, core)) == {"test_keep"}


def test_shared_mixin_is_not_specialized_to_one_subclass():
    core = CORE + "class Parent:\n    Cache = Other\nclass A(Parent): Cache = Edited\n"
    tests = (
        "from app import Parent\nclass TestShared(Parent):\n"
        "    def test_keep(self):\n        obj=self.Cache()\n        obj[0]=3\n"
    )
    assert selected(compare(tests, core)) == {"TestShared.test_keep"}


def test_nested_callback_mapping_receiver_stays_uncertain():
    tests = (
        "from app import Other\ndef test_keep():\n"
        "    def callback(obj): obj[0]=1\n    dispatch(callback)\n"
    )
    assert selected(compare(tests)) == {"test_keep"}


def test_old_revision_reference_and_deleted_methods_keep_evidence():
    before = CORE
    after = CORE.replace("    def __delitem__(self, key): self.value = 1\n", "")
    report = compare(
        "from app import Edited\ndef test_keep():\n    obj=Edited()\n    del obj[0]\n",
        before,
        after,
    )
    assert selected(report) == {"test_keep"}
    assert "app.py::Edited.__delitem__" in report.removed


@pytest.mark.parametrize("extra", ["SETTING = 2\n", "class Added: pass\n"])
def test_initialization_or_class_addition_does_not_enter_body_only_filter(extra):
    report = compare(
        "from app import Other\ndef test_keep(): return Other()\n",
        after=CORE.replace("self.value = 1", "self.value = 2") + extra,
    )
    assert selected(report) == {"test_keep"}


def test_unknown_non_mapping_protocol_keeps_existing_broad_fallback():
    core = CORE + "class Numeric:\n    def __add__(self, other): return 1\n"
    report = compare(
        "from app import Other\ndef test_keep(): return Other()\n",
        core,
        core.replace("return 1", "return 2"),
    )
    assert selected(report) == {"test_keep"}


def test_changed_tests_are_not_excluded_by_mapping_filter():
    request = AnalysisRequest(
        base=Snapshot(
            files={
                "app.py": CORE,
                "test_app.py": "from app import Other\ndef test_changed(): return 1\n",
            }
        ),
        head=Snapshot(
            files={
                "app.py": CORE.replace("self.value = 1", "self.value = 2"),
                "test_app.py": "from app import Other\ndef test_changed(): return 2\n",
            }
        ),
    )
    report = analyze(request)
    validate_report(request, report)
    assert selected(report) == {"test_changed"}
    assert report.recommendations[0].reason == "Test itself changed"


MAPPING_CORE = """import collections
import collections.abc
class Base(collections.abc.MutableMapping):
    def __init__(self): self.__data = collections.OrderedDict()
    def __getitem__(self, key): return self.__data[key]
    def __setitem__(self, key, value): self.__data[key] = value
    def __delitem__(self, key): del self.__data[key]
    def __iter__(self): return iter(self.__data)
    def __len__(self): return len(self.__data)
class Edited(Base):
    def __setitem__(self, key, value): self.value = 1
class Other(Base): pass
"""


def test_generic_abc_mapping_keeps_class_identity_and_private_base_storage():
    tests = (
        "from app import Edited, Other\n"
        "def test_edited():\n    obj=Edited[int, int]()\n    obj[0]=1\n"
        "def test_control():\n    obj=Other[int, int]()\n    obj[0]=1\n"
    )
    assert selected(compare(tests, MAPPING_CORE)) == {"test_edited"}


@pytest.mark.parametrize(
    "edit",
    [
        "collections = replacement\n",
        "if flag:\n    import fake as collections\n",
        "from unknown import *\n",
        "collections.abc.MutableMapping = replacement\n",
    ],
)
def test_stdlib_shape_rebinding_keeps_uncertainty(edit):
    core = MAPPING_CORE.replace("class Base", edit + "class Base")
    tests = "from app import Other\ndef test_keep():\n    obj=Other[int, int]()\n    obj[0]=1\n"
    assert selected(compare(tests, core)) == {"test_keep"}


def test_snapshot_module_named_collections_is_not_the_stdlib():
    tests = "from app import Other\ndef test_keep():\n    obj=Other[int, int]()\n    obj[0]=1\n"
    assert selected(compare(tests, MAPPING_CORE, extra={"collections.py": "abc=unknown()\n"})) == {
        "test_keep"
    }


def test_custom_generic_subscription_is_not_treated_as_the_original_class():
    core = MAPPING_CORE.replace(
        "class Other(Base): pass",
        "class Other(Base):\n    def __class_getitem__(cls, key): return Edited\n",
    )
    tests = "from app import Other\ndef test_keep():\n    obj=Other[int, int]()\n    obj[0]=1\n"
    assert selected(compare(tests, core)) == {"test_keep"}


@pytest.mark.parametrize(
    "operation", ["return 0 in obj", "return list(obj)", "return next(obj)", "for key in obj: pass"]
)
def test_unknown_mapping_use_through_helpers_is_retained(operation):
    tests = (
        "from app import Other\n"
        f"def helper(obj):\n    {operation}\n"
        "def test_keep(): return helper(unknown())\n"
    )
    assert selected(compare(tests)) == {"test_keep"}


def test_before_receiver_is_considered_when_head_uses_only_other_mapping():
    before = {
        "app.py": CORE,
        "test_app.py": (
            "from app import factory\ndef test_keep():\n    obj=factory()\n    obj[0]=1\n"
        ),
    }
    before["app.py"] += "def factory(): return Edited()\n"
    # A mixed factory/body edit must retain the existing aggregate fallback.
    request = AnalysisRequest(
        base=Snapshot(files=before),
        head=Snapshot(
            files=before
            | {
                "app.py": before["app.py"]
                .replace("self.value = 1", "self.value = 2")
                .replace("return Edited()", "return Other()")
            }
        ),
    )
    report = analyze(request)
    validate_report(request, report)
    assert selected(report) == {"test_keep"}


def test_reference_budget_exhaustion_retains_selection(monkeypatch):
    from codeimpact import mapping_protocols

    monkeypatch.setattr(mapping_protocols, "MAX_VISITS", 0)
    assert selected(compare("from app import Other\ndef test_keep(): return Other()\n")) == {
        "test_keep"
    }


def test_receiver_recursion_does_not_remove_recommendations(monkeypatch):
    from codeimpact import mapping_protocols

    def exhausted(*args):
        raise RecursionError("bounded query")

    monkeypatch.setattr(mapping_protocols.MappingQuery, "depends", exhausted)
    assert selected(compare("from app import Other\ndef test_keep(): return Other()\n")) == {
        "test_keep"
    }


def test_report_graph_ids_directions_and_source_are_not_rewritten():
    from codeimpact.analyzer import build_index, merge_edges

    tests = "from app import Edited\ndef test_keep():\n    obj=Edited()\n    obj[0]=1\n"
    request = AnalysisRequest(
        base=Snapshot(files={"app.py": CORE, "test_app.py": tests}),
        head=Snapshot(
            files={"app.py": CORE.replace("self.value = 1", "self.value = 2"), "test_app.py": tests}
        ),
    )
    report = analyze(request)
    before, after = build_index(request.base), build_index(request.head)
    expected = merge_edges(before, after)
    assert {e.id: e.model_dump() for e in report.edges} == {
        e.id: e.model_dump() for e in expected.values()
    }
    assert {n.id for n in report.nodes} == before.nodes.keys() | after.nodes.keys()
    validate_report(request, report)


@pytest.mark.parametrize(
    "name", ["__new__", "__getattribute__", "__setattr__", "__init_subclass__"]
)
def test_assigned_customization_is_not_a_plain_receiver(name):
    core = CORE.replace("class Other:", f"class Other:\n    {name} = hook")
    tests = "from app import Other\ndef test_keep():\n    obj=Other()\n    obj[0]=1\n"
    assert selected(compare(tests, core)) == {"test_keep"}


def test_assigned_generic_hook_is_unknown():
    core = MAPPING_CORE.replace(
        "class Other(Base): pass", "class Other(Base):\n    __class_getitem__ = hook\n"
    )
    tests = "from app import Other\ndef test_keep():\n    obj=Other[int]()\n    obj[0]=1\n"
    assert selected(compare(tests, core)) == {"test_keep"}


def test_global_rebinding_does_not_preserve_stdlib_identity():
    core = MAPPING_CORE + "def rebind():\n    global collections\n    collections = unknown()\n"
    tests = "from app import Other\ndef test_keep():\n    obj=Other[int]()\n    obj[0]=1\n"
    assert selected(compare(tests, core)) == {"test_keep"}


@pytest.mark.parametrize(
    "statement", ["self.__data += unknown()", "del self.__data", "self.__data: object = unknown()"]
)
def test_private_storage_unknown_writes_retain_selection(statement):
    core = MAPPING_CORE.replace(
        "    def __getitem__", f"    def reset(self): {statement}\n    def __getitem__"
    )
    tests = "from app import Other\ndef test_keep():\n    obj=Other[int]()\n    obj[0]=1\n"
    assert selected(compare(tests, core)) == {"test_keep"}


def test_mangled_private_storage_write_is_not_ignored():
    core = MAPPING_CORE + "def mutate(obj): obj._Base__data = unknown()\n"
    tests = "from app import Other\ndef test_keep():\n    obj=Other[int]()\n    obj[0]=1\n"
    assert selected(compare(tests, core)) == {"test_keep"}


def test_duplicate_definition_declines_filter():
    core = CORE + "class Edited:\n    def __setitem__(self, key, value): self.value = 1\n"
    tests = "from app import Other\ndef test_keep(): return Other()\n"
    assert selected(compare(tests, core)) == {"test_keep"}


def test_unknown_iterator_result_retains_selection():
    tests = "from app import Other\ndef test_keep(): return next(iter(Other[int]()))\n"
    assert selected(compare(tests, MAPPING_CORE)) == {"test_keep"}


@pytest.mark.parametrize("inherited", [False, True])
def test_class_stored_callable_keeps_fallback(inherited):
    core = CORE + "class Stored:\n    callback = hook\n"
    if inherited:
        core += "class Child(Stored): pass\n"
    cls = "Child" if inherited else "Stored"
    tests = f"from app import {cls}\ndef test_keep():\n    obj={cls}()\n    obj.callback()\n"
    assert selected(compare(tests, core)) == {"test_keep"}


def test_assigned_protocol_method_keeps_fallback():
    core = CORE + "Other.__getitem__ = Edited.__getitem__\n"
    tests = "from app import Other\ndef test_keep(): return Other()[0]\n"
    assert selected(compare(tests, core)) == {"test_keep"}


@pytest.mark.parametrize(
    "initialization",
    ["VALUE = Edited()[0]", "VALUE = helper()", "class Config:\n    VALUE = helper()"],
)
def test_unchanged_initialization_can_still_observe_edited_bodies(initialization):
    core = CORE + "def helper(): return Edited()[0]\n" + initialization + "\n"
    tests = "from app import Other\ndef test_keep(): return Other()\n"
    assert selected(compare(tests, core)) == {"test_keep"}


@pytest.mark.parametrize(
    "initialization",
    [
        "def helper(value: Edited()[0]): pass",
        "def helper() -> Edited()[0]: pass",
        "VALUE = imported_mapping[0]",
        "VALUE = 0 in imported_mapping",
        "@decorate\ndef helper(): pass",
        "@decorate\nclass Helper: pass",
    ],
)
def test_implicit_initialization_and_annotations_keep_fallback(initialization):
    tests = "from app import Other\ndef test_keep(): return Other()\n"
    assert selected(compare(tests, CORE + initialization + "\n")) == {"test_keep"}


def test_plain_stdlib_ordering_decorator_does_not_invoke_comparison_body():
    core = (
        "import functools as ft\n"
        + CORE
        + "@ft.total_ordering\nclass Ordered:\n    def __lt__(self, other): return False\n"
    )
    tests = "from app import Other\ndef test_control(): return Other()\n"
    assert selected(compare(tests, core)) == set()


@pytest.mark.parametrize("mutation", ["functools = unknown", "functools.total_ordering = unknown"])
def test_mutated_ordering_decorator_keeps_initialization_fallback(mutation):
    core = (
        "import functools\n"
        + CORE
        + mutation
        + "\n@functools.total_ordering\nclass Ordered: pass\n"
    )
    tests = "from app import Other\ndef test_keep(): return Other()\n"
    assert selected(compare(tests, core)) == {"test_keep"}


def test_snapshot_ordering_decorator_is_not_trusted_stdlib():
    core = "import functools\n" + CORE + "@functools.total_ordering\nclass Ordered: pass\n"
    tests = "from app import Other\ndef test_keep(): return Other()\n"
    assert selected(
        compare(tests, core, extra={"functools.py": "def total_ordering(cls): return cls\n"})
    ) == {"test_keep"}
