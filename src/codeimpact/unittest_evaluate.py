"""Replay v4 with versioned source labels for newly discovered unittest methods."""

import ast
import hashlib
from pathlib import Path
from typing import Any, Literal

from codeimpact.corpus import CorpusCase, Nonblank, StrictModel
from codeimpact.discovery import CURRENT_POLICY, V2_POLICY, mixed_case_methods
from codeimpact.evaluate import Classification, Metrics
from codeimpact.fresh_evaluate import PROJECT, file_hash, measurement, replay_source_matches
from codeimpact.holdout_evaluate import DraftLabel, safe_file
from codeimpact.real_evaluate import SHA256, evaluate_real, read_metadata, require
from codeimpact.real_evaluate import main as real_main
from codeimpact.v4_evaluate import (
    DIRECTORY,
    ENGINE,
    FIRST,
    FREEZE,
    SUCCESSOR,
    attach_coverage,
    evaluate_v4,
    inventories,
    stable_bytes,
    validate_frozen,
)

LABELS = "labels.json"
BASELINE = "baseline.json"
OUTPUT = Path("reports/real-v4-unittest-discovery-v1-evaluation.json")


class CaseDraft(StrictModel):
    source_case_sha256: SHA256
    labels: dict[str, DraftLabel]


class DiscoveryLabels(StrictModel):
    schema_version: Literal["1.0"]
    name: Literal["unittest-discovery-v1"]
    policy: Literal["test-files-v3"]
    original_discovery_sha256: SHA256
    original_freeze_sha256: SHA256
    review_status: Literal["agent_draft"]
    independent_reviewer: None
    author: Nonblank
    timing: Nonblank
    cases: dict[str, CaseDraft]


class Baseline(StrictModel):
    schema_version: Literal["1.0"]
    name: Literal["unittest-discovery-v1"]
    labels_sha256: SHA256
    original_first_run_sha256: SHA256
    original_report_sha256: SHA256
    analyzer_sha256: dict[str, SHA256]
    report_sha256: SHA256
    summary: Metrics
    classifications: dict[str, Classification]


def verify_ranges(case: CorpusCase, labels: dict[str, DraftLabel]) -> None:
    by_path: dict[str, dict[str, tuple[int, int | None]]] = {}
    for sid, label in labels.items():
        path, _, qualified = sid.partition("::")
        if path not in by_path:
            tree = ast.parse(case.request.head.files[path], filename=path)
            methods = mixed_case_methods(tree)
            by_path[path] = {
                f"{cls.name}.{node.name}": (node.lineno, node.end_lineno)
                for cls in tree.body
                if isinstance(cls, ast.ClassDef)
                for node in cls.body
                if isinstance(node, ast.FunctionDef) and node in methods
            }
        require(
            by_path[path].get(qualified) == (label.line, label.end_line),
            f"Label source range mismatch: {sid}",
        )


