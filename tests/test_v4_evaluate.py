"""V4 replay integrity, evidence validation and a separate review workflow."""

import importlib
import json
import shutil
import socket
import subprocess
from pathlib import Path

import pytest

from codeimpact import evaluate, v4_evaluate
from codeimpact.fresh_evaluate import file_hash
from codeimpact.models import Snapshot

ROOT = Path(__file__).parents[1]
DATA = ROOT / v4_evaluate.DIRECTORY
CASE = "humanize_intcomma_locale"


@pytest.fixture
def review_real_v4(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT))
    return importlib.import_module("scripts.review_real_v4")


@pytest.fixture
def dataset(tmp_path):
    return Path(shutil.copytree(DATA, tmp_path / "real-v4"))


def edit(path, fn):
    obj = json.loads(path.read_text())
    fn(obj)
    path.write_bytes(v4_evaluate.stable_bytes(obj))


def test_v4_offline_measurement_validates_all_paths(monkeypatch):
    def forbidden(*_a, **_kw):
        pytest.fail("offline replay attempted network or subprocess")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    report = v4_evaluate.evaluate_v4(DATA)
    assert report["evaluation"]["regressions"] == []
    assert len(report["first_regressions"]) == 6
    assert report["independent_review"] == "pending"
    assert report["reference_commit"] == v4_evaluate.REFERENCE
    summary = report["summary"]
    assert summary["test_count"] == 105
    assert summary["test_shaped_definition_count"] == 169
    assert summary["outside_discovery_count"] == 64
    assert summary["selected_count"] == 92
    assert summary["unclassified_test_count"] == 16
    assert summary["unclassified_unselected_count"] == 0
    assert summary["reason_counts"] == {
        "Conservative module/import dependency": 87,
        "Test itself changed": 5,
    }
    assert summary["metrics"]["counts"] == {
        "tp": 19,
        "fp": 57,
        "fn": 0,
        "tn": 13,
        "unclassified_recommendations": 16,
    }
    assert report["repositories"]["gruns/icecream"]["metrics"]["recall"]["value"] is None
    assert all(
        "elapsed_ms" not in item["analysis"]["stats"] for item in report["evaluation"]["cases"]
    )


def test_discovery_audit_distinguishes_filename_function_and_compound_rules():
    snapshot = Snapshot(
        files={
            "test.py": "def test_current(): pass\n",
            "tests.py": "def test_filename(): pass\n",
            "test_modes.py": (
                "class Example:\n"
                "    def testCamelCase(self): pass\n"
                "    if flag:\n"
                "        def test_conditional(self): pass\n"
            ),
        }
    )
    audit = v4_evaluate.source_inventory(snapshot)
    assert audit["discovered_ids"] == ["test.py::test_current"]
    assert audit["outside_discovery"] == {
        "tests.py::test_filename": "unsupported_filename",
        "test_modes.py::Example.testCamelCase": "unsupported_function_name",
        "test_modes.py::Example.test_conditional": "compound_statement",
    }
    assert audit["test_shaped_definition_count"] == 4


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda d: d["request"]["head"]["files"].__setitem__("setup.py", "pass\n"),
            "Source blob hash/size mismatch",
        ),
        (
            lambda d: d["request"]["head"]["files"].pop("setup.py"),
            "complete supported Python tree",
        ),
        (
            lambda d: d["expected_affected"].pop("tests/test_number.py::test_intcomma"),
            "Every head test needs an explicit label",
        ),
        (
            lambda d: d["unclassified"].__setitem__(
                "tests/test_number.py::test_intcomma", "overlap"
            ),
            "labels must be disjoint",
        ),
    ],
)
def test_invalid_cases_fail_before_analysis(dataset, monkeypatch, mutate, message):
    edit(dataset / f"cases/{CASE}.json", mutate)
    monkeypatch.setattr(
        v4_evaluate, "evaluate_real", lambda *_a, **_kw: pytest.fail("ran analysis")
    )
    with pytest.raises(ValueError, match=message):
        v4_evaluate.evaluate_v4(dataset)


def test_tampered_provenance_review_metadata_is_rejected(dataset):
    edit(
        dataset / f"provenance/{CASE}.json",
        lambda d: d["label_review"].update(status="reviewed"),
    )
    with pytest.raises(ValueError, match="Reviewed labels need a named reviewer"):
        v4_evaluate.evaluate_v4(dataset)


