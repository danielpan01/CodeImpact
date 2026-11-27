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


def test_first_assertion_uses_the_established_operands_and_exact_line():
    source = TESTS + "    right = opaque()\n    assert left == right\n"
    request = request_for(source)
    # The same expression can have different before/after source locations.
    request.head.files["tests/test_item.py"] = "\n" + source
    report = analyze(request)
    validate_report(request, report)
    (edge,) = equality_edges(report)
    assert (edge.source, edge.target, edge.revision) == (TEST, WRAPPER, "both")
    assert [ev.location.line for ev in edge.before] == [6]
    assert [ev.location.line for ev in edge.after] == [7]
    rec = next(r for r in report.recommendations if r.symbol == TEST)
    assert rec.evidence_path == [TEST, WRAPPER]
    assert rec.evidence_edges == [edge.id]


@pytest.mark.parametrize(
    "suffix", ["return", "opaque()", "def helper(parse):\n        return parse"]
)
def test_first_equality_can_precede_unrelated_statements(suffix):
    report = analyze(request_for(TESTS + "    " + suffix + "\n"))
    (edge,) = equality_edges(report)
    assert [e.location.line for e in edge.before] == [6]


@pytest.mark.parametrize(
    "suffix",
    [
        "parse = Item.parse",
        "parse: object",
        "del parse",
        "from values import parse",
        "if False:\n        parse = Item.parse",
        "try:\n        pass\n    except Exception as parse:\n        pass",
        "match 1:\n        case parse:\n            pass",
        "[(parse := x) for x in ()]",
        "yield 1",
        "yield from ()",
    ],
)
def test_function_wide_binding_or_generator_blocks_first_equality(suffix):
    assert not equality_edges(analyze(request_for(TESTS + "    " + suffix + "\n")))


@pytest.mark.parametrize(
    "statements",
    [
        "return\n    assert left == right",
        "if True:\n        return\n    assert left == right",
        "if True:\n        assert left == right",
        "right = unknown()\n    assert left == right",
        "right = 1\n    assert left == right",
        "assert unknown() == right\n    assert left == right",
        "assert False\n    assert left == right",
    ],
)
def test_unproved_prefix_or_first_assertion_declines(statements):
    source = TESTS.replace("assert left.bump() == right", statements) + "    opaque()\n"
    assert not equality_edges(analyze(request_for(source)))


@pytest.mark.parametrize("side", ["before", "after"])
def test_first_assertion_can_supply_only_one_revision(side):
    # Keep the test source identical across revisions so its own edit cannot take precedence.
    req = request_for(TESTS + "    right = unknown()\n")
    unsupported = req.head if side == "before" else req.base
    unsupported.files[SOURCE] = unsupported.files[SOURCE].replace(
        "return cls(int(value))", "return unknown(value)"
    )
    report = analyze(req)
    validate_report(req, report)
    (edge,) = equality_edges(report)
    assert edge.revision == side
    assert [e.location.line for e in edge.before] == ([6] if side == "before" else [])
    assert [e.location.line for e in edge.after] == ([6] if side == "after" else [])
    rec = next(r for r in report.recommendations if r.symbol == TEST)
    assert (rec.path_revision, rec.evidence_edges) == (side, [edge.id])


def test_pinned_first_comparison_uses_line_64_only():
    case = Path("datasets/real-v5/cases/semver_subclass_comparison.json")
    request = AnalysisRequest.model_validate(json.loads(case.read_bytes())["request"])
    report = analyze(request)
    validate_report(request, report)
    sid = "tests/test_bump.py::test_should_versioninfo_bump_multiple"
    rec = next(r for r in report.recommendations if r.symbol == sid)
    assert rec.path_revision == "both"
    assert rec.evidence_path == [sid, "src/semver/version.py::_comparator.wrapper"]
    (edge,) = [e for e in report.edges if e.id in rec.evidence_edges]
    for evidence in (edge.before, edge.after):
        (site,) = evidence
        assert (site.location.line, site.location.end_line) == (64, 64)
        assert (site.target_location.line, site.target_location.end_line) == (41, 52)


