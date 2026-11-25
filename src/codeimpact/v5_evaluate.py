"""Replay the source-traceable v5 sample against its frozen first measurement."""

import hashlib
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from codeimpact.corpus import MAX_CORPUS_BYTES, StrictModel, load_corpus
from codeimpact.discovery import CURRENT_POLICY
from codeimpact.evaluate import evaluate
from codeimpact.fresh_evaluate import CURRENT_SOURCES, PROJECT, FirstRun, file_hash, measurement
from codeimpact.holdout_evaluate import safe_file
from codeimpact.real_evaluate import (
    SHA256,
    Exclusion,
    Provenance,
    Selected,
    canonical_hash,
    label_hash,
    read_metadata,
    require,
    summarize,
    validate_revision,
)
from codeimpact.real_evaluate import main as real_main
from codeimpact.v4_evaluate import attach_coverage, inventories, stable_bytes

REFERENCE = "06f8a31b2435f95d5f3b0bbc6b4b70efd1c108b7"
DIRECTORY = Path("datasets/real-v5")
OUTPUT = Path("reports/real-v5-evaluation.json")
FREEZE = "frozen-inputs.json"
FIRST = "first-run.json"
BASELINE = "baseline.json"
DOCUMENTS = {"README.md", "PROTOCOL.md", "CANDIDATES.md", "selection.json", "discovery.json"}
ENGINE = CURRENT_SOURCES | {
    "pyproject.toml",
    "requirements-dev.lock",
    *(
        f"src/codeimpact/{name}.py"
        for name in (
            "corpus",
            "evaluate",
            "explicit_reexports",
            "fresh_evaluate",
            "holdout_evaluate",
            "parameter_rows",
            "pytest_fixtures",
            "real_evaluate",
            "runtime_imports",
            "v4_evaluate",
            "variadic_fallback",
        )
    ),
}


class Selection(StrictModel):
    schema_version: Literal["1.0"]
    policy: str
    cases: list[Selected]
    exclusions: list[Exclusion]


class FrozenInputs(StrictModel):
    schema_version: Literal["1.0"]
    reference_commit: Literal["06f8a31b2435f95d5f3b0bbc6b4b70efd1c108b7"]
    discovery_policy: Literal["test-files-v3"]
    analyzer_sha256: dict[str, SHA256]
    files_sha256: dict[str, SHA256]


class Discrepancies(StrictModel):
    false_positives: list[str]
    false_negatives: list[str]
    uncertain_selected: list[str]


class Baseline(StrictModel):
    schema_version: Literal["1.0"]
    first_run_sha256: SHA256
    expected: dict[str, Discrepancies]


def metadata(directory: Path, name: str) -> Any:
    return read_metadata(safe_file(directory, name))[0]


def validate_frozen(directory: Path, *, before_measurement: bool = False) -> FrozenInputs:
    frozen = FrozenInputs.model_validate(metadata(directory, FREEZE))
    selection = Selection.model_validate(metadata(directory, "selection.json"))
    selected = {case.id: case for case in selection.cases}
    repositories = Counter(case.repository.casefold() for case in selection.cases)
    changes = {(case.repository.casefold(), case.head) for case in selection.cases}
    require(
        len(selection.cases) == len(selected) == len(changes) == 4
        and sorted(repositories.values()) == [2, 2],
        "V5 requires four distinct changes across two repositories",
    )
    historical = {
        row["repository"].casefold()
        for name in ("real", "real-v2", "real-v3", "real-v4")
        for row in metadata(PROJECT / "corpus" / name, "selection.json")["cases"]
    }
    require(not (historical & repositories.keys()), "V5 repository was measured before")

    expected = (
        DOCUMENTS
        | {f"{folder}/{cid}.json" for cid in selected for folder in ("cases", "provenance")}
        | {f"licenses/{cid}-{side}.txt" for cid in selected for side in ("base", "head")}
    )
    require(set(frozen.files_sha256) == expected, "V5 frozen input inventory differs")
    receipts = {FREEZE} if before_measurement else {FREEZE, FIRST, BASELINE}
    paths = list(directory.rglob("*"))
    require(not any(path.is_symlink() for path in paths), "Symlink in v5 dataset")
    actual = {path.relative_to(directory).as_posix() for path in paths if path.is_file()}
    require(actual == expected | receipts, "Unexpected or missing v5 files")
    require(
        sum((directory / path).stat().st_size for path in actual) <= MAX_CORPUS_BYTES,
        "V5 total size limit exceeded",
    )
    for path, digest in sorted(frozen.files_sha256.items()):
        require(file_hash(safe_file(directory, path)) == digest, f"V5 frozen input changed: {path}")

    require(set(frozen.analyzer_sha256) == ENGINE, "V5 reference source inventory differs")
    for path, digest in sorted(frozen.analyzer_sha256.items()):
        require(
            file_hash(safe_file(PROJECT, path)) == digest, f"V5 reference source changed: {path}"
        )
    return frozen


