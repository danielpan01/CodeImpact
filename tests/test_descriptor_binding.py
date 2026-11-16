"""Source-only controls for ordinary class lookup and raw descriptor dispatch."""

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot

CORE = """class Bound:
    def __call__(self):
        raise TypeError("receiver required")

class Descriptor:
    def __call__(self, *args, **kwargs):
        return 1

    def __get__(self, obj, owner=None):
        if obj is None:
            return Bound()
        return self

def wrap(fn):
    return Descriptor()
"""

HOST = """class Owner:
    @wrap
    def method(self):
        return 2
"""


def review(body, host=HOST, core=CORE, *, head=None, extra=""):
    test = "from lib import wrap, Descriptor\n" + extra + host + "def test_use():\n" + body
    base = {"lib.py": core, "test_use.py": test}
    request = AnalysisRequest(
        base=Snapshot(files=base),
        head=Snapshot(
            files=head or base | {"lib.py": core.replace("self, *args", "self, /, *args")}
        ),
    )
    report = analyze(request)
    validate_report(request, report)
    return report


@pytest.mark.parametrize(
    "body", ["    Owner.method()\n", "    Alias = Owner\n    Alias.method()\n"]
)
def test_ordinary_class_binding_uses_a_separate_callable(body):
    assert not review(body).recommendations


@pytest.mark.parametrize(
    "body",
    [
        "    Owner().method()\n",
        "    Descriptor()()\n",
        "    Descriptor.__call__(Descriptor())\n",
        "    Owner = unknown()\n    Owner.method()\n",
        "    value = Owner.method\n    dispatch(value)\n",
        "    inspect.signature(Owner.method)\n",
        "    setattr(Owner, 'method', Descriptor())\n    Owner.method()\n",
        "    Owner().method = Descriptor()\n    Owner.method()\n",
        "    super().method()\n",
    ],
)
def test_raw_unknown_or_escaping_callable_remains_selected(body):
    assert review(body).recommendations


@pytest.mark.parametrize("decorators", ["@classmethod\n    @wrap", "@wrap\n    @classmethod"])
def test_classmethod_order_is_conservative(decorators):
    assert review("    Owner.method()\n", HOST.replace("@wrap", decorators)).recommendations


@pytest.mark.parametrize(
    "edit",
    [
        "class Owner(metaclass=Meta):",
        "class Owner(Unknown):",
        "class Owner:\n    def __getattribute__(self, name): return Descriptor()",
        "class Owner:\n    def __getattr__(self, name): return Descriptor()",
        "class Owner:\n    effect = Descriptor()()",
    ],
)
def test_custom_or_effectful_owner_is_conservative(edit):
    assert review("    Owner.method()\n", HOST.replace("class Owner:", edit)).recommendations


@pytest.mark.parametrize(
    "core",
    [
        CORE.replace("def wrap(fn):", "def wrap(fn, flag=Descriptor()()):"),
        CORE.replace("    return Descriptor()", "    Descriptor()()\n    return Descriptor()"),
        CORE.replace("def wrap(fn):", "@opaque\ndef wrap(fn):"),
        CORE.replace("    return Descriptor()", "    return wrap(fn)"),
        CORE + "\nDescriptor()()\n",
    ],
)
def test_factory_effects_or_cycle_keep_fallback(core):
    assert review("    Owner.method()\n", core=core).recommendations


def test_shadowed_classmethod_keeps_fallback():
    host = HOST.replace("@wrap", "@classmethod\n    @wrap")
    assert review("    Owner.method()\n", host, extra="classmethod = unknown\n").recommendations


def test_inherited_override_and_shared_test_are_conservative():
    host = (
        HOST
        + """class Child(Owner):
    method = Descriptor()
"""
    )
    assert review("    Child.method()\n", host).recommendations
    host += """class Shared:
    def test_mixin(self):
        self.method()

class TestChild(Shared, Child):
    pass
"""
    assert review("    Owner.method()\n", host).recommendations


