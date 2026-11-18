"""Replay preserved fresh-source inputs against an explicitly versioned regression baseline.

The fresh extension is versioned separately. Existing real dataset reports and
analysis/evaluation contracts are unchanged. No capture or upstream execution occurs.
"""

import hashlib
from pathlib import Path
from typing import Any, Literal

from pydantic import model_validator

from codeimpact.corpus import MAX_CORPUS_BYTES, KnownDiscrepancies, Nonblank, StrictModel
from codeimpact.github import SHA
from codeimpact.real_evaluate import (
    MAX_METADATA_BYTES,
    SHA256,
    canonical_hash,
    evaluate_real,
    label_hash,
    load_real,
    read_metadata,
    require,
)
from codeimpact.real_evaluate import (
    main as real_main,
)

PROJECT = Path(__file__).resolve().parents[2]
FROZEN_SOURCES = frozenset(
    f"src/codeimpact/{name}.py"
    for name in ("__init__", "analyzer", "selection", "arguments", "models", "github")
)

PARTIAL_BASELINE_FILE = "baselines/module-partial-v1.json"
ARGUMENT_BASELINE_FILE = "baselines/argument-guards-v1.json"
MAPPING_BASELINE_FILE = "baselines/mapping-fallback-v1.json"
DISCOVERY_BASELINE_FILE = "baselines/test-discovery-v1.json"
LFU_BASELINE_FILE = "baselines/lfu-callback-v1.json"
DESCRIPTOR_BASELINE_FILE = "baselines/descriptor-binding-v1.json"
LEGACY_BASELINE_FILE = "baselines/legacy-dispatch-v1.json"
TABLES_BASELINE_FILE = "baselines/literal-tables-v1.json"
EXPORTS_BASELINE_FILE = "baselines/additive-exports-v1.json"
BASELINE_FILE = "baselines/parameter-tables-v1.json"
PARTIAL_SOURCES = FROZEN_SOURCES | {"src/codeimpact/partial_bindings.py"}
ARGUMENT_SOURCES = PARTIAL_SOURCES | {"src/codeimpact/call_arguments.py"}
MAPPING_SOURCES = ARGUMENT_SOURCES | {"src/codeimpact/mapping_protocols.py"}
DISCOVERY_SOURCES = MAPPING_SOURCES | {"src/codeimpact/discovery.py"}
DESCRIPTOR_SOURCES = DISCOVERY_SOURCES | {"src/codeimpact/descriptor_binding.py"}
LEGACY_SOURCES = DESCRIPTOR_SOURCES | {"src/codeimpact/dispatch_fallback.py"}
TABLES_SOURCES = LEGACY_SOURCES | {"src/codeimpact/module_data.py"}
CURRENT_SOURCES = TABLES_SOURCES | {"src/codeimpact/additive_exports.py"}


class FrozenCase(StrictModel):
    snapshots_sha256: SHA256
    labels_sha256: SHA256


class FrozenInputs(StrictModel):
    schema_version: Literal["1.0"]
    reference_commit: SHA
    analyzer_sha256: dict[str, SHA256]
    selection_sha256: SHA256
    cases: dict[str, FrozenCase]
    review_pack_sha256: SHA256

    @model_validator(mode="after")
    def source_inventory(self) -> "FrozenInputs":
        require(set(self.analyzer_sha256) == FROZEN_SOURCES, "Frozen analyzer source inventory")
        return self


class FirstRun(StrictModel):
    schema_version: Literal["1.0"]
    reference_commit: SHA
    frozen_inputs_sha256: SHA256
    first_report_sha256: SHA256
    initial_regressions: list[str]
    measurement: dict[str, Any]


class CaseBaseline(StrictModel):
    category: Literal["supported", "known_limitation"]
    known_discrepancies: KnownDiscrepancies
    limitations: list[Nonblank]


