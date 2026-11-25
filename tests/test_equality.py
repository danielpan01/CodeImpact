"""Equality evidence uses only parsed snapshot source."""

import json
from pathlib import Path
from textwrap import dedent

import pytest

from codeimpact.analyzer import analyze
from codeimpact.equality_evaluate import evaluate_equality
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest
from codeimpact.v5_evaluate import DIRECTORY

TEST = "tests/test_item.py::test_equal"
SOURCE = "src/values/core.py"
WRAPPER = f"{SOURCE}::checked.wrapper"
SYMBOL = "test_should_versioninfo_bump_major_and_minor"
CORE = dedent("""\
    from functools import wraps

    def checked(method):
        @wraps(method)
        def wrapper(self, other):
            return method(self, other) and True
        return wrapper

    class Item:
        def __init__(self, value):
            self._value = value

        @classmethod
        def parse(cls, value):
            return cls(int(value))

        def bump(self):
            cls = type(self)
            return cls(self._value + 1)

        @checked
        def __eq__(self, rhs):
            return self._value == rhs._value

    def parse(value):
        return Item.parse(value)
    """)
TESTS = dedent("""\
    from values import parse, Item

    def test_equal():
        left = parse("1")
        right = parse("2")
        assert left.bump() == right
    """)


def request_for(tests=TESTS, *, base_core=CORE, head_core=None, package=None):
    base = {
        SOURCE: base_core,
        "src/values/__init__.py": package or "from .core import parse, Item\n",
        "tests/test_item.py": tests,
    }
    head = {**base, SOURCE: head_core or base_core.replace("and True", "and False")}
    return AnalysisRequest.model_validate({"base": {"files": base}, "head": {"files": head}})


def equality_edges(report):
    return [
        edge
        for edge in report.edges
        if any("via ==" in entry.text for entry in edge.before + edge.after)
    ]


@pytest.mark.parametrize("module", ["values", "values.core"])
def test_exact_class_from_export_and_receiver_chain(module):
    request = request_for(TESTS.replace("from values import", f"from {module} import"))
    report = analyze(request)
    validate_report(request, report)
    (edge,) = equality_edges(report)
    assert (edge.source, edge.target, edge.kind, edge.revision) == (TEST, WRAPPER, "call", "both")
    assert edge.before == edge.after
    assert edge.before[0].location.model_dump() == {
        "path": "tests/test_item.py",
        "line": 6,
        "end_line": 6,
    }
    assert edge.before[0].target_location.path == SOURCE
    assert edge.before[0].target_location.line == 4
    recommendation = next(row for row in report.recommendations if row.symbol == TEST)
    assert recommendation.evidence_path == [TEST, WRAPPER]
    assert recommendation.path_revision == "both"
    assert recommendation.reason == "Resolved call path"


@pytest.mark.parametrize(
    "test_body",
    [
        'left = parse("1")\n    right = unknown()\n    assert left == right',
        'left = parse("1")\n    right = parse("2")\n'
        "    right = unknown()\n    assert left == right",
        'parse = unknown\n    assert parse("1") == parse("2")',
        "assert 1 == Item(1)",
        "assert Item(1) == 1",
        "assert Item(1) != Item(2)",
        "assert Item(1) == Item(2) == Item(3)",
        "assert Item(1) == Child(2)",
        "assert Child(2) == Item(1)",
        "assert Child(2) == Child(1)",
        'assert left == right\n    left = parse("1")',
        "left = Item(1)\n    disrupt(left)\n    assert left == Item(2)",
    ],
)
def test_unknown_shadowed_or_reflected_operands(test_body):
    tests = "from values import parse, Item\n"
    if "Child" in test_body:
        tests += "class Child(Item): pass\n"
    request = request_for(tests + "\ndef test_equal():\n    " + test_body + "\n")
    report = analyze(request)
    assert not equality_edges(report)
    assert report.recommendations == analyze(request, equality=False).recommendations


@pytest.mark.parametrize(
    "source",
    [
        CORE.replace("@checked", "@unstudied"),
        CORE.replace("@wraps(method)", "@unstudied"),
        CORE.replace("    return wrapper\n", "    return proxy(wrapper)\n"),
        CORE + "\nItem.__eq__ = alternate\n",
        CORE + "\nother = Item\nother.__eq__ = alternate\n",
        CORE.replace("class Item:", "class Item(metaclass=other):"),
        CORE.replace(
            "    def __init__", "    def __new__(cls, value): return other(value)\n    def __init__"
        ),
        CORE.replace("return cls(int(value))", "return cls(int(value)) if value else other()"),
        CORE.replace("from functools import wraps", "from another import wraps"),
        CORE.replace("def wrapper(self, other):", "def wrapper(self):"),
        CORE.replace("self._value + 1", "self.unproved_property + 1"),
        CORE.replace("cls = type(self)", "if self._value:\n        cls = type(self)"),
    ],
)
def test_unproved_binding_does_not_add_equality_edge(source):
    assert not equality_edges(analyze(request_for(base_core=source)))


