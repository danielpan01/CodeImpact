"""Offline v3 replay: frozen source labels, first measurement and historical receipts."""

import ast
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from pydantic import Field

from codeimpact.corpus import MAX_CORPUS_BYTES, Nonblank, StrictModel, discover_tests
from codeimpact.discovery import (
    CURRENT_POLICY,
    LEGACY_POLICY,
    V2_POLICY,
    DiscoveryPolicy,
    is_mixed_case_name,
    is_test_file,
)
from codeimpact.fresh_evaluate import (
    CURRENT_SOURCES,
    DESCRIPTOR_SOURCES,
    DISCOVERY_SOURCES,
    LEGACY_SOURCES,
    MAPPING_BASELINE_FILE,
    MAPPING_SOURCES,
    PROJECT,
    TABLES_SOURCES,
    V3_EMPTY_STRING_GUARD,
    V3_SET_CLEANUP,
    CaseBaseline,
    FirstRun,
    file_hash,
    measurement,
    replay_source_matches,
)
from codeimpact.github import SHA
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

REFERENCE = "25b58040ede56918755a6a83277de98408f3dcb9"
REPORTS = {"corpus-evaluation.json", "real-evaluation.json", "real-v2-evaluation.json"}
DOCUMENTS = {
    "selection.json",
    "PROTOCOL.md",
    "README.md",
    "REVIEW.md",
    "ATTRIBUTION.md",
    "discovery.json",
    "preservation.json",
}
DISCOVERY_BASELINE_FILE = "baselines/test-discovery-v1.json"
LFU_BASELINE_FILE = "baselines/lfu-callback-v1.json"
DESCRIPTOR_BASELINE_FILE = "baselines/descriptor-binding-v1.json"
LEGACY_BASELINE_FILE = "baselines/legacy-dispatch-v1.json"
TABLES_BASELINE_FILE = "baselines/literal-tables-v1.json"
EXPORTS_BASELINE_FILE = "baselines/additive-exports-v1.json"
PARAMETERS_BASELINE_FILE = "baselines/parameter-tables-v1.json"
SET_CLEANUP_BASELINE_FILE = V3_SET_CLEANUP.removeprefix("corpus/real-v3/")
BASELINE_FILE = V3_EMPTY_STRING_GUARD.removeprefix("corpus/real-v3/")
LABELS_FILE = "baselines/test-discovery-v1-labels.json"
V2_DISCOVERY_REPLAY = "corpus/real-v2/baselines/test-discovery-v1.json"
V2_LFU_REPLAY = "corpus/real-v2/baselines/lfu-callback-v1.json"
V2_DESCRIPTOR_REPLAY = "corpus/real-v2/baselines/descriptor-binding-v1.json"
V2_LEGACY_REPLAY = "corpus/real-v2/baselines/legacy-dispatch-v1.json"
V2_TABLES_REPLAY = "corpus/real-v2/baselines/literal-tables-v1.json"
V2_EXPORTS_REPLAY = "corpus/real-v2/baselines/additive-exports-v1.json"
V2_REPLAY = "corpus/real-v2/baselines/parameter-tables-v1.json"


class DraftLabel(StrictModel):
    classification: Literal["affected", "unaffected", "uncertain"]
    rationale: Nonblank
    line: int = Field(ge=1)
    end_line: int = Field(ge=1)


class DiscoveryLabels(StrictModel):
    schema_version: Literal["1.0"]
    name: Literal["test-discovery-v1"]
    policy: Literal["test-files-v2"]
    case: Literal["ordered_set_pop"]
    source_case_sha256: SHA256
    original_discovery_sha256: SHA256
    review_status: Literal["agent_draft"]
    author: Nonblank
    independent_reviewer: None
    timing: Nonblank
    interpretation: Nonblank
    labels: dict[Nonblank, DraftLabel]