def collect(directory: Path) -> dict[str, Any]:
    """Validate source, receipts and typed evidence before recording a measurement."""
    selection = Selection.model_validate(metadata(directory, "selection.json"))
    selected = {case.id: case for case in selection.cases}
    cases = load_corpus(directory / "cases")
    require({case.id for case in cases} == selected.keys(), "V5 case IDs differ from selection")
    audit = inventories(cases, policy=CURRENT_POLICY)
    require(metadata(directory, "discovery.json") == audit, "V5 discovery drift")

    provenance = {}
    coverage: dict[str, dict[str, Any]] = {}
    for case in cases:
        pin = selected[case.id]
        receipt = Provenance.model_validate(metadata(directory, f"provenance/{case.id}.json"))
        require(
            receipt.id == pin.id
            and receipt.repository == pin.repository
            and receipt.selection_reason == pin.reason
            and receipt.change_url == f"https://github.com/{pin.repository}/commit/{pin.head}",
            f"{case.id}: provenance metadata differs",
        )
        require(
            [p.sha for p in receipt.head.commit.parents] == [pin.base],
            f"{case.id}: single pinned first parent differs",
        )
        require(
            receipt.label_review.status == "draft"
            and receipt.label_review.labels_sha256 == label_hash(case),
            f"{case.id}: draft label receipt differs",
        )
        require(
            bool(case.expected_affected)
            and bool(case.expected_unaffected)
            and not case.known_discrepancies.false_positives
            and not case.known_discrepancies.false_negatives
            and not case.expected_unclassified_recommendations,
            f"{case.id}: invalid pre-analysis labels or result expectations",
        )
        provenance[case.id] = receipt
        coverage[case.id] = {}
        for side in ("base", "head"):
            revision = getattr(receipt, side)
            coverage[case.id][side] = validate_revision(
                getattr(case.request, side),
                revision,
                getattr(pin, side),
                pin.license,
            )
            notice = safe_file(directory, f"licenses/{case.id}-{side}.txt")
            require(
                notice.read_bytes() == revision.license.text.encode(),
                f"{case.id}: {side} license notice differs",
            )

    evaluation = evaluate(cases, fixtures=True, runtime_imports=True)
    results: list[dict[str, Any]] = []
    for result in evaluation.cases:
        case = result.case
        recommendations = result.analysis["recommendations"]
        receipt = provenance[case.id]
        tests = audit[case.id]["head"]["discovered_ids"]
        results.append(
            {
                "id": case.id,
                "repository": receipt.repository,
                "change_url": receipt.change_url,
                "label_review": receipt.label_review.model_dump(),
                "coverage": coverage[case.id],
                "test_count": len(tests),
                "selected_test_ids": sorted(row["symbol"] for row in recommendations),
                "selected_count": len(recommendations),
                "unclassified_test_ids": sorted(case.unclassified),
                "unclassified_test_count": len(case.unclassified),
                "unclassified_recommendation_count": len(
                    result.results.unclassified_recommendations
                ),
                "reason_counts": dict(
                    sorted(Counter(row["reason"] for row in recommendations).items())
                ),
                "metrics": result.results.metrics.model_dump(),
            }
        )
    report = {
        "v5_evaluation_schema_version": "1.0",
        "reference_commit": REFERENCE,
        "independent_review": "skipped",
        "discovery_policy": CURRENT_POLICY,
        "discovery": audit,
        "volatile_fields_excluded": ["evaluation.cases[].analysis.stats.elapsed_ms"],
        "interpretation": "Purposive v5 sample evaluated against draft source dependency labels.",
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


def first_measurement(report: dict[str, Any]) -> dict[str, Any]:
    return measurement(report) | {
        "recommendations": {
            item["case"]["id"]: item["analysis"]["recommendations"]
            for item in report["evaluation"]["cases"]
        },
    }


def discrepancies(report: dict[str, Any]) -> dict[str, Discrepancies]:
    return {
        item["case"]["id"]: Discrepancies(
            false_positives=item["results"]["false_positives"],
            false_negatives=item["results"]["false_negatives"],
            uncertain_selected=item["results"]["unclassified_recommendations"],
        )
        for item in report["evaluation"]["cases"]
    }


def evaluate_v5(directory: Path) -> dict[str, Any]:
    frozen = validate_frozen(directory)
    first = FirstRun.model_validate(metadata(directory, FIRST))
    baseline = Baseline.model_validate(metadata(directory, BASELINE))
    require(
        file_hash(safe_file(directory, FIRST)) == baseline.first_run_sha256,
        "V5 first-run receipt changed",
    )
    require(
        first.reference_commit == REFERENCE
        and first.frozen_inputs_sha256 == canonical_hash(frozen.model_dump()),
        "V5 first-run freeze differs",
    )

    report = collect(directory)
    initial = report["evaluation"]["regressions"]
    regressions = []
    if (
        file_digest(report) != first.first_report_sha256
        or first_measurement(report) != first.measurement
        or initial != first.initial_regressions
    ):
        regressions.append("V5 report differs from the frozen first measurement")
    if discrepancies(report) != baseline.expected:
        regressions.append("V5 discrepancies differ from the recorded baseline")
    report["evaluation"]["regressions"] = regressions
    report.update(
        frozen_inputs_sha256=first.frozen_inputs_sha256,
        first_report_sha256=first.first_report_sha256,
        first_regressions=first.initial_regressions,
        baseline_sha256=file_hash(safe_file(directory, BASELINE)),
    )
    return report


def file_digest(report: dict[str, Any]) -> str:
    return hashlib.sha256(stable_bytes(report)).hexdigest()


def main(argv: list[str] | None = None) -> int:
    return real_main(
        argv,
        evaluator=evaluate_v5,
        default_corpus=DIRECTORY,
        default_output=OUTPUT,
        protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
    )


if __name__ == "__main__":
    raise SystemExit(main())
