"""Replay a frozen fresh-source sample against explicit draft-label discrepancies."""

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal

from codeimpact.corpus import MAX_CORPUS_BYTES, CorpusCase, StrictModel
from codeimpact.discovery import CURRENT_POLICY
from codeimpact.fresh_evaluate import (
    CURRENT_SOURCES,
    PROJECT,
    CaseBaseline,
    FirstRun,
    file_hash,
    measurement,
)
from codeimpact.holdout_evaluate import discovery_audit, safe_file
from codeimpact.models import Snapshot
from codeimpact.real_evaluate import (
    SHA256,
    canonical_hash,
    evaluate_real,
    load_real,
    read_metadata,
    require,
)
from codeimpact.real_evaluate import main as real_main

REFERENCE = "ed728a0851e87308c0ed454071ded12adb37eda8"
DIRECTORY = Path("corpus/real-v4")
ENGINE = CURRENT_SOURCES | {"src/codeimpact/corpus.py", "src/codeimpact/evaluate.py"}
FREEZE = "frozen-inputs.json"
FIRST = "first-run.json"
BASELINE = "baseline.json"
DOCUMENTS = {
    "README.md",
    "PROTOCOL.md",
    "CANDIDATES.md",
    "ATTRIBUTION.md",
    "REVIEW.md",
    "REVIEW_WORKFLOW.md",
    "selection.json",
    "discovery.json",
    "preservation.json",
}
PREDECESSOR_REPORTS = {
    "corpus-evaluation.json",
    "real-evaluation.json",
    "real-v2-parameter-tables-v1-evaluation.json",
    "real-v3-parameter-tables-v1-evaluation.json",
}


class FrozenInputs(StrictModel):
    schema_version: Literal["1.0"]
    reference_commit: Literal["ed728a0851e87308c0ed454071ded12adb37eda8"]
    discovery_policy: Literal["test-files-v2"]
    analyzer_sha256: dict[str, SHA256]
    files_sha256: dict[str, SHA256]


class Preservation(StrictModel):
    schema_version: Literal["1.0"]
    corpus_sha256: dict[str, SHA256]
    reports_sha256: dict[str, SHA256]


class Baseline(StrictModel):
    schema_version: Literal["1.0"]
    first_run_sha256: SHA256
    annotations: dict[str, CaseBaseline]
    expected_uncertain_selected: dict[str, list[str]]