class DiscoveryBaseline(StrictModel):
    schema_version: Literal["1.0"]
    name: Literal[
        "test-discovery-v1",
        "lfu-callback-v1",
        "descriptor-binding-v1",
        "legacy-dispatch-v1",
        "literal-tables-v1",
        "additive-exports-v1",
        "parameter-tables-v1",
        "set-cleanup-v1",
        "empty-string-guard-v1",
    ]
    explanation: Nonblank
    frozen_inputs_sha256: SHA256
    previous_baseline_sha256: SHA256
    labels_sha256: SHA256
    v2_replay_sha256: SHA256
    analyzer_sha256: dict[str, SHA256]
    annotations: dict[str, CaseBaseline]
    expected_unclassified_recommendations: list[Nonblank]
    discovery: dict[str, Any]
    measurement: dict[str, Any]


def current_baseline(directory: Path, project: Path = PROJECT) -> DiscoveryBaseline:
    baseline = DiscoveryBaseline.model_validate(
        read_metadata(safe_file(directory, BASELINE_FILE))[0]
    )
    require(baseline.name == "empty-string-guard-v1", "Current baseline name mismatch")
    require(set(baseline.analyzer_sha256) == CURRENT_SOURCES, "Current engine inventory mismatch")
    for path, expected in baseline.analyzer_sha256.items():
        require(replay_source_matches(project, path, expected), f"Engine changed: {path}")
    cleanup_path = safe_file(directory, SET_CLEANUP_BASELINE_FILE)
    require(
        file_hash(cleanup_path) == baseline.previous_baseline_sha256,
        "Preserved set cleanup baseline changed",
    )
    cleanup = DiscoveryBaseline.model_validate(read_metadata(cleanup_path)[0])
    require(cleanup.name == "set-cleanup-v1", "Set cleanup baseline name mismatch")
    require(
        set(cleanup.analyzer_sha256) == CURRENT_SOURCES, "Historical set cleanup engine inventory"
    )
    require(
        cleanup.v2_replay_sha256 == baseline.v2_replay_sha256
        and cleanup.labels_sha256 == baseline.labels_sha256
        and cleanup.frozen_inputs_sha256 == baseline.frozen_inputs_sha256,
        "Set cleanup dependency receipts changed",
    )
    require(
        file_hash(safe_file(directory, PARAMETERS_BASELINE_FILE))
        == cleanup.previous_baseline_sha256,
        "Preserved parameter tables baseline changed",
    )
    parameters = DiscoveryBaseline.model_validate(
        read_metadata(safe_file(directory, PARAMETERS_BASELINE_FILE))[0]
    )
    require(parameters.name == "parameter-tables-v1", "Parameter tables baseline name mismatch")
    require(
        set(parameters.analyzer_sha256) == CURRENT_SOURCES,
        "Historical parameter tables engine inventory",
    )
    require(
        parameters.v2_replay_sha256 == baseline.v2_replay_sha256
        and parameters.labels_sha256 == baseline.labels_sha256
        and parameters.frozen_inputs_sha256 == baseline.frozen_inputs_sha256,
        "Parameter tables dependency receipts changed",
    )
    require(
        file_hash(safe_file(directory, EXPORTS_BASELINE_FILE))
        == parameters.previous_baseline_sha256,
        "Preserved additive exports baseline changed",
    )
    exports = DiscoveryBaseline.model_validate(
        read_metadata(safe_file(directory, EXPORTS_BASELINE_FILE))[0]
    )
    require(exports.name == "additive-exports-v1", "Additive exports baseline name mismatch")
    require(
        set(exports.analyzer_sha256) == CURRENT_SOURCES,
        "Historical additive exports engine inventory",
    )
    require(
        file_hash(safe_file(project, V2_EXPORTS_REPLAY)) == exports.v2_replay_sha256,
        "Historical v2 additive exports receipt changed",
    )
    require(
        file_hash(safe_file(directory, TABLES_BASELINE_FILE)) == exports.previous_baseline_sha256,
        "Preserved literal tables baseline changed",
    )
    tables = DiscoveryBaseline.model_validate(
        read_metadata(safe_file(directory, TABLES_BASELINE_FILE))[0]
    )
    require(tables.name == "literal-tables-v1", "Literal tables baseline name mismatch")
    require(
        set(tables.analyzer_sha256) == TABLES_SOURCES, "Historical literal tables engine inventory"
    )
    require(
        file_hash(safe_file(project, V2_TABLES_REPLAY)) == tables.v2_replay_sha256,
        "Historical v2 literal tables receipt changed",
    )
    require(
        file_hash(safe_file(directory, LEGACY_BASELINE_FILE)) == tables.previous_baseline_sha256,
        "Preserved legacy dispatch baseline changed",
    )
    legacy = DiscoveryBaseline.model_validate(
        read_metadata(safe_file(directory, LEGACY_BASELINE_FILE))[0]
    )
    require(legacy.name == "legacy-dispatch-v1", "Legacy baseline name mismatch")
    require(set(legacy.analyzer_sha256) == LEGACY_SOURCES, "Historical legacy engine inventory")
    require(
        file_hash(safe_file(project, V2_LEGACY_REPLAY)) == legacy.v2_replay_sha256,
        "Historical v2 legacy receipt changed",
    )
    require(
        file_hash(safe_file(directory, DESCRIPTOR_BASELINE_FILE))
        == legacy.previous_baseline_sha256,
        "Preserved descriptor baseline changed",
    )
    descriptor = DiscoveryBaseline.model_validate(
        read_metadata(safe_file(directory, DESCRIPTOR_BASELINE_FILE))[0]
    )
    require(descriptor.name == "descriptor-binding-v1", "Descriptor baseline name mismatch")
    require(
        set(descriptor.analyzer_sha256) == DESCRIPTOR_SOURCES,
        "Historical descriptor engine inventory",
    )
    require(
        file_hash(safe_file(project, V2_DESCRIPTOR_REPLAY)) == descriptor.v2_replay_sha256,
        "Historical v2 descriptor receipt changed",
    )
    require(
        file_hash(safe_file(directory, LFU_BASELINE_FILE)) == descriptor.previous_baseline_sha256,
        "Preserved LFU baseline changed",
    )
    lfu = DiscoveryBaseline.model_validate(
        read_metadata(safe_file(directory, LFU_BASELINE_FILE))[0]
    )
    require(lfu.name == "lfu-callback-v1", "LFU baseline name mismatch")
    require(
        set(lfu.analyzer_sha256) == DISCOVERY_SOURCES, "Historical LFU engine inventory mismatch"
    )
    require(
        file_hash(safe_file(project, V2_LFU_REPLAY)) == lfu.v2_replay_sha256,
        "Historical v2 LFU receipt changed",
    )
    require(
        file_hash(safe_file(directory, DISCOVERY_BASELINE_FILE)) == lfu.previous_baseline_sha256,
        "Preserved discovery baseline changed",
    )
    discovery = DiscoveryBaseline.model_validate(
        read_metadata(safe_file(directory, DISCOVERY_BASELINE_FILE))[0]
    )
    require(discovery.name == "test-discovery-v1", "Discovery baseline name mismatch")
    require(
        set(discovery.analyzer_sha256) == DISCOVERY_SOURCES,
        "Historical discovery engine inventory mismatch",
    )
    require(
        file_hash(safe_file(project, V2_DISCOVERY_REPLAY)) == discovery.v2_replay_sha256,
        "Historical v2 discovery receipt changed",
    )
    require(baseline.labels_sha256 == discovery.labels_sha256, "Discovery label receipt changed")
    require(
        baseline.frozen_inputs_sha256 == discovery.frozen_inputs_sha256, "Discovery freeze changed"
    )
    require(
        file_hash(safe_file(directory, LABELS_FILE)) == baseline.labels_sha256,
        "Discovery labels changed",
    )
    require(
        file_hash(safe_file(directory, "baseline.json")) == discovery.previous_baseline_sha256,
        "Historical first baseline changed",
    )
    require(
        file_hash(safe_file(project, V2_REPLAY)) == baseline.v2_replay_sha256,
        "Versioned v2 replay receipt changed",
    )
    return baseline


