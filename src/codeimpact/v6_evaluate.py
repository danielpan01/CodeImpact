"""Offline replay of the frozen v6 sample on the merged reference analyzer."""

from collections import Counter
from pathlib import Path
from typing import Any, Literal

from codeimpact.corpus import MAX_CORPUS_BYTES, Nonblank, StrictModel
from codeimpact.discovery import CURRENT_POLICY
from codeimpact.evaluate import evaluate
from codeimpact.fresh_evaluate import PROJECT, FirstRun, file_hash
from codeimpact.github import SHA
from codeimpact.holdout_evaluate import safe_file
from codeimpact.real_evaluate import (
    SHA256,
    Selection,
    canonical_hash,
    load_real,
    require,
    summarize,
)
from codeimpact.real_evaluate import main as real_main
from codeimpact.v4_evaluate import attach_coverage, inventories
from codeimpact.v5_evaluate import Baseline, discrepancies, file_digest, first_measurement, metadata

REFERENCE = "060547c3375a999eb4bc8d582cff9883f7c39ef5"
DIRECTORY = Path("datasets/real-v6")
OUTPUT = Path("reports/real-v6-evaluation.json")
FREEZE = "frozen-inputs.json"
FIRST = "first-run.json"
BASELINE = "baseline.json"
DOCUMENTS = {
    "README.md",
    "PROTOCOL.md",
    "CANDIDATES.md",
    "REVIEW.md",
    "analyzer.json",
    "candidates.json",
    "selection.json",
    "discovery.json",
}


class Candidate(StrictModel):
    revision: SHA
    parents: list[SHA]
    subject: Nonblank
    reason: Nonblank
    case_id: Nonblank | None


class CandidateRepository(StrictModel):
    repository: Nonblank
    default_branch: Nonblank
    commits: list[Candidate]


class CandidateInventory(StrictModel):
    schema_version: Literal["1.0"]
    cutoff: Literal["2025-10-01T00:00:00Z"]
    repositories: list[CandidateRepository]


class FrozenInputs(StrictModel):
    schema_version: Literal["1.0"]
    reference_commit: Literal["060547c3375a999eb4bc8d582cff9883f7c39ef5"]
    discovery_policy: Literal["test-files-v3"]
    files_sha256: dict[str, SHA256]


class FrozenAnalyzer(StrictModel):
    schema_version: Literal["1.0"]
    reference_commit: Literal["060547c3375a999eb4bc8d582cff9883f7c39ef5"]
    sources_sha256: dict[str, SHA256]


def validate_selection(directory: Path, selection: Selection) -> None:
    prior_directories = [
        *(PROJECT / "corpus" / version for version in ("real", "real-v2", "real-v3", "real-v4")),
        PROJECT / "datasets/real-v5",
    ]
    historical = {
        case["repository"].casefold()
        for root in prior_directories
        for case in metadata(root, "selection.json")["cases"]
    }
    repositories = list(dict.fromkeys(case.repository for case in selection.cases))
    require(
        len({repo.casefold() for repo in repositories}) == 3
        and historical.isdisjoint(repo.casefold() for repo in repositories),
        "V6 requires three repositories unused in v1–v5",
    )

    candidates = CandidateInventory.model_validate(metadata(directory, "candidates.json"))
    require(
        [row.repository for row in candidates.repositories] == repositories,
        "V6 candidate repository order differs",
    )
    selected = []
    excluded = []
    for row in candidates.repositories:
        require(
            1 <= len(row.commits) <= 60
            and len({item.revision for item in row.commits}) == len(row.commits)
            and sum(item.case_id is not None for item in row.commits) == 2
            and row.commits[-1].case_id is not None,
            f"{row.repository}: invalid inspected prefix",
        )
        for item in row.commits:
            if item.case_id is None:
                excluded.append((row.repository, item.revision, item.reason))
            else:
                require(len(item.parents) == 1, f"{item.case_id}: expected one first parent")
                selected.append(
                    (item.case_id, row.repository, item.parents[0], item.revision, item.reason)
                )
    require(
        selected
        == [
            (case.id, case.repository, case.base, case.head, case.reason)
            for case in selection.cases
        ]
        and excluded
        == [(item.repository, item.revision, item.reason) for item in selection.exclusions],
        "V6 candidate decisions differ from selection",
    )


def validate_frozen(directory: Path, *, before_measurement: bool = False) -> FrozenInputs:
    frozen = FrozenInputs.model_validate(metadata(directory, FREEZE))
    selection = Selection.model_validate(metadata(directory, "selection.json"))
    expected = (
        DOCUMENTS
        | {
            f"{folder}/{case.id}.json"
            for case in selection.cases
            for folder in ("cases", "provenance")
        }
        | {
            f"licenses/{case.id}-{side}.txt"
            for case in selection.cases
            for side in ("base", "head")
        }
    )
    require(set(frozen.files_sha256) == expected, "V6 frozen input inventory differs")

    paths = list(directory.rglob("*"))
    require(not any(path.is_symlink() for path in paths), "Symlink in v6 dataset")
    actual = {path.relative_to(directory).as_posix() for path in paths if path.is_file()}
    receipts = {FREEZE} if before_measurement else {FREEZE, FIRST, BASELINE}
    require(actual == expected | receipts, "Unexpected or missing v6 files")
    require(
        sum((directory / path).stat().st_size for path in actual) <= MAX_CORPUS_BYTES,
        "V6 total size limit exceeded",
    )
    for path, digest in sorted(frozen.files_sha256.items()):
        require(file_hash(safe_file(directory, path)) == digest, f"V6 frozen input changed: {path}")

    analyzer = FrozenAnalyzer.model_validate(metadata(directory, "analyzer.json"))
    require(
        len(analyzer.sources_sha256) == 61
        and {"src/codeimpact/analyzer.py", "pyproject.toml", "requirements-dev.lock"}
        <= analyzer.sources_sha256.keys(),
        "V6 reference source inventory differs",
    )
    for path, digest in sorted(analyzer.sources_sha256.items()):
        require(
            file_hash(safe_file(PROJECT, path)) == digest, f"V6 reference source changed: {path}"
        )
    validate_selection(directory, selection)
    return frozen