def source_inventory(snapshot: Snapshot) -> dict[str, Any]:
    """Extend the source audit with unittest-style names outside discovery."""
    result = discovery_audit(snapshot)
    outside = result["outside_discovery"]

    class Visitor(ast.NodeVisitor):
        def __init__(self, path: str) -> None:
            self.path = path
            self.scope: list[str] = []

        def definition(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> None:
            self.scope.append(node.name)
            if not isinstance(node, ast.ClassDef) and re.match(r"^test[A-Z]", node.name):
                sid = f"{self.path}::{'.'.join(self.scope)}"
                require(sid not in outside, f"Ambiguous source-only test ID: {sid}")
                outside[sid] = "unsupported_function_name"
            for child in node.body:
                self.visit(child)
            self.scope.pop()

        visit_FunctionDef = definition
        visit_AsyncFunctionDef = definition
        visit_ClassDef = definition

    for path, source in sorted(snapshot.files.items()):
        if path not in result["unparseable_files"]:
            Visitor(path).visit(ast.parse(source, filename=path))
    result["test_shaped_definition_count"] = len(result["discovered_ids"]) + len(outside)
    return result


def inventories(cases: list[CorpusCase]) -> dict[str, Any]:
    return {
        c.id: {side: source_inventory(getattr(c.request, side)) for side in ("base", "head")}
        for c in cases
    }


def input_files(cases: list[CorpusCase]) -> set[str]:
    return (
        DOCUMENTS
        | {f"{folder}/{c.id}.json" for c in cases for folder in ("cases", "provenance")}
        | {f"licenses/{c.id}-{side}.txt" for c in cases for side in ("base", "head")}
    )


def validate_history(directory: Path, project: Path) -> Preservation:
    receipt = Preservation.model_validate(
        read_metadata(safe_file(directory, "preservation.json"))[0]
    )
    prior = {
        p.relative_to(project).as_posix()
        for p in (project / "corpus").rglob("*")
        if p.is_file() and not p.is_relative_to(project / DIRECTORY)
    }
    require(set(receipt.corpus_sha256) == prior, "Historical corpus inventory differs")
    require(
        set(receipt.reports_sha256) == PREDECESSOR_REPORTS, "Historical report inventory differs"
    )
    for path, expected in receipt.corpus_sha256.items():
        require(
            file_hash(safe_file(project, path)) == expected, f"Historical corpus changed: {path}"
        )
    return receipt


def validate_frozen(
    directory: Path, project: Path = PROJECT, *, before_measurement: bool = False
) -> tuple[FrozenInputs, list[CorpusCase], dict[str, Any]]:
    selected, cases, provenance, _ = load_real(directory, discovery_policy=CURRENT_POLICY)
    frozen = FrozenInputs.model_validate(read_metadata(safe_file(directory, FREEZE))[0])
    require(set(frozen.analyzer_sha256) == ENGINE, "Frozen v4 engine inventory differs")
    for path, digest in frozen.analyzer_sha256.items():
        require(file_hash(safe_file(project, path)) == digest, f"Frozen analyzer changed: {path}")
    expected = input_files(cases)
    require(set(frozen.files_sha256) == expected, "Frozen v4 input inventory differs")
    actual_paths = sorted(directory.rglob("*"))
    require(not any(p.is_symlink() for p in actual_paths), "Symlink in v4 dataset")
    actual = {p.relative_to(directory).as_posix() for p in actual_paths if p.is_file()}
    receipts = {FREEZE} if before_measurement else {FREEZE, FIRST, BASELINE}
    require(actual == expected | receipts, "Unexpected or missing v4 dataset files")
    total = 0
    for path in sorted(actual):
        file = safe_file(directory, path)
        total += file.stat().st_size
        if path in expected:
            require(
                file_hash(file) == frozen.files_sha256[path], f"Frozen v4 input changed: {path}"
            )
    require(total <= MAX_CORPUS_BYTES, "V4 total size limit exceeded")
    audit = inventories(cases)
    require(read_metadata(safe_file(directory, "discovery.json"))[0] == audit, "V4 discovery drift")
    for case in cases:
        review = provenance[case.id].label_review
        require(
            review.status == "draft", "Frozen v4 labels must declare pending independent review"
        )
        require(
            not case.known_discrepancies.false_positives
            and not case.known_discrepancies.false_negatives
            and not case.expected_unclassified_recommendations,
            "Pre-analysis case contains result expectations",
        )
        require(audit[case.id]["head"]["test_shaped_definition_count"] > 0, "No test-shaped source")
        for side in ("base", "head"):
            notice = safe_file(directory, f"licenses/{case.id}-{side}.txt").read_bytes()
            require(
                notice == getattr(provenance[case.id], side).license.text.encode(),
                "License notice differs from provenance",
            )
    historical_repos = {
        row["repository"].casefold()
        for parent in ("real", "real-v2", "real-v3")
        for row in read_metadata(safe_file(project, f"corpus/{parent}/selection.json"))[0]["cases"]
    }
    require(
        len({case.repository.casefold() for case in selected.cases}) == 3
        and all(case.repository.casefold() not in historical_repos for case in selected.cases),
        "V4 repositories must be previously unused",
    )
    validate_history(directory, project)
    return frozen, cases, audit


def stable_bytes(report: dict[str, Any]) -> bytes:
    return (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()


def attach_coverage(report: dict[str, Any], audit: dict[str, Any]) -> None:
    for case in report["cases"]:
        inv = audit[case["id"]]["head"]
        case.update(
            test_shaped_definition_count=inv["test_shaped_definition_count"],
            outside_discovery=inv["outside_discovery"],
            outside_discovery_count=len(inv["outside_discovery"]),
            unclassified_unselected_count=case["unclassified_test_count"]
            - case["unclassified_recommendation_count"],
            unclassified_unselected_ids=sorted(
                set(case["unclassified_test_ids"]) - set(case["selected_test_ids"])
            ),
        )
    for key, group in [("all", report["summary"]), *report["repositories"].items()]:
        cases = [c for c in report["cases"] if key == "all" or c["repository"] == key]
        group.update(
            test_shaped_definition_count=sum(c["test_shaped_definition_count"] for c in cases),
            outside_discovery_count=sum(c["outside_discovery_count"] for c in cases),
            outside_discovery=[
                {"case": c["id"], "test_id": sid, "reason": reason}
                for c in cases
                for sid, reason in sorted(c["outside_discovery"].items())
            ],
            unclassified_unselected_count=sum(c["unclassified_unselected_count"] for c in cases),
        )


def evaluate_v4(directory: Path) -> dict[str, Any]:
    frozen, cases, audit = validate_frozen(directory)
    first = FirstRun.model_validate(read_metadata(safe_file(directory, FIRST))[0])
    baseline = Baseline.model_validate(read_metadata(safe_file(directory, BASELINE))[0])
    require(
        file_hash(safe_file(directory, FIRST)) == baseline.first_run_sha256,
        "First-run receipt changed",
    )
    require(first.reference_commit == REFERENCE, "First-run engine reference differs")
    require(
        first.frozen_inputs_sha256 == canonical_hash(frozen.model_dump()),
        "First-run freeze differs",
    )
    by_id = {c.id: c for c in cases}
    require(
        set(baseline.annotations) == set(baseline.expected_uncertain_selected) == set(by_id),
        "Baseline case inventory differs",
    )
    for cid, note in baseline.annotations.items():
        expected = baseline.expected_uncertain_selected[cid]
        data = by_id[cid].model_dump() | note.model_dump()
        CorpusCase.model_validate(data | {"expected_unclassified_recommendations": expected})
    report = evaluate_real(directory, discovery_policy=CURRENT_POLICY)
    initial = list(report["evaluation"]["regressions"])
    regressions = []
    if (
        hashlib.sha256(stable_bytes(report)).hexdigest() != first.first_report_sha256
        or measurement(report) != first.measurement
        or initial != first.initial_regressions
    ):
        regressions.append("v4: report differs from the frozen first measurement")
    for item in report["evaluation"]["cases"]:
        cid, observed = item["case"]["id"], item["results"]
        known = baseline.annotations[cid].known_discrepancies
        if (
            set(observed["false_positives"]) != set(known.false_positives)
            or set(observed["false_negatives"]) != set(known.false_negatives)
            or sorted(observed["unclassified_recommendations"])
            != sorted(baseline.expected_uncertain_selected[cid])
        ):
            regressions.append(f"{cid}: discrepancies differ from the v4 baseline")
    report["evaluation"]["regressions"] = regressions
    attach_coverage(report, audit)
    report.update(
        v4_evaluation_schema_version="1.0",
        reference_commit=REFERENCE,
        frozen_inputs_sha256=first.frozen_inputs_sha256,
        first_report_sha256=first.first_report_sha256,
        baseline_sha256=file_hash(safe_file(directory, BASELINE)),
        first_regressions=first.initial_regressions,
        baseline_annotations={cid: note.model_dump() for cid, note in baseline.annotations.items()},
        discovery_policy=CURRENT_POLICY,
        discovery=audit,
        independent_review="pending",
        interpretation="Fresh purposive evaluation against frozen draft source dependency labels. "
        "Outside-discovery definitions are measured separately. No upstream tests were executed.",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    return real_main(
        argv,
        evaluator=evaluate_v4,
        default_corpus=DIRECTORY,
        default_output=Path("reports/real-v4-evaluation.json"),
    )


if __name__ == "__main__":
    raise SystemExit(main())
