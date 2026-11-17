"""Source-only legacy dispatch and aggregate fallback regressions."""

import textwrap

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot

CORE = """from .old import run as old_route
__all__ = ['render']

def edited(text):
    return text + 'before'

def modern(text):
    return edited(text)

def render(text, *, mode='old'):
    if mode not in ('old', 'new'):
        raise ValueError('invalid mode')
    if mode == 'old':
        return old_route(text)
    return modern(text)
"""
OLD = "def run(text):\n    return text.upper()\n"


def review(
    body,
    *,
    prefix="",
    core=CORE,
    old=OLD,
    package="from .render import *\n",
    head_changes=None,
    extra=None,
    parameters="",
):
    base = {
        "pkg/__init__.py": package,
        "pkg/render.py": core,
        "pkg/old.py": old,
        "test_use.py": "from pkg import render\n"
        + prefix
        + f"\ndef test_use({parameters}):\n"
        + textwrap.indent(body, "    "),
    }
    base.update(extra or {})
    head = base | {"pkg/render.py": core.replace("'before'", "'after'")} | (head_changes or {})
    request = AnalysisRequest(base=Snapshot(files=base), head=Snapshot(files=head))
    report = analyze(request)
    validate_report(request, report)
    return report


@pytest.mark.parametrize("suffix", ["", ", mode='old'"])
def test_known_legacy_dispatch_removes_aggregate_fallback(suffix):
    assert not review(f"assert render('abc'{suffix}) == 'ABC'\n").recommendations


@pytest.mark.parametrize(
    ("body", "prefix", "parameters"),
    [
        ("render('abc', mode='new')\n", "", ""),
        (
            "fast('abc')\n",
            "from functools import partial\nfast = partial(render, mode='new')\n",
            "",
        ),
        (
            "slow('abc', mode='new')\n",
            "from functools import partial\nslow = partial(render, mode='old')\n",
            "",
        ),
        ("render('abc')\nrender('abc', mode='new')\n", "", ""),
        ("render('abc', mode=mode)\n", "", "mode"),
        ("render(text)\n", "", "text"),
        (
            "alias('abc')\nrender = unknown()\nrender('abc')\n",
            "from pkg import render as alias\n",
            "",
        ),
        ("publish(render)\nrender('abc')\n", "", ""),
        ("render('abc')\n", "hook()\n", ""),
    ],
)
def test_affected_or_unproved_calls_keep_evidence(body, prefix, parameters):
    assert review(body, prefix=prefix, parameters=parameters).recommendations


@pytest.mark.parametrize(
    "package",
    [
        "from .render import *\nstartup()\n",
        "from .render import *\nfrom unknown_dependency import callback\n",
        "from .render import *\nexec('modify exports')\n",
        "from .render import *\nfrom .old import run as render\n",
    ],
)
def test_effectful_or_ambiguous_package_keeps_fallback(package):
    assert review("render('abc')\n", package=package).recommendations


def test_imported_legacy_module_cannot_reach_modern_helper():
    old = "def run(text):\n    from .render import edited\n    return edited(text)\n"
    assert review("render('abc')\n", old=old).recommendations


def test_legacy_module_change_keeps_fallback():
    assert review(
        "render('abc')\n", head_changes={"pkg/old.py": OLD.replace("upper", "lower")}
    ).recommendations


def test_before_only_route_keeps_fallback():
    old = "def run(text):\n    from .render import edited\n    return edited(text)\n"
    assert review("render('abc')\n", old=old, head_changes={"pkg/old.py": OLD}).recommendations


def test_deleted_callable_preserves_evidence():
    head = CORE.replace("def edited(text):\n    return text + 'before'\n\n", "")
    report = review("render('abc')\n", head_changes={"pkg/render.py": head})
    assert report.recommendations
    assert "pkg/render.py::edited" in report.removed


def test_budget_exhaustion_keeps_fallback(monkeypatch):
    from codeimpact import call_arguments

    monkeypatch.setattr(call_arguments, "MAX_STEPS", 0)
    assert review("render('abc')\n").recommendations


def test_eager_call_into_edited_helper_keeps_fallback():
    core = CORE + "\nINITIAL_VALUE = edited('payload')\n"
    assert review("render('abc')\n", core=core).recommendations


def test_unknown_import_result_is_not_assumed_to_be_data():
    old = """from importlib import import_module
def run(text):
    module = import_module('unknown_backend')
    return getattr(module, 'render')(text)
"""
    assert review("render('abc')\n", old=old).recommendations


def test_deliberate_default_rebinding_after_definition_keeps_fallback():
    core = "DEFAULT_MODE = 'new'\n" + CORE.replace("mode='old'", "mode=DEFAULT_MODE")
    core += "\nDEFAULT_MODE = 'old'\n"
    assert review("render('abc')\n", core=core).recommendations


def test_another_changed_callable_keeps_resolved_evidence():
    extra = "from independent import other\n"
    report = review(
        "render('abc')\nother()\n",
        prefix=extra,
        extra={"independent.py": "def other(): return 1\n"},
        head_changes={"independent.py": "def other(): return 2\n"},
    )
    assert report.recommendations[0].evidence_path[-1] == "independent.py::other"


def test_audit_budget_exhaustion_keeps_fallback(monkeypatch):
    from codeimpact import dispatch_fallback

    monkeypatch.setattr(dispatch_fallback, "MAX_AUDIT_STEPS", 1)
    assert review("render('abc')\n").recommendations


def review_unittest_case(hook=""):
    source = (
        "import unittest\n"
        "from pkg import render\n"
        "from pkg.render import edited\n\n"
        "class TestLegacy(unittest.TestCase):\n"
        + textwrap.indent(hook, "    ")
        + "    def test_legacy(self):\n"
        "        self.assertEqual(render('abc'), 'ABC')\n"
    )
    return review("", extra={"test_use.py": source})


@pytest.mark.parametrize(
    "hook",
    [
        "def __new__(cls, *args, **kwargs):\n"
        "    edited('construction')\n"
        "    return super().__new__(cls)\n\n",
        "def doCleanups(self):\n    edited('cleanup')\n    return super().doCleanups()\n\n",
    ],
    ids=["construction", "cleanup"],
)
def test_unittest_lifecycle_override_keeps_conservative_evidence(hook):
    report = review_unittest_case(hook)
    assert len(report.recommendations) == 1
    item = report.recommendations[0]
    assert item.symbol == "test_use.py::TestLegacy.test_legacy"
    assert item.reason == "Conservative module/import dependency"
    assert item.evidence_path[-1] == "pkg/render.py::<module>"
    assert item.path_revision == "both"


def test_plain_unittest_legacy_dispatch_removes_aggregate_fallback():
    assert not review_unittest_case().recommendations