def test_source_only_pack_regenerates_and_freeze_detects_changes(
    dataset, monkeypatch, review_real_v4
):
    monkeypatch.setattr(evaluate, "analyze", lambda *_a: pytest.fail("ran analysis"))
    path = dataset / "REVIEW.md"
    assert review_real_v4.build_pack(dataset) == path.read_text()
    assert "unsupported_function_name" in path.read_text()
    with path.open("a") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="Frozen v4 input changed: REVIEW.md"):
        v4_evaluate.evaluate_v4(dataset)


def test_v4_rejects_bad_revision_evidence(monkeypatch):
    analyze = evaluate.analyze

    def corrupt(request, **kwargs):
        report = analyze(request, **kwargs)
        if report.recommendations:
            rec = report.recommendations[0]
            rec.path_revision = "after" if rec.path_revision == "both" else "both"
        return report

    monkeypatch.setattr(evaluate, "analyze", corrupt)
    with pytest.raises(ValueError, match="path revision intersection"):
        v4_evaluate.evaluate_v4(DATA)


def test_recorded_discrepancies_cannot_drift(dataset):
    edit(
        dataset / "baseline.json",
        lambda d: d["annotations"][CASE]["known_discrepancies"]["false_positives"].clear(),
    )
    assert (
        v4_evaluate.main(["--corpus", str(dataset), "--output", str(dataset.parent / "r.json")])
        == 1
    )
    report = json.loads((dataset.parent / "r.json").read_text())
    assert report["evaluation"]["regressions"] == [
        f"{CASE}: discrepancies differ from the v4 baseline"
    ]


def test_first_report_drift_fails_even_with_same_classifications(monkeypatch):
    evaluate_real = v4_evaluate.evaluate_real

    def changed(*args, **kw):
        report = evaluate_real(*args, **kw)
        rec = report["evaluation"]["cases"][0]["analysis"]["recommendations"][0]
        rec["score"] += 1
        return report

    monkeypatch.setattr(v4_evaluate, "evaluate_real", changed)
    assert v4_evaluate.evaluate_v4(DATA)["evaluation"]["regressions"] == [
        "v4: report differs from the frozen first measurement"
    ]


@pytest.fixture
def record():
    sid = "tests/test_number.py::test_intcomma"
    provenance = json.loads((DATA / f"provenance/{CASE}.json").read_text())
    return {
        "schema_version": "1.0",
        "case": CASE,
        "frozen_inputs_sha256": file_hash(DATA / v4_evaluate.FREEZE),
        "labels_sha256": provenance["label_review"]["labels_sha256"],
        "reviewer": "Synthetic Test Reviewer",
        "reviewed_on": "2026-11-17",
        "review_reference": "fixture for validator test",
        "discovery_notes": "Synthetic check of one discovered definition.",
        "decisions": {
            sid: {
                "original": "affected",
                "proposed": "uncertain",
                "rationale": "Synthetic disagreement.",
                "evidence": [
                    {
                        "revision": "head",
                        "path": "src/humanize/number.py",
                        "line": 70,
                        "end_line": 79,
                    }
                ],
            }
        },
    }


def test_review_record_does_not_change_frozen_labels(record, review_real_v4):
    before = file_hash(DATA / f"cases/{CASE}.json")
    result = review_real_v4.validate_review(
        DATA, review_real_v4.ReviewRecord.model_validate(record)
    )
    assert len(result["remaining_ids"]) == 33
    assert result["proposed_revisions"] == ["tests/test_number.py::test_intcomma"]
    assert file_hash(DATA / f"cases/{CASE}.json") == before


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("reviewed_on", "not-a-date", "reviewed_on"),
        ("reviewer", "   ", "reviewer"),
        ("labels_sha256", "0" * 64, "Review labels differ"),
        ("frozen_inputs_sha256", "0" * 64, "Review freeze differs"),
    ],
)
def test_bad_review_metadata(record, field, value, message, review_real_v4):
    record[field] = value
    with pytest.raises(ValueError, match=message):
        review_real_v4.validate_review(DATA, review_real_v4.ReviewRecord.model_validate(record))


def test_bad_review_span(record, review_real_v4):
    decision = record["decisions"]["tests/test_number.py::test_intcomma"]
    decision["evidence"][0]["end_line"] = 100000
    with pytest.raises(ValueError, match="Invalid pinned source range"):
        review_real_v4.validate_review(DATA, review_real_v4.ReviewRecord.model_validate(record))


@pytest.fixture
def pilot_inputs(review_real_v4):
    return review_real_v4.load_inputs(DATA)


