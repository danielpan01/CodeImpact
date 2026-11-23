"""Exercise fixture recognition using snapshot strings only."""

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest

TEST = "tests/test_fixture.py::test_quote"
FIXTURE = "tests/conftest.py::quoted"
CHANGED = "core.py::price"
TEST_SOURCE = "def test_quote(quoted):\n    assert quoted == 1\n\ndef test_control():\n    pass\n"
CONFTEST = (
    "import pytest\nfrom core import price\n\n@pytest.fixture\ndef quoted():\n    return price()\n"
)


def request_for(test=TEST_SOURCE, conftest=CONFTEST, head_conftest=None, extra=None):
    base = {"tests/test_fixture.py": test, "tests/conftest.py": conftest, **(extra or {})}
    head = {**base, "core.py": "def price():\n    return 2\n"}
    if head_conftest is not None:
        head["tests/conftest.py"] = head_conftest
    return AnalysisRequest.model_validate(
        {
            "base": {"files": {**base, "core.py": "def price():\n    return 1\n"}},
            "head": {"files": head},
        }
    )


def test_fixture_path_has_parameter_and_declaration_evidence_in_both_revisions():
    request = request_for(extra={"sibling/test_fixture.py": TEST_SOURCE})
    report = analyze(request)
    validate_report(request, report)
    assert report.schema_version == "2.1"
    (recommendation,) = report.recommendations
    assert recommendation.symbol == TEST
    assert recommendation.evidence_path == [TEST, FIXTURE, CHANGED]
    assert recommendation.reason == "Resolved fixture dependency"
    assert recommendation.path_revision == "both"
    edges = {edge.id: edge for edge in report.edges}
    injected, called = (edges[key] for key in recommendation.evidence_edges)
    assert (injected.kind, called.kind) == ("fixture", "call")
    assert (injected.source, injected.target) == (TEST, FIXTURE)
    assert len(injected.before) == len(injected.after) == 1
    assert injected.before == injected.after
    (evidence,) = injected.after
    assert evidence.location.model_dump() == {
        "path": "tests/test_fixture.py",
        "line": 1,
        "end_line": 1,
    }
    assert evidence.target_location.model_dump() == {
        "path": "tests/conftest.py",
        "line": 4,
        "end_line": 6,
    }


def test_removed_fixture_keeps_before_only_evidence():
    request = request_for(head_conftest="import pytest\n")
    report = analyze(request)
    validate_report(request, report)
    (recommendation,) = report.recommendations
    assert recommendation.evidence_path == [TEST, FIXTURE]
    assert recommendation.path_revision == "before"
    assert FIXTURE in report.removed
    (edge,) = [edge for edge in report.edges if edge.kind == "fixture"]
    assert edge.revision == "before"
    assert edge.before and not edge.after


def test_head_only_registration_does_not_fabricate_before_evidence():
    request = request_for(
        conftest=CONFTEST.replace("@pytest.fixture\n", ""), head_conftest=CONFTEST
    )
    report = analyze(request)
    validate_report(request, report)
    (recommendation,) = report.recommendations
    assert recommendation.evidence_path == [TEST, FIXTURE]
    assert recommendation.path_revision == "after"


@pytest.mark.parametrize(
    ("test", "conftest", "extra"),
    [
        (TEST_SOURCE, CONFTEST, {"src/pytest/__init__.py": ""}),
        (TEST_SOURCE, CONFTEST + "\npytest.fixture = replacement\n", {}),
        (TEST_SOURCE, CONFTEST.replace("import pytest", "import framework as pytest"), {}),
        (TEST_SOURCE, CONFTEST + "\n" + CONFTEST[CONFTEST.index("@pytest") :], {}),
        (TEST_SOURCE, CONFTEST + "\n@pytest.fixture(name='quoted')\ndef renamed(): pass\n", {}),
        (TEST_SOURCE + "\nimport conftest\nquoted = conftest.quoted\n", CONFTEST, {}),
        (TEST_SOURCE + "\ndef pytest_generate_tests(metafunc): pass\n", CONFTEST, {}),
        (TEST_SOURCE, CONFTEST, {"conftest.py": "def pytest_generate_tests(metafunc): pass\n"}),
        (TEST_SOURCE, CONFTEST, {"tests/__init__.py": "def broken("}),
        (
            TEST_SOURCE,
            CONFTEST.replace("from core import price", "import opaque"),
            {
                "opaque.py": "def broken(",
            },
        ),
        (TEST_SOURCE, CONFTEST.replace("@pytest.fixture", "@pytest.fixture(params=[1])"), {}),
        (
            "import pytest\n@pytest.mark.parametrize('quoted', [1])\n" + TEST_SOURCE,
            CONFTEST,
            {},
        ),
        (TEST_SOURCE.replace("quoted):", "quoted=1):"), CONFTEST, {}),
        (TEST_SOURCE.replace("quoted):", "quoted, other):"), CONFTEST, {}),
        (TEST_SOURCE, CONFTEST.replace("return price()", "yield price()"), {}),
        (TEST_SOURCE.replace("quoted", "request"), CONFTEST.replace("quoted", "request"), {}),
    ],
)
def test_ambiguous_or_unsupported_registration_does_not_create_an_edge(test, conftest, extra):
    request = request_for(test, conftest, extra=extra)
    report = analyze(request)
    validate_report(request, report)
    assert all(edge.kind != "fixture" for edge in report.edges)
    assert all(rec.reason != "Resolved fixture dependency" for rec in report.recommendations)


def test_independent_call_path_keeps_its_existing_score_and_evidence():
    request = request_for(
        test="from core import price\n\n"
        + TEST_SOURCE.replace("assert quoted == 1", "assert price() == quoted")
    )
    previous = analyze(request, fixtures=False)
    current = analyze(request)
    validate_report(request, current)
    assert current.recommendations == previous.recommendations
    assert current.recommendations[0].evidence_path == [TEST, CHANGED]
    assert current.recommendations[0].reason == "Resolved call path"


def test_fixture_path_does_not_join_a_before_call_to_an_after_call():
    request = request_for(
        head_conftest=CONFTEST.replace("from core import price", "from quiet import price"),
        conftest=CONFTEST.replace("from core import price", "from helper import price"),
        extra={
            "helper.py": "from quiet import value\n\ndef price():\n    return value()\n",
            "quiet.py": "def price():\n    return 1\n\ndef value():\n    return 1\n",
        },
    )
    request.head.files["helper.py"] = request.head.files["helper.py"].replace(
        "from quiet import value", "from core import price as value"
    )
    report = analyze(request)
    validate_report(request, report)
    assert any(edge.kind == "fixture" and edge.revision == "both" for edge in report.edges)
    assert any(
        edge.kind == "call"
        and edge.source == FIXTURE
        and edge.target == "helper.py::price"
        and edge.revision == "before"
        for edge in report.edges
    )
    assert any(
        edge.kind == "call"
        and edge.source == "helper.py::price"
        and edge.target == CHANGED
        and edge.revision == "after"
        for edge in report.edges
    )
    assert all(rec.reason != "Resolved fixture dependency" for rec in report.recommendations)
