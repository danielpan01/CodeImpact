"""Offline corpus integrity, source-as-data safety, and honest denominators."""

import json
import shutil
import socket
from pathlib import Path

import pytest

from codeimpact.real_evaluate import evaluate_real, load_real, main

ROOT = Path(__file__).parents[1] / "corpus" / "real"


@pytest.fixture
def dataset(tmp_path):
    target = tmp_path / "real"
    shutil.copytree(ROOT, target)
    return target


def edit(root, relative, mutate):
    path = root / relative
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data))


def test_complete_offline_dataset_and_draft_denominators(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("offline evaluation attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    report = evaluate_real(ROOT)
    assert report["dataset_schema_version"] == "1.0"
    assert report["summary"]["test_count"] == 201
    assert report["summary"]["unclassified_test_count"] == 33
    assert report["summary"]["label_status_counts"] == {"draft": 6}
    assert report["evaluation"]["case_count"] == 6
    assert len(report["repositories"]) == 3
    assert report["summary"]["selected_count"] == sum(c["selected_count"] for c in report["cases"])
    for case in report["cases"]:
        assert case["selected_count"] == len(case["selected_test_ids"])
        assert sum(case["reason_counts"].values()) == case["selected_count"]
        assert case["unclassified_recommendation_count"] <= case["unclassified_test_count"]


@pytest.mark.parametrize(
    ("relative", "mutate", "error"),
    [
        (
            "cases/schedule_tags.json",
            lambda d: d["request"]["head"]["files"].pop("setup.py"),
            "complete",
        ),
        (
            "cases/schedule_tags.json",
            lambda d: d["request"]["head"]["files"].__setitem__("setup.py", "# altered\n"),
            "hash",
        ),
        (
            "provenance/schedule_tags.json",
            lambda d: d["head"]["tree"].__setitem__("truncated", True),
            "truncated",
        ),
        ("provenance/schedule_tags.json", lambda d: d["head"]["tree"]["tree"].pop(), "tree"),
        (
            "provenance/schedule_tags.json",
            lambda d: d.__setitem__("change_url", "https://example.com"),
            "URL",
        ),
        (
            "provenance/schedule_tags.json",
            lambda d: d["head"]["commit"]["parents"][0].__setitem__("sha", "0" * 40),
            "parent",
        ),
        (
            "provenance/schedule_tags.json",
            lambda d: d["head"]["license"].__setitem__("text", "MIT"),
            "license",
        ),
        (
            "provenance/schedule_tags.json",
            lambda d: d["label_review"].__setitem__("labels_sha256", "0" * 64),
            "label",
        ),
        (
            "provenance/schedule_tags.json",
            lambda d: d["label_review"].__setitem__("status", "reviewed"),
            "reviewer",
        ),
        ("selection.json", lambda d: d["cases"].append(d["cases"][0]), "six"),
    ],
)
def test_tampering_fails_closed(dataset, relative, mutate, error):
    edit(dataset, relative, mutate)
    with pytest.raises(ValueError, match=error):
        load_real(dataset)


def test_missing_extra_and_symlink_provenance_rejected(dataset, tmp_path):
    path = dataset / "provenance/schedule_tags.json"
    backup = path.read_bytes()
    path.unlink()
    with pytest.raises(ValueError, match="provenance"):
        load_real(dataset)
    outside = tmp_path / "outside.json"
    outside.write_bytes(backup)
    path.symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        load_real(dataset)


def test_cli_output_cannot_destroy_dataset(dataset, capsys):
    path = dataset / "selection.json"
    before = path.read_bytes()
    assert main(["--corpus", str(dataset), "--output", str(path)]) == 2
    assert path.read_bytes() == before
    assert "outside" in capsys.readouterr().err


def test_duplicate_json_keys_rejected(dataset):
    path = dataset / "selection.json"
    path.write_text(
        path.read_text().replace(
            '"schema_version":', '"schema_version":"1.0", "schema_version":', 1
        )
    )
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        load_real(dataset)


def test_reports_repeat_exactly_and_match_recorded_mistakes():
    first = evaluate_real(ROOT)
    assert first == evaluate_real(ROOT)
    assert first["evaluation"]["regressions"] == []
    assert first["summary"]["metrics"]["counts"] == {
        "tp": 45,
        "fn": 0,
        "fp": 0,
        "tn": 123,
        "unclassified_recommendations": 11,
    }
    assert first["volatile_fields_excluded"] == ["evaluation.cases[].analysis.stats.elapsed_ms"]
    for case in first["evaluation"]["cases"]:
        assert "elapsed_ms" not in case["analysis"]["stats"]


def test_no_upstream_imports_or_processes(monkeypatch):
    import builtins
    import subprocess

    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        assert name.split(".")[0] not in {
            "schedule",
            "markupsafe",
            "itsdangerous",
            "test_schedule",
            "test_itsdangerous",
        }
        return original(name, *args, **kwargs)

    def forbidden(*args, **kwargs):
        raise AssertionError("evaluation spawned a process")

    monkeypatch.setattr(builtins, "__import__", guarded)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    evaluate_real(ROOT)


def test_evidence_path_corruption_is_rejected(monkeypatch):
    from codeimpact import evaluate

    original = evaluate.analyze

    def corrupt(request):
        report = original(request)
        report.recommendations[0].evidence_path = ["not-a-test"]
        return report

    monkeypatch.setattr(evaluate, "analyze", corrupt)
    with pytest.raises(ValueError, match="path must start"):
        evaluate_real(ROOT)


def test_cli_baseline_drift_is_nonzero(dataset, tmp_path, capsys):
    edit(
        dataset,
        "cases/itsdangerous_fips.json",
        lambda d: d["known_discrepancies"]["false_positives"].update(
            {
                "tests/test_itsdangerous/test_signer.py::test_abstract_algorithm": (
                    "Deliberately restore the former false positive to verify baseline drift."
                )
            }
        ),
    )
    output = tmp_path / "result.json"
    assert main(["--corpus", str(dataset), "--output", str(output)]) == 1
    assert "Baseline: CHANGED" in capsys.readouterr().out
    assert json.loads(output.read_text())["summary"]["metrics"]["counts"]["fp"] == 0


@pytest.mark.parametrize("total", [False, True])
def test_metadata_byte_limits(monkeypatch, total):
    from codeimpact import real_evaluate

    monkeypatch.setattr(real_evaluate, "MAX_CORPUS_BYTES" if total else "MAX_METADATA_BYTES", 100)
    with pytest.raises(ValueError, match="size limit"):
        load_real(ROOT)


@pytest.mark.parametrize(
    "change", ["duplicate", "unsafe", "mode", "subtree", "sha256", "extra_hash", "pin"]
)
def test_tree_and_source_integrity(dataset, change):
    def mutate(d):
        tree = d["head"]["tree"]["tree"]
        if change == "duplicate":
            tree.append(tree[0])
        elif change == "unsafe":
            tree[0]["path"] = "../escape.py"
        elif change == "mode":
            tree[0]["mode"] = "160000"
        elif change == "subtree":
            next(e for e in tree if e["type"] == "tree")["sha"] = "0" * 40
        elif change == "sha256":
            d["head"]["source_sha256"]["setup.py"] = "0" * 64
        elif change == "extra_hash":
            d["head"]["source_sha256"]["missing.py"] = "0" * 64
        elif change == "pin":
            d["head"]["commit"]["sha"] = "0" * 40

    edit(dataset, "provenance/schedule_tags.json", mutate)
    with pytest.raises(ValueError):
        load_real(dataset)


def project_script(monkeypatch, name):
    import importlib

    monkeypatch.syspath_prepend(str(ROOT.parents[1] / "scripts"))
    return importlib.import_module(name)


def test_review_pack_is_source_only_and_current(monkeypatch):
    from codeimpact import evaluate

    def forbidden(*args, **kwargs):
        raise AssertionError("review generator ran analyzer")

    monkeypatch.setattr(evaluate, "analyze", forbidden)
    script = project_script(monkeypatch, "review_real")
    pack = script.review_pack(ROOT)
    assert pack == (ROOT / "REVIEW.md").read_text()
    assert pack.count("- [ ]") == 201
    assert pack.count("Label status: **draft**") == 6


@pytest.mark.parametrize("id", ["schedule_tags", "markupsafe_striptags", "itsdangerous_fips"])
def test_capture_replays_pinned_github_objects_as_data(monkeypatch, id):
    import asyncio
    import base64

    import httpx

    from codeimpact.real_evaluate import blob_hash

    script = project_script(monkeypatch, "capture_real")
    selection, cases, provenance, _ = load_real(ROOT)
    case = next(c for c in cases if c.id == id)
    selected = next(c for c in selection.cases if c.id == id)
    p = provenance[id]
    blobs = {}
    for side in ["base", "head"]:
        receipt = getattr(p, side)
        for source in [*getattr(case.request, side).files.values(), receipt.license.text]:
            raw = source.encode()
            sha = blob_hash(raw)
            blobs[sha] = {
                "sha": sha,
                "size": len(raw),
                "encoding": "base64",
                "content": base64.b64encode(raw).decode(),
            }

    def handle(request):
        path = request.url.path
        prefix = f"/repos/{selected.repository}"
        if path == prefix:
            data = {"full_name": selected.repository, "private": False}
        elif "/git/blobs/" in path:
            data = blobs[path.split("/")[-1]]
        else:
            receipt = next(
                r
                for r in [p.base, p.head]
                if path.endswith(r.commit.sha) or path.endswith(r.tree.sha)
            )
            data = (
                receipt.commit.model_dump()
                if "/git/commits/" in path
                else receipt.tree.model_dump()
            )
        return httpx.Response(200, json=data)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            return await script.capture(client, selected.model_dump())

    captured = asyncio.run(run())
    assert captured["request"] == case.request.model_dump()
    for side in ["base", "head"]:
        assert captured["provenance"][side] == getattr(p, side).model_dump()


def test_capture_rejects_bad_identity_before_network(monkeypatch):
    import asyncio

    script = project_script(monkeypatch, "capture_real")
    selected = json.loads((ROOT / "selection.json").read_text())["cases"][0]
    selected["id"] = "../escape"
    with pytest.raises(ValueError):
        asyncio.run(script.capture(None, selected))


def test_report_output_hardlink_cannot_overwrite_case(dataset, tmp_path):
    original = dataset / "cases/schedule_tags.json"
    before = original.read_bytes()
    output = tmp_path / "result.json"
    output.hardlink_to(original)
    assert main(["--corpus", str(dataset), "--output", str(output)]) == 0
    assert original.read_bytes() == before
    assert json.loads(output.read_text())["dataset_schema_version"] == "1.0"


def test_failed_report_replace_leaves_no_temporary_file(tmp_path):
    output = tmp_path / "directory"
    output.mkdir()
    assert main(["--corpus", str(ROOT), "--output", str(output)]) == 2
    assert list(tmp_path.iterdir()) == [output]
