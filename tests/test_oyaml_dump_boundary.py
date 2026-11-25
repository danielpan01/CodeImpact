"""Source-only controls for the load/dump boundary and independent fallback seeds."""

import json
from pathlib import Path

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest

CASE = Path(__file__).parents[1] / "corpus/real-v4/cases/oyaml_error_context.json"
TEST_MODULE = "test_oyaml.py::<module>"
DUMP_SPANS = {
    "test_dump": (14, 15),
    "test_dump_all": (22, 26),
    "test_dump_and_safe_dump_match": (29, 32),
    "test_safe_dump": (18, 19),
    "test_safe_dump_all": (35, 39),
    "test_subclass_dump": (90, 94),
}


def test_pinned_oyaml_keeps_all_six_dump_edges_and_load_evidence():
    case = json.loads(CASE.read_bytes())
    request = AnalysisRequest.model_validate(case["request"])
    report = analyze(request)
    validate_report(request, report)

    by_test = {rec.symbol: rec for rec in report.recommendations}
    by_id = {edge.id: edge for edge in report.edges}
    assert by_test.keys() == (
        case["expected_affected"].keys()
        | case["expected_unaffected"].keys()
        | case["unclassified"].keys()
    )
    for name, (start, end) in DUMP_SPANS.items():
        sid = f"test_oyaml.py::{name}"
        rec = by_test[sid]
        assert rec.evidence_path == [sid, TEST_MODULE]
        assert rec.reason == "Conservative module/import dependency"
        assert rec.path_revision == "both" and rec.score == 50
        (eid,) = rec.evidence_edges
        edge = by_id[eid]
        assert (edge.kind, edge.source, edge.target) == ("module", sid, TEST_MODULE)
        for evidence, shift, module_end in ((edge.before, 0, 188), (edge.after, 1, 194)):
            (item,) = evidence
            assert (item.location.line, item.location.end_line) == (start + shift, end + shift)
            assert (item.target_location.line, item.target_location.end_line) == (1, module_end)

    changed_id = "test_oyaml.py::test_unhashable_error_context"
    changed_test = by_test[changed_id]
    assert changed_test.evidence_path == [changed_id]
    assert changed_test.reason == "Test itself changed"
    assert changed_test.path_revision == "after" and changed_test.evidence_edges == []
    for sid in case["unclassified"].keys() | (case["expected_affected"].keys() - {changed_id}):
        assert by_test[sid].evidence_path == [sid, TEST_MODULE]
        assert by_test[sid].path_revision == "both"


def test_the_pinned_test_module_edit_independently_retains_dump_recommendations():
    data = json.loads(CASE.read_bytes())["request"]
    request = AnalysisRequest.model_validate(data)
    # Keep the production and packaging sources identical to the base snapshot.
    request.head.files = request.base.files | {"test_oyaml.py": request.head.files["test_oyaml.py"]}
    report = analyze(request)
    validate_report(request, report)
    assert TEST_MODULE in report.changed
    assert "oyaml.py::<module>" not in report.changed
    assert {
        rec.symbol: rec.evidence_path[-1]
        for rec in report.recommendations
        if rec.symbol.split("::")[-1] in DUMP_SPANS
    } == {f"test_oyaml.py::{name}": TEST_MODULE for name in DUMP_SPANS}


BRIDGE = """import codec

def build():
    return 1

codec.add_constructor("map", build)
from codec import *
"""

# This invented backend witnesses a possible registration effect. Its source is
# inspected by the analyzer, never imported or executed.
BACKEND = """state = None

def add_constructor(tag, callback):
    global state
    state = callback()

def dump(value):
    return state, value

def load(value):
    return state, value
"""

TEST_SOURCE = """import bridge as api
from independent import check

def test_dump_only():
    assert api.dump({})

def test_load_only():
    assert api.load({})

def test_mixed():
    assert api.dump({})
    assert api.load({})

def test_independent():
    assert api.dump({})
    assert check()
"""


@pytest.mark.parametrize("known_side", ["before", "after", "neither"])
def test_registration_or_test_initialization_preserves_other_paths(known_side):
    base = {
        "bridge.py": BRIDGE,
        "test_bridge.py": TEST_SOURCE,
        "independent.py": "def check():\n    return 1\n",
    }
    head = base | {
        "bridge.py": BRIDGE.replace("return 1", "return 2"),
        "independent.py": "def check():\n    return 2\n",
    }
    if known_side == "before":
        base["codec.py"] = BACKEND
    elif known_side == "after":
        head["codec.py"] = BACKEND
    else:
        head["test_bridge.py"] = "from codec.errors import LoadError\n" + TEST_SOURCE
    request = AnalysisRequest.model_validate({"base": {"files": base}, "head": {"files": head}})
    report = analyze(request)
    validate_report(request, report)
    by_test = {rec.symbol: rec for rec in report.recommendations}
    direct = by_test["test_bridge.py::test_independent"]
    assert direct.evidence_path == ["test_bridge.py::test_independent", "independent.py::check"]
    assert direct.reason == "Resolved call path"
    assert direct.path_revision == "both"
    for test in ("test_dump_only", "test_load_only", "test_mixed"):
        sid = f"test_bridge.py::{test}"
        rec = by_test[sid]
        assert rec.reason == "Conservative module/import dependency"
        if known_side == "neither":
            assert rec.evidence_path == [sid, "test_bridge.py::<module>"]
            assert rec.path_revision == "both"
        else:
            assert rec.evidence_path == [
                sid,
                "test_bridge.py::<module>",
                "bridge.py::<module>",
                "codec.py::<module>",
            ]
            assert rec.path_revision == known_side
