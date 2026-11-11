"""Revision-aware report contract, using source strings only."""

from itertools import pairwise
from pathlib import Path

import pytest

from codeimpact.analyzer import analyze
from codeimpact.models import AnalysisRequest, Report, Snapshot


def compare(base, head):
    return analyze(AnalysisRequest(base=Snapshot(files=base), head=Snapshot(files=head)))


def assert_typed_paths(report: Report):
    edges = {edge.id: edge for edge in report.edges}
    for item in report.recommendations:
        assert item.evidence_path[0] == item.symbol
        assert item.evidence_path[-1] in report.changed
        assert item.symbol not in report.removed
        assert len(item.evidence_edges) == item.distance == len(item.evidence_path) - 1
        revisions = {"before", "after"}
        for edge_id, (source, target) in zip(
            item.evidence_edges, pairwise(item.evidence_path), strict=True
        ):
            edge = edges[edge_id]
            assert (edge.source, edge.target) == (source, target)
            assert edge.kind in {"call", "module", "import"}
            revisions &= {r for r in ("before", "after") if getattr(edge, r)}
        if item.evidence_edges:
            expected = "both" if len(revisions) == 2 else next(iter(revisions), "mixed")
            assert item.path_revision == expected


def test_changed_ranges_include_decorators_nested_definitions_and_line_movement():
    before = (
        "@decorate\ndef outer():\n    @decorate\n    def inner(): return 1\n    return inner()\n"
    )
    after = "# moved\n\n" + before.replace("return 1", "return 2")
    report = compare({"a.py": before}, {"a.py": after})
    changes = {c.symbol: c for c in report.changes}
    assert report.schema_version == "2.0"
    assert changes["a.py::outer"].status == "modified"
    assert changes["a.py::outer"].before.model_dump() == {"line": 1, "end_line": 5}
    assert changes["a.py::outer"].after.model_dump() == {"line": 3, "end_line": 7}
    assert changes["a.py::outer.inner"].before.line == 3
    assert changes["a.py::outer.inner"].after.line == 5
    assert len(report.source_files) == 1  # no file copies per nested symbol
    assert report.source_files[0].before.text == before
    assert report.source_files[0].after.text == after
    assert not compare({"a.py": before}, {"a.py": "\n# move\n" + before}).changes


@pytest.mark.parametrize("rename_file", [False, True])
def test_added_removed_and_renamed_symbols(rename_file):
    report = compare(
        {"old.py": "def old(): return 1\n"},
        {"new.py" if rename_file else "old.py": "def new(): return 1\n"},
    )
    changes = {c.symbol: c for c in report.changes}
    old, new = changes["old.py::old"], changes[f"{'new' if rename_file else 'old'}.py::new"]
    assert (old.status, old.after) == ("removed", None)
    assert (new.status, new.before) == ("added", None)
    if rename_file:
        files = {f.path: f for f in report.source_files}
        assert files["old.py"].after is None
        assert files["new.py"].before is None


@pytest.mark.parametrize(
    "before,after,status_before,status_after,changed",
    [
        (None, "", None, "parsed", True),
        ("", None, "parsed", None, True),
        ("", "# only a comment\n", "parsed", "parsed", False),
        ("# one\n", "\n# two\n", "parsed", "parsed", False),
        ("", "VALUE = 1\n", "parsed", "parsed", True),
        ("VALUE = 1\n", "VALUE =\n", "parsed", "unparseable", True),
        ("VALUE =\n", "", "unparseable", "parsed", True),
        ("VALUE =\n", "# fixed\n", "unparseable", "parsed", True),
        ("VALUE =\n", "VALUE =\n", "unparseable", "unparseable", False),
    ],
)
def test_file_presence_empty_source_and_parse_transitions(
    before, after, status_before, status_after, changed
):
    report = compare(
        {} if before is None else {"a.py": before},
        {} if after is None else {"a.py": after},
    )
    assert bool(report.changes) == changed
    if changed:
        file = report.source_files[0]
        for side, source, status in [
            (file.before, before, status_before),
            (file.after, after, status_after),
        ]:
            if source is None:
                assert side is None
            else:
                assert side.text == source
                assert side.parse_status == status
    else:
        assert report.source_files == []


