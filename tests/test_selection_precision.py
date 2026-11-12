"""Selection must distinguish declaration containers from executed dependencies."""

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot


def compare(files, path, replacement):
    request = AnalysisRequest(
        base=Snapshot(files=files), head=Snapshot(files=files | {path: replacement})
    )
    report = analyze(request)
    validate_report(request, report)
    return report


def selected(report):
    return {r.symbol.split("::")[1] for r in report.recommendations}


def test_sibling_function_edit_does_not_select_unrelated_imports():
    src = "def price(): return 1\ndef healthy(): return True\n"
    files = {
        "app.py": src,
        "test_app.py": (
            "from app import price, healthy\n"
            "def test_price(): return price()\n"
            "def test_health(): return healthy()\n"
            ""
        ),
    }
    report = compare(files, "app.py", src.replace("return 1", "return 2"))
    assert selected(report) == {"test_price"}
    assert "app.py::<module>" in report.changed  # Still visible in Changes.


@pytest.mark.parametrize("edit", ["modify", "add", "delete"])
def test_test_body_change_does_not_select_unchanged_sibling(edit):
    before = "def test_one(): assert 1\ndef test_two(): assert 2\n"
    after = {
        "modify": before.replace("assert 1", "assert 3"),
        "add": before + "def test_three(): assert 3\n",
        "delete": before.replace("def test_one(): assert 1\n", ""),
    }[edit]
    report = compare({"test_app.py": before}, "test_app.py", after)
    assert (
        selected(report) == {"modify": {"test_one"}, "add": {"test_three"}, "delete": set()}[edit]
    )


@pytest.mark.parametrize("invocation", ["Thing().price()", "obj.price()"])
@pytest.mark.parametrize("edit", ["modify", "add", "delete"])
def test_method_edit_does_not_mark_every_constructor_user_affected(invocation, edit):
    method = "    def price(self): return 1\n"
    before = "class Thing:\n" + method + "    def healthy(self): return True\n"
    after = before.replace("return 1", "return 2")
    if edit == "add":
        before = before.replace(method, "")
    if edit == "delete":
        after = before.replace(method, "")
    tests = (
        f"from app import Thing\n"
        f"def test_price():\n"
        f"    obj=Thing()\n"
        f"    return {invocation}\n"
        f"def test_health(): return Thing().healthy()\n"
        f"def test_construct(): return Thing()\n"
        f""
    )
    report = compare({"app.py": before, "test_app.py": tests}, "app.py", after)
    assert selected(report) == {"test_price"}
    assert "app.py::Thing" in report.changed
    rec = report.recommendations[0]
    assert rec.reason == "Conservative module/import dependency"
    assert rec.evidence_path[-1] == "app.py::<module>"


def test_repr_and_str_are_separate_protocols():
    src = (
        'class Work:\n    def __repr__(self): return "old"\n    def __str__(self): return "same"\n'
    )
    tests = (
        "from app import Work\n"
        "def test_repr(): return repr(Work())\n"
        "def test_str(): return str(Work())\n"
        "def test_construct(): return Work()\n"
        ""
    )
    assert selected(
        compare({"app.py": src, "test_app.py": tests}, "app.py", src.replace("old", "new"))
    ) == {"test_repr"}


def test_factory_fluent_properties_do_not_confuse_same_named_field():
    src = (
        "class Job:\n"
        "    def __init__(self): self.next_run=1\n"
        "    @property\n"
        "    def minutes(self): return self\n"
        "    def do(self): return self\n"
        "class Scheduler:\n"
        "    @property\n"
        "    def next_run(self): return 2\n"
        "    def every(self): return Job()\n"
        "scheduler=Scheduler()\n"
        "def every(): return scheduler.every()\n"
        ""
    )
    tests = (
        "from app import every, scheduler\n"
        "def test_job(): return every().minutes.do().next_run\n"
        "def test_scheduler(): return scheduler.next_run\n"
        ""
    )
    report = compare(
        {"app.py": src, "test_app.py": tests}, "app.py", src.replace("return 2", "return 3")
    )
    assert selected(report) == {"test_scheduler"}