def test_before_only_equality_uses_before_location():
    request = request_for(
        head_core=CORE.replace("@checked", "@unknown").replace("and True", "and False")
    )
    report = analyze(request)
    validate_report(request, report)
    (edge,) = equality_edges(report)
    assert edge.revision == "before" and edge.before and not edge.after
    rec = next(row for row in report.recommendations if row.symbol == TEST)
    assert rec.path_revision == "before"


def test_unparseable_import_blocks_equality_evidence_in_that_revision():
    request = request_for("import dependency\n" + TESTS)
    request.base.files["dependency.py"] = "pass\n"
    request.head.files["dependency.py"] = "def incomplete(\n"
    report = analyze(request)
    validate_report(request, report)
    (edge,) = equality_edges(report)
    assert edge.revision == "before" and edge.before and not edge.after


def test_frozen_semver_miss_gains_wrapper_edge():
    path = Path("datasets/real-v5/cases/semver_subclass_comparison.json")
    request = AnalysisRequest.model_validate(json.loads(path.read_bytes())["request"])
    report = analyze(request)
    validate_report(request, report)
    rec = next(
        row for row in report.recommendations if row.symbol == f"tests/test_bump.py::{SYMBOL}"
    )
    assert rec.evidence_path == [
        f"tests/test_bump.py::{SYMBOL}",
        "src/semver/version.py::_comparator.wrapper",
    ]
    assert rec.path_revision == "both"


def test_successor_preserves_frozen_results_and_checks_evidence_drift(monkeypatch):
    report = evaluate_equality(DIRECTORY)
    assert report["evaluation"]["regressions"] == []
    assert report["summary"]["selected_count"] == 104
    assert report["delta"]["semver_subclass_comparison"]["removed"] == []
    assert sorted(report["delta"]["semver_subclass_comparison"]["added"]) == [
        "tests/test_bump.py::test_should_versioninfo_bump_major_and_minor",
        "tests/test_bump.py::test_should_versioninfo_bump_minor_and_patch",
    ]

    from codeimpact import equality_evaluate

    def altered_report(directory, *, equality):
        result = equality_evaluate_collect(directory, equality=equality)
        item = next(
            row
            for row in result["evaluation"]["cases"]
            if row["case"]["id"] == "semver_subclass_comparison"
        )
        rec = next(row for row in item["analysis"]["recommendations"] if SYMBOL in row["symbol"])
        rec["path_revision"] = "before"
        return result

    equality_evaluate_collect = equality_evaluate.collect
    monkeypatch.setattr(equality_evaluate, "collect", altered_report)
    assert evaluate_equality(DIRECTORY)["evaluation"]["regressions"] == [
        "Exact equality report differs from the successor receipt"
    ]


# Synthetic source only. Different identifiers keep the proof independent of the corpus.
FACTORY = "import re\n" + CORE.replace(
    "    def bump(self):",
    """    digits = re.compile(r"(\\d+)")

    @staticmethod
    def advance(text):
        match = Item.digits.search(text)
        if match:
            digit = str(int(match.group(1)) + 1)
            start, end = match.span(1)
            text = text[:max(start, end - len(digit))] + digit + text[end:]
        return text

    def bump(self):""",
).replace("return cls(self._value + 1)", 'return cls(cls.advance("tag.1"))')


def test_static_scalar_helper_preserves_exact_factory_class():
    req = request_for(base_core=FACTORY)
    report = analyze(req)
    validate_report(req, report)
    (edge,) = equality_edges(report)
    assert (edge.source, edge.target, edge.revision) == (TEST, WRAPPER, "both")
    assert edge.before == edge.after
    assert edge.before[0].location.line == 6
    assert edge.before[0].target_location.line == 5
    rec = next(r for r in report.recommendations if r.symbol == TEST)
    assert (rec.evidence_path, rec.path_revision) == ([TEST, WRAPPER], "both")