def test_current_successor_pins_both_first_comparison_locations(monkeypatch):
    from codeimpact import equality_evaluate, first_assertion_evaluate

    predecessor = first_assertion_evaluate.evaluate_factories(DIRECTORY)
    monkeypatch.setattr(first_assertion_evaluate, "evaluate_factories", lambda _: predecessor)
    result = first_assertion_evaluate.evaluate_first_assertion(DIRECTORY)
    assert result["evaluation"]["regressions"] == []
    case = "semver_subclass_comparison"
    delta = result["delta"][case]
    assert delta["changed"] == {} and delta["removed"] == []
    sites = {
        "tests/test_bump.py::test_should_versioninfo_bump_multiple": 64,
        "tests/test_parsing.py::test_equal_versions_have_equal_hashes": 155,
    }
    assert delta["added"].keys() == sites.keys()
    analysis = next(c["analysis"] for c in result["evaluation"]["cases"] if c["case"]["id"] == case)
    edges = {e["id"]: e for e in analysis["edges"]}
    for sid, line in sites.items():
        edge = edges[delta["added"][sid]["evidence_edges"][0]]
        for side in ("before", "after"):
            assert [ev["location"]["line"] for ev in edge[side]] == [line]

    collect = equality_evaluate.collect

    def wrong_line(directory, *, equality):
        report = collect(directory, equality=equality)
        case_data = next(
            c["analysis"] for c in report["evaluation"]["cases"] if c["case"]["id"] == case
        )
        first = next(e for e in case_data["edges"] if e["id"] == edge["id"])
        first["before"][0]["location"]["line"] += 1
        return report

    monkeypatch.setattr(equality_evaluate, "collect", wrong_line)
    assert first_assertion_evaluate.evaluate_first_assertion(DIRECTORY)["evaluation"][
        "regressions"
    ] == ["First equality assertion report differs from the successor receipt"]


def test_first_assertion_budget_preserves_previously_proved_factory(monkeypatch):
    from codeimpact import equality
    from codeimpact.analyzer import build_index

    earlier = TESTS.replace("def test_equal()", "def test_earlier()") + "    opaque()\n"
    req = request_for(earlier + "\n" + TESTS.split("\n", 1)[1], base_core=FACTORY)
    steps = []
    tick = equality.Proof.tick

    def count(proof):
        tick(proof)
        steps.append(proof.steps)

    with monkeypatch.context() as measure:
        measure.setattr(equality.Proof, "tick", count)
        build_index(req.base, equality="factories")
    monkeypatch.setattr(equality, "MAX_PROOF_STEPS", max(steps))
    report = analyze(req)
    validate_report(req, report)
    assert (TEST, WRAPPER, "both") in {
        (e.source, e.target, e.revision) for e in equality_edges(report)
    }


ORDERED_CORE = CORE.replace("def __eq__", "def __lt__").replace(
    "return self._value == rhs._value",
    """return self._value < rhs._value

    def __gt__(self, rhs):
        return self._value > rhs._value""",
)
ORDERED_TEST = (
    TESTS.replace("assert left.bump() == right", "assert left < right") + "    opaque()\n"
)


def less_than_edges(report):
    return [
        edge
        for edge in report.edges
        if any("via < " in entry.text for entry in edge.before + edge.after)
    ]


def test_less_than_uses_first_assertion_and_bound_wrapper():
    request = request_for(ORDERED_TEST, base_core=ORDERED_CORE)
    report = analyze(request)
    validate_report(request, report)
    (edge,) = less_than_edges(report)
    assert (edge.source, edge.target, edge.kind, edge.revision) == (TEST, WRAPPER, "call", "both")
    assert [entry.location.line for entry in edge.before] == [6]
    assert edge.before == edge.after
    rec = next(r for r in report.recommendations if r.symbol == TEST)
    assert (rec.evidence_path, rec.evidence_edges, rec.path_revision) == (
        [TEST, WRAPPER],
        [edge.id],
        "both",
    )


def test_less_than_proves_first_call_even_if_it_returns_not_implemented():
    source = ORDERED_CORE.replace("    @checked\n", "").replace(
        "return self._value < rhs._value", "return NotImplemented"
    )
    head = source.replace("return NotImplemented", "return NotImplemented if True else False")
    head = head.replace("return self._value > rhs._value", "return True")
    request = request_for(ORDERED_TEST, base_core=source, head_core=head)
    report = analyze(request)
    validate_report(request, report)
    (edge,) = less_than_edges(report)
    assert edge.target == f"{SOURCE}::Item.__lt__"
    assert edge.revision == "both"


@pytest.mark.parametrize(
    "assertion",
    [
        "assert left < Item(2) < Item(3)",
        "assert left < unknown()",
        "assert left < 1",
        "assert left < Other()",
        "assert left < Child(2)",
        "assert Child(1) < right",
        "assert left < right or False",
        "if True:\n        assert left < right",
        "if False:\n        return\n    assert left < right",
        "assert False\n    assert left < right",
    ],
)
def test_less_than_declines_unproved_dispatch_or_assertion(assertion):
    source = ORDERED_TEST.replace("assert left < right", assertion)
    if "Other" in assertion:
        source += "\nclass Other: pass\n"
    if "Child" in assertion:
        source += "\nclass Child(Item):\n    def __gt__(self, other): return True\n"
    assert not less_than_edges(analyze(request_for(source, base_core=ORDERED_CORE)))


