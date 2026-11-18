"""Package export refinements use synthetic source without running it."""

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot

PACKAGE = "from .api import parse, ParseError\n__all__ = ['parse', 'ParseError']\n"
PACKAGE_HEAD = (
    "from .api import parse, ParseError, validate\n__all__ = ['parse', 'validate' 'ParseError']\n"
)
API = "class ParseError(ValueError): pass\ndef parse(text): return int(text)\n"
ADDITION = "\ndef validate(text: str) -> bool: return bool(text)\n"
NAMED = "from pkg import parse\ndef test_parse(): assert parse('1') == 1\n"
QUALIFIED = "import pkg\ndef test_parse(): assert pkg.parse('1') == 1\n"
CHILD = "from pkg import api\ndef test_parse(): assert api.parse('1') == 1\n"


def review(
    tests=QUALIFIED,
    *,
    head_test=None,
    api=API,
    addition=ADDITION,
    package=PACKAGE_HEAD,
    extra=None,
    head_extra=None,
):
    before = {"pkg/__init__.py": PACKAGE, "pkg/api.py": api, "test_api.py": tests, **(extra or {})}
    after = before | {"pkg/__init__.py": package, "pkg/api.py": api + addition} | (head_extra or {})
    if head_test is not None:
        after["test_api.py"] = head_test
    request = AnalysisRequest(base=Snapshot(files=before), head=Snapshot(files=after))
    report = analyze(request)
    validate_report(request, report)
    return report


def recommendations(report):
    return {r.symbol: r for r in report.recommendations}


@pytest.mark.parametrize("test_source", [NAMED, QUALIFIED, CHILD])
def test_old_named_member_survives_addition_without_fallback(test_source):
    assert not recommendations(review(test_source))


def test_changed_and_direct_validator_tests_are_retained():
    direct = "from pkg.api import validate\ndef test_validate(): assert validate('1')\n"
    source = "from pkg import api\ndef test_changed(): assert api.parse('1') == 1\n"
    result = recommendations(
        review(
            source,
            head_test=source.replace("'1'", "'2'"),
            extra={
                "test_direct.py": direct,
            },
        )
    )
    assert result["test_api.py::test_changed"].reason == "Test itself changed"
    direct_rec = result["test_direct.py::test_validate"]
    assert direct_rec.reason == "Resolved call path"
    assert direct_rec.evidence_path[-1] == "pkg/api.py::validate"


def test_alternative_changed_dependency_keeps_exact_evidence():
    source = QUALIFIED.replace("def test_parse", "from other import helper\ndef test_parse")
    source = source.replace("assert pkg.parse('1') == 1", "assert pkg.parse('1') == helper()")
    result = recommendations(
        review(
            source,
            extra={"other.py": "def helper(): return 1"},
            head_extra={"other.py": "def helper(): return 2"},
        )
    )
    assert result["test_api.py::test_parse"].evidence_path == [
        "test_api.py::test_parse",
        "other.py::helper",
    ]


@pytest.mark.parametrize(
    "tests",
    [
        "from pkg import *\ndef test_parse(): assert parse('1') == 1\n",
        "import pkg\ndef test_parse(): assert 'ParseError' in pkg.__all__\n",
        "import pkg\ndef test_parse(): assert getattr(pkg, 'parse')('1') == 1\n",
        "import pkg\ndef test_parse(): assert vars(pkg)['parse']('1') == 1\n",
        "import pkg\ndef test_parse(): consume(pkg)\n",
        "import pkg\n@unknown\ndef test_parse(): assert pkg.parse('1') == 1\n",
        "import pkg\ndef setup_function(): touch(pkg)\n"
        "def test_parse(): assert pkg.parse('1') == 1\n",
        "import pkg\ndef test_parse(fixture): assert pkg.parse('1') == fixture\n",
        QUALIFIED + "@unknown\ndef test_other(): pass\n",
        "import pkg\npkg = proxy(pkg)\ndef test_parse(): assert pkg.parse('1') == 1\n",
    ],
)
def test_ambiguous_consumers_keep_conservative_evidence(tests):
    assert recommendations(review(tests))["test_api.py::test_parse"].reason.startswith(
        "Conservative"
    )


@pytest.mark.parametrize(
    "addition",
    [
        "\ndef validate(text=initialize()): return bool(text)\n",
        "\n@register\ndef validate(text): return bool(text)\n",
        "\ndef validate(text: annotation()): return bool(text)\n",
    ],
)
def test_added_eager_effects_keep_fallback(addition):
    assert "test_api.py::test_parse" in recommendations(review(addition=addition))


def test_ambiguous_reexport_keeps_fallback():
    result = review(package=PACKAGE_HEAD + "from .api import validate as parse\n")
    assert "test_api.py::test_parse" in recommendations(result)


def test_existing_initialization_that_observes_namespace_keeps_fallback():
    result = review(api=API + "\nregistry = globals()\n")
    assert "test_api.py::test_parse" in recommendations(result)


def test_captured_conftest_keeps_fallback():
    result = review(extra={"conftest.py": "import pkg\ndef pytest_configure(): touch(pkg)\n"})
    assert "test_api.py::test_parse" in recommendations(result)


def test_calling_an_uninspected_sibling_test_keeps_fallback():
    source = QUALIFIED.replace("assert pkg.parse('1') == 1", "test_other()")
    source += "def test_other(): assert getattr(pkg, 'validate')('1')\n"
    assert "test_api.py::test_parse" in recommendations(review(source))


def test_added_binding_cannot_shadow_a_builtin_used_in_old_code():
    result = review(
        addition=ADDITION.replace("def validate", "def int"),
        package=PACKAGE_HEAD.replace("Error, validate", "Error, int"),
    )
    assert "test_api.py::test_parse" in recommendations(result)


def test_proof_declines_a_before_only_dynamic_observer():
    base = QUALIFIED + "def test_observer(): assert vars(pkg)['parse']('1') == 1\n"
    head = base.replace("vars(pkg)['parse']", "pkg.parse")
    # The changed observer keeps its own path. The unchanged plain test can
    # still shed its package path because sibling bodies are deferred.
    result = recommendations(review(base, head_test=head))
    assert set(result) == {"test_api.py::test_observer"}
    assert result["test_api.py::test_observer"].path_revision == "both"


def test_budget_exhaustion_retains_original_evidence(monkeypatch):
    from codeimpact import additive_exports

    monkeypatch.setattr(additive_exports, "MAX_NODES", 2)
    assert "test_api.py::test_parse" in recommendations(review())