@pytest.mark.parametrize(
    "source",
    [
        FACTORY.replace("return cls(cls.advance", "return Other(cls.advance")
        + "\nclass Other: pass\n",
        FACTORY + "\nItem.advance = replacement\n",
        FACTORY.replace("@staticmethod", "@classmethod"),
        FACTORY.replace('cls.advance("tag.1")', 'lookup().advance("tag.1")'),
        FACTORY.replace("return text", "return opaque(text)"),
        FACTORY.replace("return text", "return Item(text)"),
        FACTORY.replace("match.span(1)", "external.span(1)"),
        FACTORY.replace(
            "        match = Item", "        len = user_callback\n        match = Item"
        ),
        FACTORY.replace("import re\n", "import re\nfrom functools import partial as max\n"),
        FACTORY.replace("    digits =", "    def advance(self): pass\n    digits ="),
    ],
)
def test_ambiguous_factory_or_helper_has_no_operator_evidence(source):
    report = analyze(request_for(base_core=source))
    assert not equality_edges(report)


def test_subclass_overriding_scalar_helper_has_no_operator_evidence():
    req = request_for(TESTS.replace('parse("1")', 'Child("1")'), base_core=FACTORY)
    for snap in (req.base, req.head):
        snap.files["tests/test_item.py"] += (
            "\nclass Child(Item):\n    def advance(self, text): return unknown(text)\n"
        )
    assert not equality_edges(analyze(req))


@pytest.mark.parametrize("supported", ["before", "after"])
def test_factory_helper_proof_uses_only_the_supported_revision(supported):
    opaque = FACTORY.replace("return text", "return unknown(text)")
    base, head = (FACTORY, opaque) if supported == "before" else (opaque, FACTORY)
    req = request_for(base_core=base, head_core=head.replace("and True", "and False"))
    report = analyze(req)
    validate_report(req, report)
    (edge,) = equality_edges(report)
    assert (edge.source, edge.target, edge.revision) == (TEST, WRAPPER, supported)
    assert bool(edge.before) == (supported == "before")
    assert bool(edge.after) == (supported == "after")
    rec = next(r for r in report.recommendations if r.symbol == TEST)
    assert (rec.evidence_path, rec.path_revision) == ([TEST, WRAPPER], supported)


def test_pinned_factory_successor_keeps_evidence_and_rejects_drift(monkeypatch):
    from codeimpact import equality_evaluate, factory_evaluate

    baseline = evaluate_equality(DIRECTORY)
    monkeypatch.setattr(factory_evaluate, "evaluate_equality", lambda _: baseline)
    report = factory_evaluate.evaluate_factories(DIRECTORY)
    assert report["evaluation"]["regressions"] == []
    added = report["delta"]["semver_subclass_comparison"]["added"]
    assert len(added) == 8
    sid = "tests/test_bump.py::test_should_versioninfo_bump_prerelease_with_none"
    rec = added[sid]
    assert rec["evidence_path"] == [sid, "src/semver/version.py::_comparator.wrapper"]
    assert rec["path_revision"] == "both"
    case = next(
        c for c in report["evaluation"]["cases"] if c["case"]["id"] == "semver_subclass_comparison"
    )
    edge = next(e for e in case["analysis"]["edges"] if e["id"] == rec["evidence_edges"][0])
    assert edge["before"] == edge["after"]
    assert edge["before"][0]["location"]["line"] == 78

    original = equality_evaluate.collect

    def drift(directory, *, equality):
        altered = original(directory, equality=equality)
        item = next(
            c
            for c in altered["evaluation"]["cases"]
            if c["case"]["id"] == "semver_subclass_comparison"
        )
        next(e for e in item["analysis"]["edges"] if e["id"] == edge["id"])["before"].clear()
        return altered

    monkeypatch.setattr(equality_evaluate, "collect", drift)
    assert factory_evaluate.evaluate_factories(DIRECTORY)["evaluation"]["regressions"] == [
        "Class-preserving factory report differs from the successor receipt"
    ]


def test_helper_budget_cannot_displace_a_later_existing_equality(monkeypatch):
    from codeimpact import equality
    from codeimpact.analyzer import build_index

    source = TESTS + "\ndef test_z():\n    assert Item(1) == Item(2)\n"
    req = request_for(source, base_core=FACTORY)
    # Give the extended pass exactly the budget used by the original pass.
    original_tick = equality.Proof.tick
    steps = []

    def count(proof):
        original_tick(proof)
        steps.append(proof.steps)

    with monkeypatch.context() as measure:
        measure.setattr(equality.Proof, "tick", count)
        build_index(req.base, equality="exact-class")
    monkeypatch.setattr(equality, "MAX_PROOF_STEPS", max(steps))
    report = analyze(req)
    validate_report(req, report)
    assert ("tests/test_item.py::test_z", WRAPPER, "both") in {
        (edge.source, edge.target, edge.revision) for edge in equality_edges(report)
    }