def test_before_after_and_shared_edges_keep_all_occurrences_and_locations():
    common = {"a.py": "def f(): return 1\ndef g(): return 2\n"}
    report = compare(
        common | {"test_a.py": "from a import f, g\ndef test_a():\n    f()\n    f()\n"},
        common | {"test_a.py": "\nfrom a import f, g\ndef test_a():\n    f()\n    f()\n    g()\n"},
    )
    edge = next(e for e in report.edges if e.kind == "call" and e.target == "a.py::f")
    assert edge.revision == "both"
    assert [e.location.line for e in edge.before] == [3, 4]
    assert [e.location.line for e in edge.after] == [4, 5]
    assert edge.before[0].text == "test_a.py:3 calls f"
    assert edge.after[0].text == "test_a.py:4 calls f"
    assert edge.before[0].target_location.path == "a.py"
    assert edge.before[0].target_location.line == 1
    added = next(e for e in report.edges if e.kind == "call" and e.target == "a.py::g")
    assert (added.revision, added.before) == ("after", [])
    deleted = compare(
        {"a.py": common["a.py"], "test_a.py": "from a import f\ndef test_a(): return f()"},
        {"a.py": "", "test_a.py": "from a import f\ndef test_a(): return f()"},
    )
    old = next(e for e in deleted.edges if e.kind == "call")
    assert (old.revision, old.after) == ("before", [])
    assert deleted.recommendations[0].path_revision == "before"
    assert_typed_paths(report)
    assert_typed_paths(deleted)


def mixed_snapshots():
    request = AnalysisRequest.model_validate_json(
        (Path(__file__).parent / "fixtures/mixed-revisions.json").read_text()
    )
    return request.base.files, request.head.files


def test_mixed_revision_path_is_labeled_without_changing_call_preference():
    report = compare(*mixed_snapshots())
    item = report.recommendations[0]
    assert item.evidence_path == ["test_bridge.py::test_g", "bridge.py::g", "a.py::f"]
    assert item.path_revision == "mixed"
    assert item.reason == "Resolved call path"
    assert_typed_paths(report)


def test_module_fallback_control_determinism_and_removed_tests():
    base = {
        "a.py": "VALUE = 1\n",
        "test_a.py": "import a\nimport a\ndef test_a(): return a.VALUE\n",
        "test_removed.py": "import a\ndef test_removed(): return a.VALUE\n",
        "control.py": "def f(): return 5\n",
        "test_control.py": "from control import f\ndef test_control(): return f()\n",
    }
    head = {k: v for k, v in base.items() if k != "test_removed.py"} | {"a.py": "VALUE = 2\n"}
    report = compare(base, head)
    assert [r.symbol for r in report.recommendations] == ["test_a.py::test_a"]
    item = report.recommendations[0]
    assert item.reason.startswith("Conservative")
    assert item.path_revision == "both"
    assert_typed_paths(report)
    edges = {e.id: e for e in report.edges}
    assert [edges[e].kind for e in item.evidence_edges] == ["module", "import"]
    assert [e.location.line for e in edges[item.evidence_edges[-1]].before] == [1, 2]
    again = compare(dict(reversed(list(base.items()))), dict(reversed(list(head.items()))))
    assert report.model_dump(exclude={"stats"}) == again.model_dump(exclude={"stats"})


def test_source_stays_data_and_full_files_are_stored_once(tmp_path):
    sentinel = tmp_path / "must-not-exist"
    source = f"from pathlib import Path\nPath({str(sentinel)!r}).touch()\n"
    source += 'HTML = "<script>window.sourceExecuted = true</script>"\n'
    source += "\n" * 200 + "def late(): return 1\n"
    report = compare({}, {"a.py": source})
    assert not sentinel.exists()
    assert report.source_files[0].after.text == source
    assert report.changes[-1].after.line == 204
    assert report.model_dump_json().count("must-not-exist") == 1


def test_parenthesized_multiline_decorator_includes_at_sign():
    source = "@(\n    decorate\n)\ndef f(): return 1\n"
    report = compare({}, {"a.py": source})
    assert next(c for c in report.changes if c.symbol == "a.py::f").after.line == 1


def test_module_ranges_use_python_physical_lines_not_unicode_string_separators():
    source = "TEXT = 'a\u2028b'\r\n\r\ndef f(): return TEXT\r\n"
    report = compare({}, {"a.py": source})
    changes = {c.symbol: c for c in report.changes}
    assert changes["a.py::<module>"].after.end_line == 3
    assert changes["a.py::f"].after.line == 3


def test_decorator_only_change_and_new_test_have_valid_paths():
    source = "@one\ndef f(): return 1\n"
    report = compare(
        {"a.py": source},
        {
            "a.py": source.replace("@one", "@two"),
            "test_a.py": "from a import f\ndef test_new(): return f()\n",
        },
    )
    assert "a.py::f" in report.changed
    assert report.recommendations[0].path_revision == "after"
    assert report.recommendations[0].evidence_edges == []
    assert_typed_paths(report)


def test_line_movement_preserves_edge_ids_and_cycles_have_valid_typed_paths():
    base = {
        "a.py": "def f(): return g()\ndef g(): return f()\n",
        "test_a.py": "from a import g\ndef test_g(): return g()\n",
    }
    head = base | {"a.py": "# moved\n\ndef f(): return g() + 1\ndef g(): return f()\n"}
    report = compare(base, head)
    assert_typed_paths(report)
    assert {e.id for e in report.edges} == {e.id for e in compare(base, base).edges}
    assert all(e.revision == "both" for e in report.edges)