def collect(directory: Path) -> dict[str, Any]:
    selection, cases, provenance, coverage = load_real(directory, discovery_policy=CURRENT_POLICY)
    selected = {case.id: case for case in selection.cases}
    audit = inventories(cases, policy=CURRENT_POLICY)
    require(metadata(directory, "discovery.json") == audit, "V6 discovery drift")
    for case in cases:
        receipt = provenance[case.id]
        pin = selected[case.id]
        require(
            [parent.sha for parent in receipt.head.commit.parents] == [pin.base],
            f"{case.id}: single first parent differs",
        )
        require(
            receipt.label_review.status == "draft", f"{case.id}: expected a draft label receipt"
        )
        require(
            bool(case.expected_affected)
            and bool(case.expected_unaffected)
            and len(audit[case.id]["head"]["discovered_ids"]) <= 120
            and not case.known_discrepancies.false_positives
            and not case.known_discrepancies.false_negatives
            and not case.expected_unclassified_recommendations,
            f"{case.id}: invalid pre-analysis labels, coverage, or result expectations",
        )
        for side in ("base", "head"):
            notice = safe_file(directory, f"licenses/{case.id}-{side}.txt")
            revision = getattr(receipt, side)
            require(
                notice.read_bytes() == revision.license.text.encode(),
                f"{case.id}: {side} license notice differs",
            )

    # These settings match the merged analyzer's defaults for user requests.
    evaluation = evaluate(cases, fixtures=True, runtime_imports=True, equality=True)
    results: list[dict[str, Any]] = []
    for item in evaluation.cases:
        case = item.case
        cid = case.id
        rows = item.analysis["recommendations"]
        receipt = provenance[cid]
        results.append(
            {
                "id": cid,
                "repository": receipt.repository,
                "change_url": receipt.change_url,
                "label_review": receipt.label_review.model_dump(),
                "coverage": coverage[cid],
                "test_count": len(audit[cid]["head"]["discovered_ids"]),
                "selected_test_ids": sorted(row["symbol"] for row in rows),
                "selected_count": len(rows),
                "unclassified_test_ids": sorted(case.unclassified),
                "unclassified_test_count": len(case.unclassified),
                "unclassified_recommendation_count": len(item.results.unclassified_recommendations),
                "reason_counts": dict(sorted(Counter(row["reason"] for row in rows).items())),
                "metrics": item.results.metrics.model_dump(),
            }
        )
    report = {
        "v6_evaluation_schema_version": "1.0",
        "reference_commit": REFERENCE,
        "independent_review": "pending",
        "discovery_policy": CURRENT_POLICY,
        "discovery": audit,
        "volatile_fields_excluded": ["evaluation.cases[].analysis.stats.elapsed_ms"],
        "interpretation": "Purposive v6 sample evaluated against draft source dependency labels.",
        "cases": results,
        "summary": summarize(results),
        "repositories": {
            repo: summarize([case for case in results if case["repository"] == repo])
            for repo in sorted({case["repository"] for case in results})
        },
        "evaluation": evaluation.model_dump(mode="json"),
    }
    attach_coverage(report, audit)
    return report


def evaluate_v6(directory: Path) -> dict[str, Any]:
    frozen = validate_frozen(directory)
    first = FirstRun.model_validate(metadata(directory, FIRST))
    baseline = Baseline.model_validate(metadata(directory, BASELINE))
    require(
        file_hash(safe_file(directory, FIRST)) == baseline.first_run_sha256, "V6 first run changed"
    )
    require(
        first.reference_commit == REFERENCE
        and first.frozen_inputs_sha256 == canonical_hash(frozen.model_dump()),
        "V6 first-run freeze differs",
    )

    report = collect(directory)
    initial = report["evaluation"]["regressions"]
    regressions = []
    if (
        file_digest(report) != first.first_report_sha256
        or first_measurement(report) != first.measurement
        or initial != first.initial_regressions
    ):
        regressions.append("V6 report differs from the frozen first measurement")
    if discrepancies(report) != baseline.expected:
        regressions.append("V6 discrepancies differ from the recorded baseline")
    report["evaluation"]["regressions"] = regressions
    report.update(
        frozen_inputs_sha256=first.frozen_inputs_sha256,
        first_report_sha256=first.first_report_sha256,
        first_regressions=first.initial_regressions,
        baseline_sha256=file_hash(safe_file(directory, BASELINE)),
    )
    return report


def main(argv: list[str] | None = None) -> int:
    return real_main(
        argv,
        evaluator=evaluate_v6,
        default_corpus=DIRECTORY,
        default_output=OUTPUT,
        protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
    )


if __name__ == "__main__":
    raise SystemExit(main())