def test_unknown_receiver_retains_conservative_method_reference():
    src = "class Service:\n    def read(self): return 1\n"
    tests = (
        "from app import Service\n"
        "def test_read(service): return service.read()\n"
        "def test_other(service): return service.other()\n"
        ""
    )
    report = compare(
        {"app.py": src, "test_app.py": tests}, "app.py", src.replace("return 1", "return 2")
    )
    assert selected(report) == {"test_read"}
    assert report.recommendations[0].reason.startswith("Conservative")


def test_conditional_definition_retains_uncertainty_without_sibling_overselection():
    src = "if enabled:\n    def price(): return 1\ndef healthy(): return True\n"
    tests = (
        "from app import price, healthy\n"
        "def test_price(): return price()\n"
        "def test_health(): return healthy()\n"
        ""
    )
    report = compare(
        {"app.py": src, "test_app.py": tests}, "app.py", src.replace("return 1", "return 2")
    )
    assert selected(report) == {"test_price"}
    assert report.recommendations[0].reason.startswith("Conservative")


def test_inherited_member_keeps_affected_control_separate():
    src = (
        "class Base:\n"
        "    def price(self): return 1\n"
        "    def healthy(self): return True\n"
        "class Child(Base): pass\n"
        ""
    )
    tests = (
        "from app import Child\n"
        "def test_price(): return Child().price()\n"
        "def test_health(): return Child().healthy()\n"
        ""
    )
    assert selected(
        compare(
            {"app.py": src, "test_app.py": tests}, "app.py", src.replace("return 1", "return 2")
        )
    ) == {"test_price"}


@pytest.mark.parametrize(
    "change",
    [
        ("VALUE=1\ndef read(): return VALUE\n", "VALUE=2\ndef read(): return VALUE\n"),
        ("register(1)\ndef read(): return 1\n", "register(2)\ndef read(): return 1\n"),
        ("def read(x=register(1)): return x\n", "def read(x=register(2)): return x\n"),
        ("@decorate(1)\ndef read(): return 1\n", "@decorate(2)\ndef read(): return 1\n"),
        (
            "class C:\n    VALUE=1\ndef read(): return C.VALUE\n",
            "class C:\n    VALUE=2\ndef read(): return C.VALUE\n",
        ),
        ("def read(): return 1\n", "def read(:\n"),
    ],
)
def test_real_initialization_or_parse_changes_keep_fallback(change):
    tests = "from app import read\ndef test_read(): return read()\n"
    assert selected(compare({"app.py": change[0], "test_app.py": tests}, "app.py", change[1])) == {
        "test_read"
    }


def test_constructor_edit_still_selects_constructor_users():
    src = "class C:\n    def __init__(self): self.value=1\n"
    tests = "from app import C\ndef test_construct(): return C()\n"
    assert selected(
        compare({"app.py": src, "test_app.py": tests}, "app.py", src.replace("value=1", "value=2"))
    ) == {"test_construct"}


def test_passed_callable_reference_still_has_conservative_evidence():
    src = "def price(): return 1\n"
    tests = "from app import price\ndef test_callback(): return external(price)\n"
    report = compare(
        {"app.py": src, "test_app.py": tests}, "app.py", src.replace("return 1", "return 2")
    )
    assert selected(report) == {"test_callback"}


def test_unknown_custom_new_cannot_prove_receiver_independence():
    src = (
        "class A:\n"
        "    def read(self): return 1\n"
        "class B:\n"
        "    def __new__(cls): return choose_runtime_type()\n"
        "    def read(self): return 7\n"
        ""
    )
    tests = "from app import B\ndef test_read(): return B().read()\n"
    report = compare(
        {"app.py": src, "test_app.py": tests}, "app.py", src.replace("return 1", "return 2")
    )
    assert selected(report) == {"test_read"}
    assert report.recommendations[0].reason.startswith("Conservative")