@pytest.mark.parametrize(
    ("case_id", "count", "uncertain"),
    [("humanize_small_delta", 33, 0), ("oyaml_error_context", 18, 7)],
)
def test_pilot_packet_is_source_only_and_locally_citable(
    case_id, count, uncertain, monkeypatch, review_real_v4
):
    def forbidden(*_args, **_kwargs):
        pytest.fail("review packet ran analysis, network or a subprocess")

    monkeypatch.setattr(evaluate, "analyze", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    pilot_inputs = review_real_v4.load_inputs(DATA)
    packet = review_real_v4.pilot_packet(pilot_inputs, case_id)
    assert packet == review_real_v4.pilot_packet(pilot_inputs, case_id)
    context = pilot_inputs.provenance[case_id]
    page = pilot_inputs.cases[case_id]
    template = review_real_v4.review_template(pilot_inputs, case_id)
    assert template["case"] == case_id
    assert template["labels_sha256"] == context.label_review.labels_sha256
    assert template["frozen_inputs_sha256"] in packet
    assert template["reviewer"] == template["reviewed_on"] == ""
    assert packet.count("- [ ]") == len(template["decisions"]) == count
    assert (
        sum(row["original"] == "uncertain" for row in template["decisions"].values()) == uncertain
    )
    assert all(
        row["rationale"] == "" and row["evidence"] == [] for row in template["decisions"].values()
    )
    for snapshot in (context.base, context.head):
        assert snapshot.commit.sha in packet
        assert snapshot.license.text.rstrip("\n") in packet
        assert all(digest in packet for digest in snapshot.source_sha256.values())
    for sid, (_, rationale) in review_real_v4.draft_labels(page).items():
        path, _ = sid.split("::", 1)
        assert f"`{sid}`" in packet and rationale in packet
        assert f"[head `{path}:" in packet
    if case_id == "humanize_small_delta":
        assert "[base `tests/test_time.py:456–502`](#source-base-11)" in packet
        assert "[head `tests/test_time.py:456–507`](#source-head-11)" in packet
    else:
        assert "base: no pinned definition span · [head `test_oyaml.py:192–194`]" in packet
    assert "## Complete captured Python diff" in packet
    for forbidden_field in ("selected_test_ids", "score", "recommendation", "false_positive"):
        assert forbidden_field not in packet.lower()


def pilot_record(review_tool, inputs, case_id, reviewer, proposed):
    data = review_tool.review_template(inputs, case_id)
    data.update(
        reviewer=reviewer,
        reviewed_on="2026-11-23",
        review_reference="Fictional test-only reference",
        discovery_notes="Fictional discovery check.",
        decisions={
            sid: data["decisions"][sid]
            | {
                "proposed": label,
                "rationale": "Fictional rationale for a summary regression.",
                "evidence": [
                    {"revision": "head", "path": sid.split("::", 1)[0], "line": 1, "end_line": 1}
                ],
            }
            for sid, label in proposed.items()
        },
    )
    return review_tool.ReviewRecord.model_validate(data)


def test_empty_pilot_keeps_all_ids_unreviewed(review_real_v4, pilot_inputs):
    result = review_real_v4.summarize_pilot(pilot_inputs, [])
    assert result["status"] == "ready_for_review"
    assert result["totals"] == {
        "definitions": 51,
        "draft_uncertain": 7,
        "records": 0,
        "unreviewed": 51,
        "agreements": 0,
        "proposed_label_changes": 0,
        "unresolved_disagreements": 0,
    }
    assert set(result["cases"]) == {"humanize_small_delta", "oyaml_error_context"}


def test_pilot_summary_records_conflicts_and_partial_coverage(review_real_v4, pilot_inputs):
    cid = "humanize_small_delta"
    labels = review_real_v4.draft_labels(pilot_inputs.cases[cid])
    agree, change, dispute = sorted(labels)[:3]
    author_a = pilot_record(
        review_real_v4,
        pilot_inputs,
        cid,
        "Fictional reviewer A",
        {agree: labels[agree][0], change: "uncertain", dispute: labels[dispute][0]},
    )
    author_b = pilot_record(
        review_real_v4, pilot_inputs, cid, "Fictional reviewer B", {dispute: "uncertain"}
    )
    result = review_real_v4.summarize_pilot(pilot_inputs, [author_b, author_a])
    reordered = review_real_v4.summarize_pilot(pilot_inputs, [author_a, author_b])
    assert v4_evaluate.stable_bytes(result) == v4_evaluate.stable_bytes(reordered)
    assert result["status"] == "partial"
    assert result["totals"]["definitions"] == 51
    assert result["totals"]["unreviewed"] == 48
    humanize = result["cases"][cid]
    assert list(humanize["agreements"]) == [agree]
    assert list(humanize["proposed_label_changes"]) == [change]
    assert list(humanize["unresolved_disagreements"]) == [dispute]
    row = humanize["unresolved_disagreements"][dispute]
    assert row["proposed_labels"] == sorted([labels[dispute][0], "uncertain"])
    assert [s["reviewer"] for s in row["submissions"]] == [author_a.reviewer, author_b.reviewer]
    assert all(s["evidence"] and s["rationale"] for s in row["submissions"])
    assert len(result["cases"]["oyaml_error_context"]["unreviewed_ids"]) == 18


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda d: d.update(frozen_inputs_sha256="0" * 64), "Review freeze differs"),
        (lambda d: d.update(labels_sha256="0" * 64), "Review labels differ"),
        (lambda d: d.update(case="icecream_local_time"), "outside the v4 review pilot"),
        (
            lambda d: d["decisions"].update(
                {"unknown.py::test_example": next(iter(d["decisions"].values()))}
            ),
            "Unknown review definition",
        ),
        (
            lambda d: next(iter(d["decisions"].values()))["evidence"][0].update(end_line=99999),
            "Invalid pinned source range",
        ),
        (
            lambda d: next(iter(d["decisions"].values()))["evidence"][0].update(path="missing.py"),
            "Invalid pinned source range",
        ),
    ],
)
def test_summary_rejects_invalid_submissions(review_real_v4, pilot_inputs, mutation, message):
    cid = "oyaml_error_context"
    sid = next(iter(pilot_inputs.cases[cid].unclassified))
    original = pilot_record(
        review_real_v4, pilot_inputs, cid, "Fictional reviewer", {sid: "uncertain"}
    )
    data = original.model_dump(mode="json")
    mutation(data)
    with pytest.raises(ValueError, match=message):
        review_real_v4.summarize_pilot(
            pilot_inputs, [review_real_v4.ReviewRecord.model_validate(data)]
        )