class RegressionBaseline(StrictModel):
    schema_version: Literal["1.0"]
    name: Literal[
        "module-partial-v1",
        "argument-guards-v1",
        "mapping-fallback-v1",
        "test-discovery-v1",
        "lfu-callback-v1",
        "descriptor-binding-v1",
        "legacy-dispatch-v1",
        "literal-tables-v1",
        "additive-exports-v1",
        "parameter-tables-v1",
    ]
    previous_baseline_sha256: SHA256 | None = None
    explanation: Nonblank
    frozen_inputs_sha256: SHA256
    first_run_sha256: SHA256
    original_cases_sha256: dict[str, SHA256]
    historical_files_sha256: dict[str, SHA256]
    analyzer_sha256: dict[str, SHA256]
    annotations: dict[str, CaseBaseline]
    measurement: dict[str, Any]

    @model_validator(mode="after")
    def source_inventory(self) -> "RegressionBaseline":
        sources = {
            "module-partial-v1": PARTIAL_SOURCES,
            "argument-guards-v1": ARGUMENT_SOURCES,
            "mapping-fallback-v1": MAPPING_SOURCES,
            "test-discovery-v1": DISCOVERY_SOURCES,
            "lfu-callback-v1": DISCOVERY_SOURCES,
            "descriptor-binding-v1": DESCRIPTOR_SOURCES,
            "legacy-dispatch-v1": LEGACY_SOURCES,
            "literal-tables-v1": TABLES_SOURCES,
            "additive-exports-v1": CURRENT_SOURCES,
            "parameter-tables-v1": CURRENT_SOURCES,
        }
        require(
            set(self.analyzer_sha256) == sources[self.name],
            "Current analyzer source inventory",
        )
        require(
            (self.name != "module-partial-v1") == (self.previous_baseline_sha256 is not None),
            "Previous baseline receipt",
        )
        return self


def active_baseline(directory: Path, project: Path = PROJECT) -> RegressionBaseline:
    baseline = RegressionBaseline.model_validate(read_metadata(directory / BASELINE_FILE)[0])
    require(baseline.name == "parameter-tables-v1", "Active baseline name mismatch")
    require(
        file_hash(directory / EXPORTS_BASELINE_FILE) == baseline.previous_baseline_sha256,
        "Preserved additive exports baseline changed",
    )
    exports = RegressionBaseline.model_validate(read_metadata(directory / EXPORTS_BASELINE_FILE)[0])
    require(exports.name == "additive-exports-v1", "Additive exports baseline name mismatch")
    require(
        file_hash(directory / TABLES_BASELINE_FILE) == exports.previous_baseline_sha256,
        "Preserved literal tables baseline changed",
    )
    tables = RegressionBaseline.model_validate(read_metadata(directory / TABLES_BASELINE_FILE)[0])
    require(tables.name == "literal-tables-v1", "Literal tables baseline name mismatch")
    require(
        file_hash(directory / LEGACY_BASELINE_FILE) == tables.previous_baseline_sha256,
        "Preserved legacy dispatch baseline changed",
    )
    legacy = RegressionBaseline.model_validate(read_metadata(directory / LEGACY_BASELINE_FILE)[0])
    require(legacy.name == "legacy-dispatch-v1", "Legacy baseline name mismatch")
    require(
        file_hash(directory / DESCRIPTOR_BASELINE_FILE) == legacy.previous_baseline_sha256,
        "Preserved descriptor baseline changed",
    )
    descriptor = RegressionBaseline.model_validate(
        read_metadata(directory / DESCRIPTOR_BASELINE_FILE)[0]
    )
    require(descriptor.name == "descriptor-binding-v1", "Descriptor baseline name mismatch")
    require(
        file_hash(directory / LFU_BASELINE_FILE) == descriptor.previous_baseline_sha256,
        "Preserved LFU baseline changed",
    )
    lfu = RegressionBaseline.model_validate(read_metadata(directory / LFU_BASELINE_FILE)[0])
    require(lfu.name == "lfu-callback-v1", "LFU baseline name mismatch")
    require(
        file_hash(directory / DISCOVERY_BASELINE_FILE) == lfu.previous_baseline_sha256,
        "Preserved discovery baseline changed",
    )
    discovery = RegressionBaseline.model_validate(
        read_metadata(directory / DISCOVERY_BASELINE_FILE)[0]
    )
    require(discovery.name == "test-discovery-v1", "Discovery baseline name mismatch")
    require(
        file_hash(directory / MAPPING_BASELINE_FILE) == discovery.previous_baseline_sha256,
        "Preserved mapping baseline changed",
    )
    mapping = RegressionBaseline.model_validate(read_metadata(directory / MAPPING_BASELINE_FILE)[0])
    require(mapping.name == "mapping-fallback-v1", "Mapping baseline name mismatch")
    require(
        file_hash(directory / ARGUMENT_BASELINE_FILE) == mapping.previous_baseline_sha256,
        "Preserved argument baseline changed",
    )
    argument = RegressionBaseline.model_validate(
        read_metadata(directory / ARGUMENT_BASELINE_FILE)[0]
    )
    require(argument.name == "argument-guards-v1", "Previous baseline name mismatch")
    require(
        file_hash(directory / PARTIAL_BASELINE_FILE) == argument.previous_baseline_sha256,
        "Preserved partial baseline changed",
    )
    previous = RegressionBaseline.model_validate(
        read_metadata(directory / PARTIAL_BASELINE_FILE)[0]
    )
    require(previous.name == "module-partial-v1", "Previous baseline name mismatch")
    for path, expected in sorted(baseline.analyzer_sha256.items()):
        require(file_hash(project / path) == expected, f"Current analyzer mismatch: {path}")
    return baseline