def label_extension(
    directory: Path, selected_unknown: list[str]
) -> tuple[DiscoveryLabels, dict[str, dict[str, Any]]]:
    labels = DiscoveryLabels.model_validate(read_metadata(safe_file(directory, LABELS_FILE))[0])
    require(
        file_hash(safe_file(directory, "cases/ordered_set_pop.json")) == labels.source_case_sha256,
        "Discovery label source changed",
    )
    require(
        file_hash(safe_file(directory, "discovery.json")) == labels.original_discovery_sha256,
        "Original discovery inventory changed",
    )
    case = next(c for c in load_real(directory)[1] if c.id == labels.case)
    added = discover_tests(case.request.head, policy=V2_POLICY) - discover_tests(
        case.request.head, policy=LEGACY_POLICY
    )
    require(set(labels.labels) == added, "Expanded label inventory mismatch")
    definitions = {
        f"test.py::{n.name}": n
        for n in ast.parse(case.request.head.files["test.py"]).body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for sid, label in labels.labels.items():
        node = definitions.get(sid)
        require(
            node is not None and (node.lineno, node.end_lineno) == (label.line, label.end_line),
            f"Label source range mismatch: {sid}",
        )
    extension = {
        field: {
            sid: label.rationale
            for sid, label in labels.labels.items()
            if label.classification == category
        }
        for field, category in (
            ("expected_affected", "affected"),
            ("expected_unaffected", "unaffected"),
            ("unclassified", "uncertain"),
        )
    }
    return labels, {
        labels.case: extension | {"expected_unclassified_recommendations": selected_unknown}
    }


class FrozenInputs(StrictModel):
    schema_version: Literal["1.0"]
    reference_commit: SHA
    analyzer_sha256: dict[str, SHA256]
    files_sha256: dict[str, SHA256]


class Preservation(StrictModel):
    schema_version: Literal["1.0"]
    corpus_sha256: dict[str, SHA256]
    reports_sha256: dict[str, SHA256]


class ReplayBaseline(StrictModel):
    schema_version: Literal["1.0"]
    name: Literal["first-run"]
    first_run_sha256: SHA256
    annotations: dict[str, CaseBaseline]


def safe_file(root: Path, relative: str) -> Path:
    """Reject traversal and symlink parents as well as symlink leaf files."""
    path = PurePosixPath(relative)
    require(
        bool(path.parts)
        and not path.is_absolute()
        and str(path) == relative
        and not any(part in {".", ".."} for part in path.parts)
        and not any(char in relative for char in "\\\0:"),
        "Unsafe receipt path",
    )
    current = root
    require(current.is_dir() and not current.is_symlink(), "Unsafe receipt directory")
    for part in path.parts:
        current = current / part
        require(not current.is_symlink(), "Symlink in receipt path")
    require(current.is_file(), f"Missing receipt file: {relative}")
    return current


def discovery_audit(
    snapshot: Snapshot, *, policy: DiscoveryPolicy = CURRENT_POLICY
) -> dict[str, Any]:
    """Count test-shaped source definitions outside discovery; never collect/run tests."""
    discovered = discover_tests(snapshot, policy=policy)
    shaped: set[str] = set()
    mixed: set[str] = set()
    unparseable = []

    class Visitor(ast.NodeVisitor):
        def __init__(self, path: str):
            self.path = path
            self.scope: list[str] = []

        def definition(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> None:
            self.scope.append(node.name)
            if not isinstance(node, ast.ClassDef):
                sid = f"{self.path}::{'.'.join(self.scope)}"
                if node.name.startswith("test_"):
                    shaped.add(sid)
                elif policy == CURRENT_POLICY and is_mixed_case_name(node.name):
                    mixed.add(sid)
            for statement in node.body:
                self.visit(statement)
            self.scope.pop()

        visit_FunctionDef = definition
        visit_AsyncFunctionDef = definition
        visit_ClassDef = definition

    for path, source in sorted(snapshot.files.items()):
        try:
            tree = ast.parse(source, filename=path)
        except (SyntaxError, ValueError, RecursionError):
            unparseable.append(path)
            continue
        Visitor(path).visit(tree)
    excluded = {}
    shaped.update(mixed)
    for sid in sorted(shaped - discovered):
        path = sid.split("::", 1)[0]
        if not is_test_file(path, policy=policy):
            excluded[sid] = "unsupported_filename"
        else:
            excluded[sid] = "unsupported_unittest_scope" if sid in mixed else "compound_statement"
    return {
        "discovered_ids": sorted(discovered),
        "test_shaped_definition_count": len(shaped),
        "outside_discovery": excluded,
        "unparseable_files": unparseable,
    }


def validate_preservation(directory: Path, project: Path = PROJECT) -> Preservation:
    receipt = Preservation.model_validate(read_metadata(directory / "preservation.json")[0])
    historical = {
        p.relative_to(project).as_posix()
        for p in (project / "corpus").rglob("*")
        if p.is_file()
        and not p.is_relative_to(project / "corpus/real-v3")
        and not p.is_relative_to(project / "corpus/real-v4")
        and not p.is_relative_to(project / "corpus/real-v4-successors/unittest-discovery-v1")
        and not p.is_relative_to(project / "corpus/real-v4-successors/variadic-dispatch-v1")
        and not p.is_relative_to(project / "corpus/real-v4-successors/parameter-rows-v1")
        and not p.is_relative_to(project / "corpus/real-v4-successors/explicit-reexports-v1")
    }
    require(
        set(receipt.corpus_sha256)
        | {
            V2_DISCOVERY_REPLAY,
            V2_LFU_REPLAY,
            V2_DESCRIPTOR_REPLAY,
            V2_LEGACY_REPLAY,
            V2_TABLES_REPLAY,
            V2_EXPORTS_REPLAY,
            V2_REPLAY,
        }
        == historical,
        "Historical corpus inventory changed",
    )
    baseline = current_baseline(directory, project)
    require(
        file_hash(safe_file(project, V2_REPLAY)) == baseline.v2_replay_sha256,
        "Versioned v2 replay receipt changed",
    )
    require(set(receipt.reports_sha256) == REPORTS, "Historical report inventory mismatch")
    for path, expected in receipt.corpus_sha256.items():
        require(
            file_hash(safe_file(project, path)) == expected, f"Historical corpus changed: {path}"
        )
    return receipt


def validate_frozen(directory: Path, project: Path = PROJECT) -> FrozenInputs:
    """Validate all frozen bytes before analysis; added receipts share one total budget."""
    selection, cases, provenance, _ = load_real(directory)
    frozen = FrozenInputs.model_validate(read_metadata(directory / "frozen-inputs.json")[0])
    require(frozen.reference_commit == REFERENCE, "Reference engine mismatch")
    require(set(frozen.analyzer_sha256) == MAPPING_SOURCES, "Historical engine inventory mismatch")
    expected = (
        DOCUMENTS
        | {f"{folder}/{case.id}.json" for case in cases for folder in ("cases", "provenance")}
        | {f"licenses/{case.id}-{side}.txt" for case in cases for side in ("base", "head")}
    )
    require(set(frozen.files_sha256) == expected, "Frozen input inventory mismatch")
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
    require(
        actual
        <= expected
        | {
            "frozen-inputs.json",
            "first-run.json",
            "baseline.json",
            DISCOVERY_BASELINE_FILE,
            LFU_BASELINE_FILE,
            DESCRIPTOR_BASELINE_FILE,
            LEGACY_BASELINE_FILE,
            TABLES_BASELINE_FILE,
            EXPORTS_BASELINE_FILE,
            PARAMETERS_BASELINE_FILE,
            SET_CLEANUP_BASELINE_FILE,
            BASELINE_FILE,
            LABELS_FILE,
        },
        "Unexpected dataset file",
    )
    total = 0
    for path, expected_hash in frozen.files_sha256.items():
        file = safe_file(directory, path)
        require(file_hash(file) == expected_hash, f"Frozen input changed: {path}")
        total += file.stat().st_size
    for path in (
        "frozen-inputs.json",
        "first-run.json",
        "baseline.json",
        BASELINE_FILE,
        DISCOVERY_BASELINE_FILE,
        LFU_BASELINE_FILE,
        DESCRIPTOR_BASELINE_FILE,
        LEGACY_BASELINE_FILE,
        TABLES_BASELINE_FILE,
        EXPORTS_BASELINE_FILE,
        PARAMETERS_BASELINE_FILE,
        SET_CLEANUP_BASELINE_FILE,
        LABELS_FILE,
    ):
        if (directory / path).exists():
            total += read_metadata(directory / path)[1]
    require(total <= MAX_CORPUS_BYTES, "V3 total size limit exceeded")
    baseline = current_baseline(directory, project)
    require(
        canonical_hash(frozen.model_dump()) == baseline.frozen_inputs_sha256,
        "Historical frozen receipt changed",
    )
    mapping = read_metadata(safe_file(project, f"corpus/real-v2/{MAPPING_BASELINE_FILE}"))[0]
    require(
        frozen.analyzer_sha256 == mapping["analyzer_sha256"], "Historical engine receipt changed"
    )
    audit = read_metadata(directory / "discovery.json")[0]
    require(
        audit
        == {case.id: discovery_audit(case.request.head, policy=LEGACY_POLICY) for case in cases},
        "Discovery audit mismatch",
    )
    for case in cases:
        for side in ("base", "head"):
            notice = safe_file(directory, f"licenses/{case.id}-{side}.txt").read_bytes()
            require(
                notice == getattr(provenance[case.id], side).license.text.encode("utf-8"),
                "License notice mismatch",
            )
    validate_preservation(directory, project)
    return frozen


def evaluate_holdout(directory: Path) -> dict[str, Any]:
    frozen = validate_frozen(directory)
    initial = FirstRun.model_validate(read_metadata(directory / "first-run.json")[0])
    original = ReplayBaseline.model_validate(read_metadata(directory / "baseline.json")[0])
    baseline = current_baseline(directory)
    require(initial.reference_commit == frozen.reference_commit, "First-run reference mismatch")
    require(
        initial.frozen_inputs_sha256 == canonical_hash(frozen.model_dump()),
        "First-run frozen input mismatch",
    )
    require(
        canonical_hash(initial.model_dump()) == original.first_run_sha256,
        "First measurement changed",
    )
    labels, extensions = label_extension(directory, baseline.expected_unclassified_recommendations)
    discovery = {
        case.id: discovery_audit(case.request.head, policy=V2_POLICY)
        for case in load_real(directory)[1]
    }
    require(discovery == baseline.discovery, "Current discovery audit mismatch")
    report = evaluate_real(
        directory,
        annotations={key: value.model_dump() for key, value in baseline.annotations.items()},
        label_extensions=extensions,
    )
    matches = measurement(report) == initial.measurement
    current_matches = measurement(report) == baseline.measurement
    if not current_matches:
        report["evaluation"]["regressions"].append(
            "v3: measurement differs from empty-string-guard-v1"
        )
    report.update(
        holdout_evaluation_schema_version="10.0",
        previous_baseline="set-cleanup-v1",
        previous_baseline_sha256=baseline.previous_baseline_sha256,
        active_baseline=baseline.name,
        active_baseline_sha256=canonical_hash(baseline.model_dump()),
        current_analyzer_sha256=baseline.analyzer_sha256,
        current_measurement_matches=current_matches,
        original_summary=initial.measurement["summary"],
        original_discovery=read_metadata(directory / "discovery.json")[0],
        discovery_policy=V2_POLICY,
        label_extension=labels.model_dump(),
        first_measurement_matches=matches,
        first_run_sha256=original.first_run_sha256,
        frozen_inputs=frozen.model_dump(),
        initial_regressions=initial.initial_regressions,
        discovery=discovery,
        interpretation=(
            "Versioned v3 empty-string-guard-v1 measurement; prior receipts preserved; "
            "original 90-test first measurement "
            "and excluded inventory preserved. "
            "New source labels were drafted before expanded analysis; human review pending. "
            "The owner deferred the human usability pilot. Preserved mistakes are regression "
            "data, not independent accuracy, test failures or permission to skip tests. "
            "Definitions outside discovery are listed separately and excluded from metrics."
        ),
    )
    return report


def main(argv: list[str] | None = None) -> int:
    return real_main(
        argv,
        evaluator=evaluate_holdout,
        default_corpus=Path("corpus/real-v3"),
        default_output=Path("reports/real-v3-empty-string-guard-v1-evaluation.json"),
    )


if __name__ == "__main__":
    raise SystemExit(main())