def test_property_decorator_to_explicit_binding_does_not_select_all_methods():
    before = (
        "class C:\n"
        "    @property\n"
        "    def read(self): return 1\n"
        "    def healthy(self): return True\n"
        ""
    )
    after = (
        "class C:\n"
        "    def get_read(self): return 2\n"
        "    read=property(get_read)\n"
        "    def healthy(self): return True\n"
        ""
    )
    tests = (
        "from app import C\n"
        "def test_read(): return C().read\n"
        "def test_health(): return C().healthy()\n"
        ""
    )
    assert selected(compare({"app.py": before, "test_app.py": tests}, "app.py", after)) == {
        "test_read"
    }


def test_rebinding_property_getter_is_not_hidden():
    before = (
        "class C:\n"
        "    def one(self): return 1\n"
        "    def two(self): return 2\n"
        "    read=property(one)\n"
        ""
    )
    tests = (
        "from app import C\ndef test_read(): return C().read\ndef test_construct(): return C()\n"
    )
    assert selected(
        compare(
            {"app.py": before, "test_app.py": tests},
            "app.py",
            before.replace("property(one)", "property(two)"),
        )
    ) == {"test_read"}


def test_global_callable_alias_does_not_lose_a_dependency():
    src = "def price(): return 1\n"
    wrapper = "from app import price\nalias=price\ndef read(): return alias()\n"
    tests = "from wrapper import read\ndef test_read(): return read()\n"
    assert selected(
        compare(
            {"app.py": src, "wrapper.py": wrapper, "test_app.py": tests},
            "app.py",
            src.replace("return 1", "return 2"),
        )
    ) == {"test_read"}


def test_module_attribute_callback_reference_is_retained():
    src = "def price(): return 1\n"
    tests = "import app\ndef test_callback(): return consume(app.price)\n"
    assert selected(
        compare(
            {"app.py": src, "test_app.py": tests}, "app.py", src.replace("return 1", "return 2")
        )
    ) == {"test_callback"}


def test_repeated_same_type_bindings_keep_field_distinct_from_property():
    src = (
        "class Job:\n"
        "    next_run=1\n"
        "class Queue:\n"
        "    @property\n"
        "    def next_run(self): return 1\n"
        ""
    )
    tests = (
        "from app import Job, Queue\n"
        "def test_job():\n"
        "    job=Job()\n"
        "    a=job.next_run\n"
        "    job=Job()\n"
        "    return job.next_run\n"
        "def test_queue(): return Queue().next_run\n"
        ""
    )
    assert selected(
        compare(
            {"app.py": src, "test_app.py": tests}, "app.py", src.replace("return 1", "return 2")
        )
    ) == {"test_queue"}


def test_parameter_with_conditional_assignment_cannot_prove_receiver_type():
    src = "class A:\n    def read(self): return 1\nclass B:\n    def read(self): return 7\n"
    tests = (
        "from app import A, B\ndef test_read(obj):\n    if flag: obj=B()\n    return obj.read()\n"
    )
    assert selected(
        compare(
            {"app.py": src, "test_app.py": tests}, "app.py", src.replace("return 1", "return 2")
        )
    ) == {"test_read"}


def test_external_field_write_invalidates_field_type_assumption():
    src = (
        "class A:\n"
        '    def __repr__(self): return "old"\n'
        "class Holder:\n"
        "    def __init__(self): self.value=None\n"
        "    def show(self): return repr(self.value)\n"
        ""
    )
    tests = (
        "from app import A, Holder\n"
        "def test_show():\n"
        "    obj=Holder()\n"
        "    obj.value=A()\n"
        "    return obj.show()\n"
        ""
    )
    assert selected(
        compare({"app.py": src, "test_app.py": tests}, "app.py", src.replace("old", "new"))
    ) == {"test_show"}


def test_unknown_external_base_does_not_prove_constructor_return_type():
    src = (
        "from external import Factory\n"
        "class A:\n"
        "    def read(self): return 1\n"
        "class B(Factory):\n"
        "    def read(self): return 7\n"
        ""
    )
    tests = "from app import B\ndef test_read(): return B().read()\n"
    assert selected(
        compare(
            {"app.py": src, "test_app.py": tests}, "app.py", src.replace("return 1", "return 2")
        )
    ) == {"test_read"}