def file_hash(path: Path) -> str:
    require(path.is_file() and not path.is_symlink(), f"Expected regular file: {path.name}")
    # Same bound as other metadata, including review packs and local engine source.
    with path.open("rb") as stream:
        raw = stream.read(MAX_METADATA_BYTES + 1)
    require(len(raw) <= MAX_METADATA_BYTES, "Frozen file size limit exceeded")
    return hashlib.sha256(raw).hexdigest()


def validate_frozen(directory: Path, project: Path = PROJECT) -> FrozenInputs:
    """Validate original inputs and the separately pinned current engine; retain old hashes."""
    selection, cases, _, _ = load_real(directory)
    frozen = FrozenInputs.model_validate(read_metadata(directory / "frozen-inputs.json")[0])
    require(
        canonical_hash(selection.model_dump()) == frozen.selection_sha256,
        "Frozen selection mismatch",
    )
    require(set(frozen.cases) == {c.id for c in cases}, "Frozen case inventory mismatch")
    for case in cases:
        receipt = frozen.cases[case.id]
        require(
            canonical_hash(case.request.model_dump()) == receipt.snapshots_sha256,
            f"Frozen snapshots mismatch: {case.id}",
        )
        require(label_hash(case) == receipt.labels_sha256, f"Frozen labels mismatch: {case.id}")
    require(
        file_hash(directory / "REVIEW.md") == frozen.review_pack_sha256,
        "Frozen source-only review pack mismatch",
    )
    baseline = active_baseline(directory, project)
    require(
        canonical_hash(frozen.model_dump()) == baseline.frozen_inputs_sha256,
        "Original frozen-input receipt mismatch",
    )
    require(
        set(baseline.original_cases_sha256) == set(frozen.cases), "Original case inventory mismatch"
    )
    for case in cases:
        require(
            canonical_hash(case.model_dump()) == baseline.original_cases_sha256[case.id],
            f"Original case annotations changed: {case.id}",
        )
    return frozen


def measurement(report: dict[str, Any]) -> dict[str, Any]:
    """Keep the first measured selections, mistakes and evidence hashes, not annotations."""
    return {
        "summary": report["summary"],
        "repositories": report["repositories"],
        "cases": report["cases"],
        "classifications": {
            item["case"]["id"]: item["results"] for item in report["evaluation"]["cases"]
        },
        "analysis_sha256": {
            item["case"]["id"]: canonical_hash(item["analysis"])
            for item in report["evaluation"]["cases"]
        },
    }


def uncertainty_counts(group: dict[str, Any]) -> dict[str, int]:
    total = group["unclassified_test_count"]
    selected = group["unclassified_recommendation_count"]
    return {"total": total, "selected": selected, "unselected": total - selected}