def test_changed_body_or_deleted_method_keeps_fallback():
    changed_body = {
        "lib.py": CORE.replace("return 1", "return 3").replace("self, *args", "self, /, *args"),
        "test_use.py": "from lib import wrap, Descriptor\n"
        + HOST
        + "def test_use():\n    Owner.method()\n",
    }
    assert review("    Owner.method()\n", head=changed_body).recommendations
    head = {
        "lib.py": CORE.replace(
            "    def __call__(self, *args, **kwargs):\n        return 1\n\n", ""
        ),
        "test_use.py": "from lib import wrap, Descriptor\n"
        + HOST
        + "def test_use():\n    Descriptor()()\n",
    }
    report = review("    Descriptor()()\n", head=head)
    assert report.recommendations
    assert "lib.py::Descriptor.__call__" in report.removed


def test_effectful_construction_is_conservative():
    host = HOST.replace("class Owner:", "class Owner:\n    def __init__(self): Descriptor()()")
    assert review("    Owner().method()\n", host).recommendations


def test_separate_instance_wrapper_and_factory_alias():
    core = CORE.replace("        return self", "        return Bound()")
    host = HOST + "\ndef factory(): return Owner()\n"
    assert not review("    make = factory()\n    make.method()\n", host, core).recommendations


def test_unknown_descriptor_getter_can_invoke_raw_callable():
    core = CORE.replace(
        "            return Bound()", "            self()\n            return Bound()"
    )
    assert review("    Owner.method()\n", core=core).recommendations


def test_before_only_binding_route_retains_original_path():
    before = HOST.replace("@wrap", "@classmethod\n    @wrap")
    head = {
        "lib.py": CORE.replace("self, *args", "self, /, *args"),
        "test_use.py": "from lib import wrap, Descriptor\n"
        + HOST
        + "def test_use():\n    Owner.method()\n",
    }
    assert review("    Owner.method()\n", host=before, head=head).recommendations


def test_budget_exhaustion_retains_fallback(monkeypatch):
    from codeimpact import descriptor_binding

    monkeypatch.setattr(descriptor_binding, "MAX_STEPS", 1)
    assert review("    Owner.method()\n").recommendations


@pytest.mark.parametrize(
    "operation",
    [
        "Owner.method = Descriptor()",
        "globals()['Owner'] = Descriptor",
        "dispatch(Descriptor())",
    ],
)
def test_unsafe_mutation_or_raw_escape_declines(operation):
    assert review("    Owner.method()\n", host=HOST + operation + "\n").recommendations


def test_class_subscription_annotation_is_not_passive():
    core = CORE.replace(
        "class Descriptor:",
        "class Descriptor:\n    def __class_getitem__(cls, item): return cls()()",
    )
    assert review(
        "    Owner.method()\n", host=HOST + "item: Descriptor[int]\n", core=core
    ).recommendations


def test_exception_superclass_handler_can_reach_raw_descriptor():
    core = CORE.replace(
        '        raise TypeError("receiver required")',
        "        try:\n"
        '            raise TypeError("receiver required")\n'
        "        except Exception:\n"
        "            return Descriptor()()",
    )
    assert review("    Owner.method()\n", core=core).recommendations


def test_property_access_can_reach_raw_descriptor():
    core = CORE.replace(
        "class Bound:\n",
        "class Bound:\n    @property\n    def value(self): return Descriptor()()\n\n",
    ).replace(
        '        raise TypeError("receiver required")',
        "        self.value\n        return None",
    )
    assert review("    Owner.method()\n", core=core).recommendations


def test_advancing_an_iterator_can_reach_raw_descriptor():
    core = CORE.replace(
        '        raise TypeError("receiver required")',
        "        flags = iter((True, False))\n"
        "        next(flags)\n"
        "        if next(flags):\n"
        "            return None\n"
        "        return Descriptor()()",
    )
    assert review("    Owner.method()\n", core=core).recommendations


def test_non_none_initializer_can_enter_exception_handler():
    core = CORE.replace(
        "class Bound:\n",
        "class Invalid:\n    def __init__(self): return 1\n\nclass Bound:\n",
    ).replace(
        '        raise TypeError("receiver required")',
        "        try:\n"
        "            Invalid()\n"
        "        except TypeError:\n"
        "            return Descriptor()()",
    )
    assert review("    Owner.method()\n", core=core).recommendations