@pytest.mark.parametrize(
    "source",
    [
        ORDERED_CORE + "\nItem.__lt__ = replacement\n",
        ORDERED_CORE.replace("@checked", "@unknown"),
        ORDERED_CORE.replace("@checked", "@property"),
        ORDERED_CORE.replace("@checked", "@staticmethod"),
        ORDERED_CORE.replace("def __lt__", "def another_method"),
        ORDERED_CORE.replace("def wrapper(self, other):", "def wrapper(self):"),
    ],
)
def test_less_than_declines_ambiguous_or_unsupported_method(source):
    assert not less_than_edges(analyze(request_for(ORDERED_TEST, base_core=source)))


@pytest.mark.parametrize("side", ["before", "after"])
def test_less_than_evidence_is_revision_specific(side):
    before = ORDERED_CORE if side == "before" else ORDERED_CORE.replace("def __lt__", "def other")
    head = ORDERED_CORE if side == "after" else ORDERED_CORE.replace("def __lt__", "def other")
    request = request_for(
        ORDERED_TEST, base_core=before, head_core=head.replace("and True", "and False")
    )
    report = analyze(request)
    validate_report(request, report)
    (edge,) = less_than_edges(report)
    assert (edge.target, edge.revision) == (WRAPPER, side)
    assert [e.location.line for e in edge.before] == ([6] if side == "before" else [])
    assert [e.location.line for e in edge.after] == ([6] if side == "after" else [])
    rec = next(r for r in report.recommendations if r.symbol == TEST)
    assert (rec.evidence_edges, rec.path_revision) == ([edge.id], side)


def test_pinned_less_than_uses_line_129_and_the_changed_wrapper():
    case = Path("datasets/real-v5/cases/semver_subclass_comparison.json")
    request = AnalysisRequest.model_validate(json.loads(case.read_bytes())["request"])
    report = analyze(request)
    validate_report(request, report)
    sid = "tests/test_compare.py::test_should_compare_prerelease_with_numbers_and_letters"
    rec = next(r for r in report.recommendations if r.symbol == sid)
    assert rec.evidence_path == [sid, "src/semver/version.py::_comparator.wrapper"]
    assert rec.path_revision == "both"
    (edge,) = [e for e in less_than_edges(report) if e.id in rec.evidence_edges]
    for evidence in (edge.before, edge.after):
        (site,) = evidence
        assert (site.location.line, site.location.end_line) == (129, 129)
        assert (site.target_location.line, site.target_location.end_line) == (41, 52)


def test_less_than_budget_preserves_previously_proved_first_equality(monkeypatch):
    from codeimpact import equality
    from codeimpact.analyzer import build_index

    ordered_core = ORDERED_CORE.replace(
        "\ndef parse(value):",
        "\n    def __eq__(self, rhs): return True\n\ndef parse(value):",
    )
    # Put distinct tests in the same module so they share a proof budget.
    source = ORDERED_TEST.replace("def test_equal()", "def test_earlier()")
    source += "\ndef test_equal():\n    assert Item(1) == Item(2)\n    opaque()\n"
    request = request_for(source, base_core=ordered_core)
    steps = []
    tick = equality.Proof.tick

    def count(proof):
        tick(proof)
        steps.append(proof.steps)

    with monkeypatch.context() as measure:
        measure.setattr(equality.Proof, "tick", count)
        build_index(request.base, equality="first-assertion")
    monkeypatch.setattr(equality, "MAX_PROOF_STEPS", max(steps))
    report = analyze(request)
    validate_report(request, report)
    (edge,) = equality_edges(report)
    assert (edge.source, edge.target, edge.revision) == (TEST, f"{SOURCE}::Item.__eq__", "both")


INEQUALITY_CORE = CORE.replace("def __eq__", "def __ne__").replace(
    "return self._value == rhs._value", "return self._value != rhs._value"
)
INEQUALITY_TEST = TESTS.replace("== right", "!= right") + "    opaque()\n"


def inequality_edges(report):
    return [
        edge
        for edge in report.edges
        if any("via != " in entry.text for entry in edge.before + edge.after)
    ]