def test_conflicting_records_from_same_reviewer_are_rejected(review_real_v4, pilot_inputs):
    cid = "oyaml_error_context"
    sid = next(iter(pilot_inputs.cases[cid].unclassified))
    first = pilot_record(review_real_v4, pilot_inputs, cid, "Fictional reviewer", {sid: "affected"})
    second = pilot_record(
        review_real_v4, pilot_inputs, cid, "fictional REVIEWER", {sid: "unaffected"}
    )
    with pytest.raises(ValueError, match="Multiple records from"):
        review_real_v4.summarize_pilot(pilot_inputs, [first, second])


def test_summary_cli_reads_records_without_modifying_them(
    review_real_v4, pilot_inputs, tmp_path, capsys
):
    cid = "oyaml_error_context"
    sid = next(iter(pilot_inputs.cases[cid].unclassified))
    record = pilot_record(
        review_real_v4, pilot_inputs, cid, "Fictional reviewer", {sid: "uncertain"}
    )
    path = tmp_path / "test-only-review.json"
    payload = record.model_dump_json().encode()
    path.write_bytes(payload)
    review_real_v4.main(["--corpus", str(DATA), "--summarize", str(path)])
    assert json.loads(capsys.readouterr().out)["totals"]["unreviewed"] == 50
    assert path.read_bytes() == payload


def test_discovery_notes_alone_do_not_review_any_ids(review_real_v4, pilot_inputs):
    record = pilot_record(
        review_real_v4, pilot_inputs, "oyaml_error_context", "Fictional reader", {}
    )
    result = review_real_v4.summarize_pilot(pilot_inputs, [record])
    assert result["status"] == "partial"
    assert result["totals"]["records"] == 1
    assert result["totals"]["unreviewed"] == 51
    assert result["cases"][record.case]["reviews"][0]["discovery_notes"] == record.discovery_notes


def test_complete_coverage_keeps_unresolved_disagreements_visible(review_real_v4, pilot_inputs):
    records = [
        pilot_record(
            review_real_v4,
            pilot_inputs,
            cid,
            "Fictional reviewer A",
            {
                sid: label
                for sid, (label, _) in review_real_v4.draft_labels(pilot_inputs.cases[cid]).items()
            },
        )
        for cid in review_real_v4.PILOT_CASES
    ]
    cid = "oyaml_error_context"
    sid = next(iter(pilot_inputs.cases[cid].unclassified))
    records.append(
        pilot_record(review_real_v4, pilot_inputs, cid, "Fictional reviewer B", {sid: "affected"})
    )
    result = review_real_v4.summarize_pilot(pilot_inputs, records)
    assert result["status"] == "coverage_complete"
    assert result["totals"]["unreviewed"] == 0
    assert result["totals"]["unresolved_disagreements"] == 1
    assert list(result["cases"][cid]["unresolved_disagreements"]) == [sid]