def evaluate_fresh(directory: Path) -> dict[str, Any]:
    frozen = validate_frozen(directory)
    baseline = active_baseline(directory)
    # Include the added receipts/review pack in the existing metadata total budget.
    metadata_paths = [
        directory / name
        for name in (
            "selection.json",
            "frozen-inputs.json",
            "first-run.json",
            BASELINE_FILE,
            EXPORTS_BASELINE_FILE,
            TABLES_BASELINE_FILE,
            LEGACY_BASELINE_FILE,
            DESCRIPTOR_BASELINE_FILE,
            LFU_BASELINE_FILE,
            DISCOVERY_BASELINE_FILE,
            MAPPING_BASELINE_FILE,
            ARGUMENT_BASELINE_FILE,
            PARTIAL_BASELINE_FILE,
        )
    ] + sorted((directory / "provenance").glob("*.json"))
    total = sum(read_metadata(path)[1] for path in metadata_paths)
    total += (directory / "REVIEW.md").stat().st_size
    require(total <= MAX_CORPUS_BYTES, "Fresh metadata total size limit exceeded")
    initial = FirstRun.model_validate(read_metadata(directory / "first-run.json")[0])
    require(initial.reference_commit == frozen.reference_commit, "First-run reference mismatch")
    require(
        initial.frozen_inputs_sha256 == canonical_hash(frozen.model_dump()),
        "First-run frozen-input receipt mismatch",
    )
    require(
        canonical_hash(initial.model_dump()) == baseline.first_run_sha256,
        "Original first-run measurement changed",
    )
    report = evaluate_real(
        directory,
        annotations={key: value.model_dump() for key, value in baseline.annotations.items()},
    )
    observed = measurement(report)
    matches = observed == initial.measurement
    current_matches = observed == baseline.measurement
    if not current_matches:
        report["evaluation"]["regressions"].append(
            "v2: measurement differs from parameter-tables-v1"
        )
    argument = RegressionBaseline.model_validate(
        read_metadata(directory / ARGUMENT_BASELINE_FILE)[0]
    )
    previous = RegressionBaseline.model_validate(
        read_metadata(directory / EXPORTS_BASELINE_FILE)[0]
    )
    tables = RegressionBaseline.model_validate(read_metadata(directory / TABLES_BASELINE_FILE)[0])
    legacy = RegressionBaseline.model_validate(read_metadata(directory / LEGACY_BASELINE_FILE)[0])
    descriptor = RegressionBaseline.model_validate(
        read_metadata(directory / DESCRIPTOR_BASELINE_FILE)[0]
    )
    lfu = RegressionBaseline.model_validate(read_metadata(directory / LFU_BASELINE_FILE)[0])
    discovery = RegressionBaseline.model_validate(
        read_metadata(directory / DISCOVERY_BASELINE_FILE)[0]
    )
    mapping = RegressionBaseline.model_validate(read_metadata(directory / MAPPING_BASELINE_FILE)[0])
    partial = RegressionBaseline.model_validate(read_metadata(directory / PARTIAL_BASELINE_FILE)[0])
    report.update(
        fresh_evaluation_schema_version="11.0",
        previous_baseline=previous.name,
        previous_baseline_sha256=baseline.previous_baseline_sha256,
        previous_summary=previous.measurement["summary"],
        tables_baseline=tables.name,
        tables_baseline_sha256=previous.previous_baseline_sha256,
        tables_summary=tables.measurement["summary"],
        legacy_baseline=legacy.name,
        legacy_baseline_sha256=tables.previous_baseline_sha256,
        legacy_summary=legacy.measurement["summary"],
        descriptor_baseline=descriptor.name,
        descriptor_baseline_sha256=legacy.previous_baseline_sha256,
        descriptor_summary=descriptor.measurement["summary"],
        lfu_baseline=lfu.name,
        lfu_baseline_sha256=descriptor.previous_baseline_sha256,
        lfu_summary=lfu.measurement["summary"],
        discovery_baseline=discovery.name,
        discovery_baseline_sha256=lfu.previous_baseline_sha256,
        discovery_summary=discovery.measurement["summary"],
        mapping_baseline=mapping.name,
        mapping_baseline_sha256=discovery.previous_baseline_sha256,
        mapping_summary=mapping.measurement["summary"],
        partial_baseline=partial.name,
        argument_baseline=argument.name,
        argument_baseline_sha256=mapping.previous_baseline_sha256,
        argument_summary=argument.measurement["summary"],
        partial_baseline_sha256=argument.previous_baseline_sha256,
        partial_summary=partial.measurement["summary"],
        active_baseline=baseline.name,
        active_baseline_sha256=canonical_hash(baseline.model_dump()),
        current_analyzer_sha256=baseline.analyzer_sha256,
        current_measurement_matches=current_matches,
        original_summary=initial.measurement["summary"],
        original_annotations_preserved=True,
        frozen_inputs=frozen.model_dump(),
        first_run_sha256=canonical_hash(initial.model_dump()),
        first_measurement_matches=matches,
        uncertainty={
            "overall": uncertainty_counts(report["summary"]),
            "repositories": {
                repo: uncertainty_counts(group) for repo, group in report["repositories"].items()
            },
            "cases": {
                case["id"]: {
                    **uncertainty_counts(case),
                    "unselected_test_ids": sorted(
                        set(case["unclassified_test_ids"]) - set(case["selected_test_ids"])
                    ),
                }
                for case in report["cases"]
            },
        },
        interpretation=(
            "Development/regression evaluation with parameter-tables-v1; "
            "original bef99db first run, module-partial-v1, argument-guards-v1 "
            "mapping-fallback-v1, test-discovery-v1, lfu-callback-v1 and "
            "descriptor-binding-v1, legacy-dispatch-v1, literal-tables-v1 and "
            "additive-exports-v1 preserved. "
            "agent-drafted labels, not independent review or runtime failures. "
            "Matching the baseline preserves mistakes; it does not certify safe test skipping."
        ),
    )
    return report


def main(argv: list[str] | None = None) -> int:
    return real_main(
        argv,
        evaluator=evaluate_fresh,
        default_corpus=Path("corpus/real-v2"),
        default_output=Path("reports/real-v2-parameter-tables-v1-evaluation.json"),
    )


if __name__ == "__main__":
    raise SystemExit(main())