def test_inequality_resolves_the_first_assertion_and_records_both_ranges():
    request = request_for(INEQUALITY_TEST, base_core=INEQUALITY_CORE)
    request.head.files["tests/test_item.py"] = "\n" + INEQUALITY_TEST
    report = analyze(request)
    validate_report(request, report)
    (edge,) = inequality_edges(report)
    assert (edge.source, edge.target, edge.kind, edge.revision) == (TEST, WRAPPER, "call", "both")
    for entries, line in [(edge.before, 6), (edge.after, 7)]:
        (entry,) = entries
        assert (entry.location.line, entry.location.end_line) == (line, line)
        assert entry.target_location.line == 4
    rec = next(r for r in report.recommendations if r.symbol == TEST)
    assert (rec.evidence_path, rec.evidence_edges, rec.path_revision) == (
        [TEST, WRAPPER],
        [edge.id],
        "both",
    )


def test_inequality_only_records_initial_dispatch_when_ne_returns_not_implemented():
    base = CORE.replace(
        "    @checked\n",
        "    def __ne__(self, rhs):\n        return NotImplemented\n\n    @checked\n",
    )
    head = base.replace("return NotImplemented", "return NotImplemented if True else False")
    request = request_for(INEQUALITY_TEST, base_core=base, head_core=head)
    report = analyze(request)
    validate_report(request, report)
    (edge,) = inequality_edges(report)
    assert (edge.target, edge.revision) == (f"{SOURCE}::Item.__ne__", "both")
    assert len(edge.before) == len(edge.after) == 1


@pytest.mark.parametrize(
    "source",
    [
        CORE,  # Equality alone does not establish an explicit inequality binding.
        INEQUALITY_CORE + "\nItem.__ne__ = lambda self, rhs: True\n",
        INEQUALITY_CORE.replace("@checked", "@unknown"),
        INEQUALITY_CORE.replace("@checked", "@property"),
    ],
)
def test_inequality_declines_missing_rebound_or_unsupported_ne(source):
    assert not inequality_edges(analyze(request_for(INEQUALITY_TEST, base_core=source)))


@pytest.mark.parametrize(
    "tests",
    [
        INEQUALITY_TEST.replace("!= right", "!= unknown()"),
        INEQUALITY_TEST.replace("!= right", "!= 2"),
        INEQUALITY_TEST.replace("!= right", "!= Other()") + "\nclass Other: pass\n",
        INEQUALITY_TEST.replace("!= right", "!= Item(2) != Item(3)"),
        INEQUALITY_TEST + "    parse = Item.parse\n",
        INEQUALITY_TEST.replace('left = parse("1")', "left = Item(1)") + "    Item: type\n",
    ],
)
def test_inequality_declines_unproved_operands_or_scope(tests):
    assert not inequality_edges(analyze(request_for(tests, base_core=INEQUALITY_CORE)))


@pytest.mark.parametrize("side", ["before", "after"])
def test_inequality_evidence_is_revision_specific(side):
    base = INEQUALITY_CORE if side == "before" else CORE
    head = INEQUALITY_CORE if side == "after" else CORE
    request = request_for(
        INEQUALITY_TEST, base_core=base, head_core=head.replace("and True", "and False")
    )
    report = analyze(request)
    validate_report(request, report)
    (edge,) = inequality_edges(report)
    assert (edge.target, edge.revision) == (WRAPPER, side)
    assert [ev.location.line for ev in edge.before] == ([6] if side == "before" else [])
    assert [ev.location.line for ev in edge.after] == ([6] if side == "after" else [])
    rec = next(r for r in report.recommendations if r.symbol == TEST)
    assert (rec.evidence_edges, rec.path_revision) == ([edge.id], side)


def test_pinned_inequality_uses_line_138_and_the_changed_wrapper():
    case = Path("datasets/real-v5/cases/semver_subclass_comparison.json")
    request = AnalysisRequest.model_validate(json.loads(case.read_bytes())["request"])
    report = analyze(request)
    validate_report(request, report)
    sid = "tests/test_compare.py::test_should_compare_version_info_objects"
    rec = next(r for r in report.recommendations if r.symbol == sid)
    assert rec.evidence_path == [sid, "src/semver/version.py::_comparator.wrapper"]
    assert rec.path_revision == "both"
    (edge,) = [e for e in inequality_edges(report) if e.id in rec.evidence_edges]
    for evidence in (edge.before, edge.after):
        (site,) = evidence
        assert (site.location.line, site.location.end_line) == (138, 138)
        assert (site.target_location.line, site.target_location.end_line) == (41, 52)
