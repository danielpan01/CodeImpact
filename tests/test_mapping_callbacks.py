"""Literal-raising local callbacks: source-only negative proof and ambiguity controls."""

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot

CORE = """class Edited:
    def __setitem__(self, key, value): self.value = 1
class Other:
    def __init__(self, choice): self.choice = choice
    def __setitem__(self, key, value): self.choice(key)
"""
CALLBACK = "    def reject(value):\n        raise ValueError('rejected')\n"


def source(body="    obj = Other(choice=reject)\n    obj[0] = 1\n", callback=CALLBACK):
    return "from app import Edited, Other\ndef test_case():\n" + callback + body


def compare(tests=None, core=CORE, head=None):
    files = {"app.py": core, "test_app.py": tests or source()}
    request = AnalysisRequest(
        base=Snapshot(files=files),
        head=Snapshot(
            files=head or files | {"app.py": core.replace("self.value = 1", "self.value = 2")}
        ),
    )
    report = analyze(request)
    validate_report(request, report)
    return report


@pytest.mark.parametrize(
    "exception", ["ValueError('rejected')", "TypeError()", "RuntimeError(1)", "KeyError(None)"]
)
def test_literal_raising_callback_does_not_reference_sibling_mapping(exception):
    assert not compare(
        source(callback=CALLBACK.replace("ValueError('rejected')", exception))
    ).recommendations


def test_constructor_alias_retains_concrete_identity():
    assert not compare(
        source("    Constructor = Other\n    obj = Constructor(choice=reject)\n    obj[0] = 1\n")
    ).recommendations


@pytest.mark.parametrize(
    "body",
    [
        "    obj = Edited()\n    obj[0] = 1\n",
        "    obj = unknown(choice=reject)\n    obj[0] = 1\n",
        "    obj = Other(choice=reject, size=unknown())\n    obj[0] = 1\n",
        "    alias = reject\n    obj = Other(choice=alias)\n    obj[0] = 1\n",
        "    reject = unknown\n    obj = Other(choice=reject)\n    obj[0] = 1\n",
        "    obj = Other(choice=reject)\n    obj = unknown()\n    obj[0] = 1\n",
        "    reject.__code__ = unknown\n    obj = Other(choice=reject)\n    obj[0] = 1\n",
        "    return reject\n",
    ],
)
def test_unknown_or_dependent_uses_retain_fallback(body):
    assert compare(source(body)).recommendations


@pytest.mark.parametrize(
    "callback",
    [
        "    def reject(value):\n        value[0] = 1\n",
        "    def reject(value):\n        raise ValueError(value)\n",
        "    def reject(value):\n        raise ValueError('x') from unknown\n",
        "    def reject(value=unknown()):\n        raise ValueError('x')\n",
        "    def reject(value: unknown()):\n        raise ValueError('x')\n",
        "    @decorate\n    def reject(value):\n        raise ValueError('x')\n",
        "    async def reject(value):\n        raise ValueError('x')\n",
        "    if flag:\n        def reject(value):\n            raise ValueError('x')\n",
        "    class reject:\n        pass\n",
        CALLBACK + CALLBACK,
        "    def reject(ValueError):\n        raise ValueError('x')\n",
        "    def reject(value):\n        return 0\n",
    ],
)
def test_unsupported_callback_forms_retain_fallback(callback):
    assert compare(source(callback=callback)).recommendations


@pytest.mark.parametrize(
    "shadow",
    ["ValueError = unknown\n", "from external import ValueError\n", "from external import *\n"],
)
def test_shadowed_exception_is_not_a_builtin_proof(shadow):
    assert compare(shadow + source()).recommendations


def test_inherited_override_reaches_edited_mapping():
    core = (
        CORE + "class Child(Other):\n    def __setitem__(self, key, value):\n"
        "        obj = Edited()\n        obj[key] = value\n"
    )
    tests = source().replace(
        "from app import Edited, Other", "from app import Edited, Child as Other"
    )
    assert compare(tests, core).recommendations


def test_shared_definition_is_not_specialized():
    tests = source().replace("def test_case():", "class Shared:\n def test_case(self):")
    tests += "class TestOne(Shared): pass\nclass TestTwo(Shared): pass\n"
    assert compare(tests).recommendations


def test_effectful_constructor_hook_keeps_fallback():
    core = CORE.replace("class Other:", "class Other:\n    __new__ = hook")
    assert compare(core=core).recommendations


def test_before_dependency_and_deleted_method_keep_evidence():
    old = source().replace("raise ValueError('rejected')", "obj = Edited(); obj[0] = 1")
    report = compare(old, head={"app.py": CORE, "test_app.py": source()})
    assert report.recommendations
    report = compare(
        head={
            "app.py": CORE.replace(
                "    def __setitem__(self, key, value): self.value = 1", "    pass"
            ),
            "test_app.py": source(),
        }
    )
    assert report.recommendations
    assert "app.py::Edited.__setitem__" in report.removed


def test_query_budget_exhaustion_keeps_fallback(monkeypatch):
    from codeimpact import mapping_protocols

    monkeypatch.setattr(mapping_protocols, "MAX_VISITS", 0)
    assert compare().recommendations


@pytest.mark.parametrize(
    "binding",
    [
        "try:\n    pass\nexcept Exception as ValueError:\n    pass\n",
        "match unknown:\n    case ValueError:\n        pass\n",
        "import builtins\nbuiltins.ValueError = unknown\n",
    ],
)
def test_exception_binding_forms_are_conservative(binding):
    assert compare(binding + source()).recommendations


@pytest.mark.parametrize(
    "binding",
    [
        "    try:\n        pass\n    except Exception as reject:\n        pass\n",
        "    match unknown:\n        case reject:\n            pass\n",
        "    from external import reject\n",
    ],
)
def test_callback_rebinding_forms_are_conservative(binding):
    assert compare(
        source(binding + "    obj = Other(choice=reject)\n    obj[0] = 1\n")
    ).recommendations


def test_builtin_identity_scan_has_a_conservative_budget(monkeypatch):
    from codeimpact import mapping_protocols

    monkeypatch.setattr(mapping_protocols, "MAX_VISITS", 20)
    assert compare().recommendations


def test_callback_cannot_inspect_unknown_argument_even_via_exception_constructor():
    assert compare(
        source(callback=CALLBACK.replace("ValueError('rejected')", "ValueError(str(value))"))
    ).recommendations


def test_changed_receiver_before_head_preserves_entire_recommendation(monkeypatch):
    from codeimpact.mapping_protocols import MappingReferences

    tests = source("    obj = Edited()\n    obj[0] = 1\n")
    current = compare(tests)
    monkeypatch.setattr(MappingReferences, "closed_callbacks", lambda *_: False)
    previous = compare(tests)
    assert current.recommendations == previous.recommendations
    assert current.edges == previous.edges
    assert current.nodes == previous.nodes


@pytest.mark.parametrize(
    "mutation",
    [
        "globals()['ValueError'] = hook\n",
        "__builtins__ = {'ValueError': hook}\n",
        "import builtins\nbuiltins.__dict__['ValueError'] = hook\n",
        "import builtins\nbuiltins.setattr(builtins, 'ValueError', hook)\n",
        "import builtins\ngetattr(builtins, '__dict__')['ValueError'] = hook\n",
    ],
)
def test_reflective_exception_binding_cannot_prove_literal_raise(mutation):
    hook = "def hook(value):\n    obj = Edited()\n    obj[0] = 1\n    return Exception(value)\n"
    assert compare(source() + hook + mutation).recommendations