def test_class_alias_method_reference_is_not_dropped():
    src = "class C:\n    @staticmethod\n    def read(): return 1\n"
    tests = "from app import C\ndef test_read():\n    alias=C\n    return alias.read()\n"
    assert selected(
        compare(
            {"app.py": src, "test_app.py": tests}, "app.py", src.replace("return 1", "return 2")
        )
    ) == {"test_read"}


def test_repr_of_class_object_does_not_call_instance_repr():
    src = 'class C:\n    def __repr__(self): return "old"\n'
    tests = (
        "from app import C\n"
        "def test_instance(): return repr(C())\n"
        "def test_class(): return repr(C)\n"
        ""
    )
    assert selected(
        compare({"app.py": src, "test_app.py": tests}, "app.py", src.replace("old", "new"))
    ) == {"test_instance"}


def test_inherited_body_keeps_possible_subclass_override_in_other_module():
    base = "class Base:\n    def run(self): return self.read()\n    def read(self): return 1\n"
    child = "from base import Base\nclass Child(Base):\n    def read(self): return 2\n"
    tests = "from child import Child\ndef test_read(): return Child().run()\n"
    assert selected(
        compare(
            {"base.py": base, "child.py": child, "test_app.py": tests},
            "child.py",
            child.replace("return 2", "return 3"),
        )
    ) == {"test_read"}


def test_unused_function_local_import_does_not_select_sibling_body_edit():
    src = "def price(): return 1\n"
    tests = (
        "def test_unused():\n"
        "    from app import price\n"
        "    return 42\n"
        "def test_used():\n"
        "    from app import price\n"
        "    return price()\n"
        ""
    )
    assert selected(
        compare(
            {"app.py": src, "test_app.py": tests}, "app.py", src.replace("return 1", "return 2")
        )
    ) == {"test_used"}


def test_reference_budget_exhaustion_retains_fallback(monkeypatch):
    from codeimpact import selection

    monkeypatch.setattr(selection, "MAX_VISITS", 0)
    src = "class C:\n    def read(self): return 1\n"
    tests = "from app import C\ndef test_read(obj): return obj.read()\n"
    report = compare(
        {"app.py": src, "test_app.py": tests}, "app.py", src.replace("return 1", "return 2")
    )
    assert selected(report) == {"test_read"}
    assert any("reference budget" in w for w in report.warnings)


def test_str_uses_repr_when_class_has_no_str_override():
    src = 'class C:\n    def __repr__(self): return "old"\n'
    tests = "from app import C\ndef test_str(): return str(C())\n"
    assert selected(
        compare({"app.py": src, "test_app.py": tests}, "app.py", src.replace("old", "new"))
    ) == {"test_str"}


def test_container_repr_retains_possible_element_protocol_dependency():
    src = 'class C:\n    def __repr__(self): return "old"\n'
    tests = "from app import C\ndef test_repr(): return repr([C()])\n"
    assert selected(
        compare({"app.py": src, "test_app.py": tests}, "app.py", src.replace("old", "new"))
    ) == {"test_repr"}


def test_shadowed_builtin_does_not_invent_protocol_dispatch():
    src = 'class C:\n    def __repr__(self): return "old"\n'
    tests = 'from app import C\nrepr=lambda value: "constant"\ndef test_fake(): return repr(C())\n'
    assert (
        selected(
            compare({"app.py": src, "test_app.py": tests}, "app.py", src.replace("old", "new"))
        )
        == set()
    )


def test_unmodeled_operator_protocol_retains_broad_fallback():
    src = "class C:\n    def __add__(self, other): return 1\n"
    tests = "from app import C\ndef test_add(): return C()+1\n"
    assert selected(
        compare(
            {"app.py": src, "test_app.py": tests}, "app.py", src.replace("return 1", "return 2")
        )
    ) == {"test_add"}
