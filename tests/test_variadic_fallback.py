"""Source-only controls for guarded callable-instance dependencies."""

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot

TEST = """import unittest
from public import debug

class Example(unittest.TestCase):
    def setUp(self):
        debug.separator = '-'

    def testArgument(self):
        debug(1)

    def testEmpty(self):
        debug()

    def testBoth(self):
        debug(1)
        debug()
"""
CORE = """from contextlib import contextmanager
from datetime import datetime

def echo(value):
    return value

class Writer:
    separator = ','

    def __init__(self, output=echo):
        self.output = output

    def __call__(self, *values):
        return self.render(*values)

    def render(self, *values):
        if not values:
            return self.stamp()
        return self.output(values)

    def stamp(self):
        return 'old'

debug = Writer()
"""
PREFIX = "test_writer.py::Example."


def reports(*, core=CORE, test=TEST, head_test=None, more=None, head_more=None, head_core=None):
    reordered = "\n".join(reversed(core.splitlines()[:2])) + "\n"
    changed = (reordered + "\n".join(core.splitlines()[2:]) + "\n").replace(
        "return 'old'", "return 'new'"
    )
    base = {"writer.py": core, "public.py": "from writer import debug\n", "test_writer.py": test}
    head = base | {
        "writer.py": changed if head_core is None else head_core,
        "test_writer.py": test if head_test is None else head_test,
    }
    base.update(more or {})
    head.update(more or {})
    head.update(head_more or {})
    request = AnalysisRequest(base=Snapshot(files=base), head=Snapshot(files=head))
    report = analyze(request)
    validate_report(request, report)
    return {r.symbol: r for r in report.recommendations}


def test_proven_nonempty_forwarding_keeps_empty_and_mixed_calls():
    selected = reports()
    assert set(selected) == {PREFIX + "testEmpty", PREFIX + "testBoth"}
    for rec in selected.values():
        assert rec.path_revision == "both"
        assert rec.reason == "Conservative module/import dependency"


def test_independent_changed_dependency_replaces_the_filtered_contribution():
    source = TEST.replace(
        "from public import debug", "from public import debug\nfrom other_public import cost"
    )
    source = source.replace("        debug(1)\n", "        debug(1)\n        cost()\n", 1)
    selected = reports(
        test=source,
        more={
            "other_public.py": "from middle import cost\n",
            "middle.py": "from extra import cost\n",
            "extra.py": "fee = 1\ndef cost(): return fee\n",
        },
        head_more={"extra.py": "fee = 2\ndef cost(): return fee\n"},
    )
    rec = selected[PREFIX + "testArgument"]
    assert rec.evidence_path[-1] == "extra.py::<module>"
    assert rec.evidence_path[0] == PREFIX + "testArgument"
    assert rec.path_revision == "both"


@pytest.mark.parametrize(
    "test",
    [
        TEST.replace("debug(1)", "debug(*values)", 1),
        TEST.replace("        debug(1)", "        debug = get_debug()\n        debug(1)", 1),
        TEST.replace("        debug(1)", "        debug.render = replacement\n        debug(1)", 1),
        TEST.replace(
            "        debug(1)", "        debug.output = get_callback()\n        debug(1)", 1
        ),
        TEST.replace("        debug(1)", "        debug(1)\n        opaque(debug)", 1),
        TEST.replace(
            "    def testArgument",
            "    def tearDown(self):\n        debug()\n\n    def testArgument",
        ),
        TEST.replace(
            "    def testArgument",
            "    def doCleanups(self):\n        debug()\n\n    def testArgument",
        ),
        TEST.replace("debug.separator = '-'", "debug()"),
        TEST + "\ndef setUpModule():\n    debug()\n",
    ],
)
def test_ambiguous_arguments_bindings_callbacks_or_hooks_retain_fallback(test):
    assert PREFIX + "testArgument" in reports(test=test)


def test_dependency_seen_in_one_revision_retains_fallback():
    test = TEST.replace(
        "from public import debug", "from public import debug\nfrom extra import run"
    )
    test = test.replace("        debug(1)", "        run()\n        debug(1)", 1)
    selected = reports(
        test=test,
        more={"extra.py": "from public import debug\ndef run(): debug()\n"},
        head_more={"extra.py": "from public import debug\ndef run(): debug(1)\n"},
    )
    assert PREFIX + "testArgument" in selected


def test_other_initialization_edit_is_never_removed():
    head = CORE.replace("return 'old'", "return 'new'").replace(
        "    separator = ','", "    separator = ';'"
    )
    assert PREFIX + "testArgument" in reports(head_core=head)


def test_uncaptured_callback_is_never_assumed_safe():
    core = CORE.replace("output=echo", "output=emit").replace(
        "def echo(value):", "from unavailable import emit\n\ndef echo(value):"
    )
    assert PREFIX + "testArgument" in reports(core=core)


def test_captured_collection_hook_retains_fallback():
    selected = reports(
        more={"conftest.py": "from public import debug\ndef pytest_runtest_setup(item): debug()\n"}
    )
    assert selected[PREFIX + "testArgument"].evidence_path[-1] == "writer.py::<module>"


@pytest.mark.parametrize("hook", ["setup_module", "teardown_module", "pytestmark"])
def test_unmodeled_module_lifecycle_retains_fallback(hook):
    source = TEST + (
        f"\ndef {hook}(): debug()\n" if hook != "pytestmark" else "\npytestmark = 'custom'\n"
    )
    assert PREFIX + "testArgument" in reports(test=source)
