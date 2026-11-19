"""Source-only qualified calls through captured package initializers."""

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot

INIT = '"""Public package."""\nfrom .logic import normalize\n__all__ = ["normalize"]\n'
CORE = "def normalize(value):\n    return value + 1\n"
TEST = "import parcel\n\ndef test_normalize():\n    assert parcel.normalize(1) == 2\n"
CALLER = "tests/test_parcel.py::test_normalize"
CALLEE = "src/parcel/logic.py::normalize"


def compare(
    *,
    initializer=INIT,
    new_initializer=None,
    test=TEST,
    new_test=None,
    extra=None,
    core=CORE,
    new_core=None,
):
    files = {
        "src/parcel/__init__.py": initializer,
        "src/parcel/logic.py": core,
        "tests/test_parcel.py": test,
    } | (extra or {})
    head = files | {
        "src/parcel/__init__.py": initializer if new_initializer is None else new_initializer,
        "src/parcel/logic.py": core.replace("+ 1", "+ 2") if new_core is None else new_core,
        "tests/test_parcel.py": test if new_test is None else new_test,
    }
    request = AnalysisRequest(base=Snapshot(files=files), head=Snapshot(files=head))
    report = analyze(request)
    validate_report(request, report)
    return request, report


def call_edges(report):
    return [
        e for e in report.edges if e.source == CALLER and e.target == CALLEE and e.kind == "call"
    ]


def test_qualified_reexport_upgrades_existing_src_layout_path():
    request, report = compare()
    legacy = analyze(request, reexports=False)
    (rec,) = report.recommendations
    (edge,) = call_edges(report)
    assert rec.symbol == CALLER
    assert rec.reason == "Resolved call path"
    assert rec.evidence_path == [CALLER, CALLEE]
    assert rec.evidence_edges == [edge.id]
    assert rec.path_revision == edge.revision == "both"
    assert all(
        e.location.line == 4 and e.target_location.line == 1 for e in edge.before + edge.after
    )
    assert any(
        e.kind == "import" and e.target == "src/parcel/__init__.py::<module>" for e in report.edges
    )
    assert [r.symbol for r in legacy.recommendations] == [rec.symbol]
    assert report.impacted == legacy.impacted
    assert {e.id for e in legacy.edges} <= {e.id for e in report.edges}


def test_existing_changed_test_evidence_keeps_precedence():
    _, report = compare(new_test=TEST.replace("== 2", "== 3"))
    (rec,) = report.recommendations
    assert call_edges(report)
    assert rec.evidence_path == [CALLER]
    assert rec.reason == "Test itself changed"


def test_one_revision_binding_preserves_exact_source_evidence():
    _, report = compare(new_initializer=INIT + "\nnormalize = other\n")
    (edge,) = call_edges(report)
    assert edge.revision == "before"
    assert edge.before[0].location.model_dump() == {
        "path": "tests/test_parcel.py",
        "line": 4,
        "end_line": 4,
    }
    assert edge.before[0].target_location.model_dump() == {
        "path": "src/parcel/logic.py",
        "line": 1,
        "end_line": 2,
    }
    assert edge.after == []
    assert next(r for r in report.recommendations if r.symbol == CALLER).path_revision == "before"


@pytest.mark.parametrize(
    "initializer",
    [
        "from .logic import *\n",
        "if choose:\n    from .logic import normalize\n",
        INIT + "from .other import normalize\n",
        INIT + "normalize = other\n",
        INIT + "globals()['normalize'] = other\n",
        INIT + "def __getattr__(name): return fallback\n",
        INIT
        + "import pkg_resources\n__version__ = pkg_resources.get_distribution(__name__).version\n",
        INIT + "from .hooks import configure\nconfigure()\n",
    ],
)
def test_unproved_exports_or_eager_effects_add_no_call(initializer):
    _, report = compare(
        initializer=initializer,
        extra={
            "src/parcel/other.py": "def normalize(x): return x\n",
            "src/parcel/hooks.py": "def configure(): pass\n",
        },
    )
    assert call_edges(report) == []


@pytest.mark.parametrize(
    "test",
    [
        TEST.replace("test_normalize()", "test_normalize(parcel)"),
        TEST.replace("    assert", "    parcel = factory()\n    assert"),
        TEST.replace("    assert", "    import fake as parcel\n    assert"),
        TEST + "parcel.normalize = replacement\n",
        TEST + "copy = parcel\ncopy.normalize = replacement\n",
        TEST.replace("    assert", "    setattr(parcel, 'normalize', replacement)\n    assert"),
        TEST + "globals()['parcel'] = replacement\n",
        "from freezegun import freeze_time\n"
        + TEST.replace("def test", "@freeze_time()\ndef test"),
    ],
)
def test_unproved_consumer_binding_adds_no_call(test):
    _, report = compare(test=test)
    assert call_edges(report) == []


def test_import_cycle_declines():
    _, report = compare(initializer=INIT, core="from . import normalize\n" + CORE)
    assert call_edges(report) == []


def test_mutation_through_a_neighbouring_source_import_declines():
    _, report = compare(extra={"mutator.py": "import parcel as p\np.normalize = replacement\n"})
    assert call_edges(report) == []


def test_same_name_submodule_declines():
    _, report = compare(extra={"src/parcel/normalize.py": "pass\n"})
    assert call_edges(report) == []


def test_deleted_export_target_keeps_before_evidence():
    _, report = compare(new_core="", new_initializer="pass\n")
    (edge,) = call_edges(report)
    assert CALLEE in report.removed
    assert edge.revision == "before" and not edge.after
    assert CALLER in {r.symbol for r in report.recommendations}


def test_independent_module_effect_survives_resolved_call_edge():
    _, report = compare(
        new_core=CORE + "\nSHARED = 2\n",
        core=CORE + "\nSHARED = 1\n",
    )
    assert call_edges(report)
    (rec,) = report.recommendations
    assert rec.reason == "Conservative module/import dependency"
    assert rec.evidence_path[-1] == "src/parcel/logic.py::<module>"
