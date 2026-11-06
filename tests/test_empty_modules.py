"""Empty modules and parse failures must have distinct change semantics."""

from itertools import pairwise

import pytest

from codeimpact.analyzer import analyze
from codeimpact.models import AnalysisRequest, Report, Snapshot


@pytest.fixture
def unchanged_files():
    return {
        "test_a.py": "import a\ndef test_a(): assert a is not None\n",
        "control.py": "VALUE = 1\n",
        "test_control.py": "import control\ndef test_control(): assert control.VALUE == 1\n",
    }


def compare(base: dict[str, str], head: dict[str, str]) -> Report:
    return analyze(AnalysisRequest(base=Snapshot(files=base), head=Snapshot(files=head)))


def assert_valid_evidence(report: Report) -> None:
    edges = {(edge.source, edge.target) for edge in report.edges}
    for recommendation in report.recommendations:
        path = recommendation.evidence_path
        assert path[0] == recommendation.symbol
        assert path[-1] in report.changed
        assert all((source, target) in edges for source, target in pairwise(path))
        assert recommendation.distance == len(path) - 1
        assert recommendation.symbol not in report.removed


@pytest.mark.parametrize(
    "base_source,head_source,changed,parse_warning",
    [
        pytest.param("", "# comment only\n", False, False, id="empty-to-comment"),
        pytest.param(
            "# original\n",
            "\n  # edited\n\t\n# another comment\n",
            False,
            False,
            id="comment-and-whitespace-edits",
        ),
        pytest.param(
            "# same comment\n",
            "\n\n# same comment\n\n",
            False,
            False,
            id="comment-line-movement",
        ),
        pytest.param("", "VALUE = 1\n", True, False, id="empty-to-executable"),
        pytest.param("VALUE = 1\n", "VALUE =\n", True, True, id="valid-to-invalid"),
        pytest.param("", "VALUE =\n", True, True, id="empty-to-invalid"),
        pytest.param("VALUE =\n", "", True, True, id="invalid-to-empty"),
        pytest.param("VALUE =\n", "# fixed\n", True, True, id="invalid-to-comment"),
        pytest.param("VALUE =\n", "OTHER =\n", True, True, id="distinct-invalid-revisions"),
        pytest.param("VALUE =\n", "VALUE =\n", False, True, id="identical-invalid-revisions"),
    ],
)
def test_module_change_detection(base_source, head_source, changed, parse_warning, unchanged_files):
    report = compare(
        unchanged_files | {"a.py": base_source}, unchanged_files | {"a.py": head_source}
    )

    assert report.changed == (["a.py::<module>"] if changed else [])
    assert report.removed == []
    assert [warning for warning in report.warnings if warning.startswith("Cannot parse")] == (
        ["Cannot parse a.py: SyntaxError"] if parse_warning else []
    )
    # An independent module and its unchanged importing test stay unaffected.
    assert not any("control" in sid for sid in report.changed + report.impacted)
    assert [r.symbol for r in report.recommendations] == (["test_a.py::test_a"] if changed else [])
    if changed:
        assert report.impacted == ["test_a.py::<module>", "test_a.py::test_a"]
        assert report.recommendations[0].reason == "Conservative module/import dependency"
        assert report.recommendations[0].evidence_path == [
            "test_a.py::test_a",
            "test_a.py::<module>",
            "a.py::<module>",
        ]
    else:
        assert report.impacted == []
    assert_valid_evidence(report)


def test_removed_importing_test_is_not_recommended(unchanged_files):
    base = unchanged_files | {
        "a.py": "",
        "test_removed.py": "import a\ndef test_removed(): assert a is not None\n",
    }
    report = compare(base, unchanged_files | {"a.py": "VALUE = 1\n"})

    assert report.changed == [
        "a.py::<module>",
        "test_removed.py::<module>",
        "test_removed.py::test_removed",
    ]
    assert report.removed == ["test_removed.py::<module>", "test_removed.py::test_removed"]
    assert any(edge.source == "test_removed.py::test_removed" for edge in report.edges)
    assert [r.symbol for r in report.recommendations] == ["test_a.py::test_a"]
    assert not any("control" in sid for sid in report.changed + report.impacted)
    assert_valid_evidence(report)