def label_extensions(
    directory: Path,
    receipt: DiscoveryLabels,
    cases: list[CorpusCase],
    original: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    require(
        file_hash(safe_file(directory, "discovery.json")) == receipt.original_discovery_sha256
        and file_hash(safe_file(directory, FREEZE)) == receipt.original_freeze_sha256,
        "Original v4 discovery inputs changed",
    )
    extensions: dict[str, dict[str, Any]] = {}
    for case in cases:
        cid = case.id
        for side in ("base", "head"):
            old, new = original[cid][side], current[cid][side]
            require(
                set(old["discovered_ids"]) <= set(new["discovered_ids"])
                and old["test_shaped_definition_count"] == new["test_shaped_definition_count"]
                and set(old["outside_discovery"]) - set(new["discovered_ids"])
                == set(new["outside_discovery"]),
                f"Unexpected source inventory change: {cid} {side}",
            )
        added = set(current[cid]["head"]["discovered_ids"]) - set(
            original[cid]["head"]["discovered_ids"]
        )
        if not added:
            continue
        draft = receipt.cases.get(cid)
        if draft is None or set(draft.labels) != added:
            raise ValueError(f"Missing new labels: {cid}")
        require(
            file_hash(safe_file(directory, f"cases/{cid}.json")) == draft.source_case_sha256,
            f"Label source changed: {cid}",
        )
        verify_ranges(case, draft.labels)
        extensions[cid] = {
            field: {
                sid: label.rationale
                for sid, label in draft.labels.items()
                if label.classification == category
            }
            for field, category in (
                ("expected_affected", "affected"),
                ("expected_unaffected", "unaffected"),
                ("unclassified", "uncertain"),
            )
        } | {"expected_unclassified_recommendations": []}
    require(set(extensions) == set(receipt.cases), "Unexpected discovery label case")
    return extensions


def measure(
    directory: Path,
    receipt: DiscoveryLabels,
    *,
    variadic: bool = False,
    parameter_rows: bool = False,
    reexports: bool = False,
) -> dict[str, Any]:
    _, cases, old_audit = validate_frozen(directory)
    audit = inventories(cases, policy=CURRENT_POLICY)
    extensions = label_extensions(directory, receipt, cases, old_audit, audit)
    report = evaluate_real(
        directory,
        discovery_policy=V2_POLICY,
        analysis_policy=CURRENT_POLICY,
        label_extensions=extensions,
        variadic=variadic,
        parameter_rows=parameter_rows,
        reexports=reexports,
    )
    attach_coverage(report, audit)
    report.update(
        successor_schema_version="1.0",
        discovery_policy=CURRENT_POLICY,
        discovery=audit,
        newly_discovered={cid: sorted(draft.labels) for cid, draft in receipt.cases.items()},
        independent_review="pending",
        interpretation="Expanded v4 discovery against draft source dependency labels. "
        "Upstream tests were not executed.",
    )
    return report


def evaluate_unittest(directory: Path, *, successor: Path = PROJECT / SUCCESSOR) -> dict[str, Any]:
    label_file = safe_file(successor, LABELS)
    baseline_file = safe_file(successor, BASELINE)
    baseline = Baseline.model_validate(read_metadata(baseline_file)[0])
    require(file_hash(label_file) == baseline.labels_sha256, "Frozen discovery labels changed")
    require(
        file_hash(safe_file(directory, FIRST)) == baseline.original_first_run_sha256,
        "Original first-run receipt changed",
    )
    require(set(baseline.analyzer_sha256) == ENGINE, "Successor engine inventory differs")
    for path, expected in baseline.analyzer_sha256.items():
        require(
            replay_source_matches(PROJECT, path, expected), f"Successor analyzer changed: {path}"
        )
    receipt = DiscoveryLabels.model_validate(read_metadata(label_file)[0])
    original = evaluate_v4(directory)
    require(
        not original["evaluation"]["regressions"]
        and hashlib.sha256(stable_bytes(original)).hexdigest() == baseline.original_report_sha256,
        "Frozen v4 replay differs",
    )

    report = measure(directory, receipt)
    observed = measurement(report)
    regressions = []
    if (
        hashlib.sha256(stable_bytes(report)).hexdigest() != baseline.report_sha256
        or observed["summary"]["metrics"] != baseline.summary.model_dump()
        or observed["classifications"]
        != {cid: row.model_dump() for cid, row in baseline.classifications.items()}
    ):
        regressions.append("v4 unittest discovery: report differs from the recorded measurement")
    previous = measurement(original)["analysis_sha256"]
    for cid, digest in observed["analysis_sha256"].items():
        if cid not in receipt.cases and digest != previous[cid]:
            regressions.append(f"{cid}: analysis changed outside the discovery extension")
    report["first_regressions"] = report["evaluation"]["regressions"]
    report["evaluation"]["regressions"] = regressions
    report.update(
        original_summary=original["summary"],
        original_report_sha256=baseline.original_report_sha256,
        labels_sha256=baseline.labels_sha256,
        baseline_sha256=file_hash(baseline_file),
    )
    return report


def main(argv: list[str] | None = None) -> int:
    return real_main(
        argv,
        evaluator=evaluate_unittest,
        default_corpus=DIRECTORY,
        default_output=OUTPUT,
        protected_inputs=(PROJECT / "corpus",),
    )


if __name__ == "__main__":
    raise SystemExit(main())
