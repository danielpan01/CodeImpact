"""Offline v3 replay: frozen source labels, first measurement and historical receipts."""

import ast
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from codeimpact.corpus import MAX_CORPUS_BYTES, StrictModel, discover_tests
from codeimpact.fresh_evaluate import (
    CURRENT_SOURCES,
    PROJECT,
    CaseBaseline,
    FirstRun,
    file_hash,
    measurement,
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


def discovery_audit(snapshot: Snapshot) -> dict[str, Any]:
    """Count test-shaped source definitions outside discovery; never collect/run tests."""
    discovered = discover_tests(snapshot)
    shaped: set[str] = set()
    unparseable = []

    class Visitor(ast.NodeVisitor):
        def __init__(self, path: str):
            self.path = path
            self.scope: list[str] = []

        def definition(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> None:
            self.scope.append(node.name)
            if not isinstance(node, ast.ClassDef) and node.name.startswith("test_"):
                shaped.add(f"{self.path}::{'.'.join(self.scope)}")
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
    for sid in sorted(shaped - discovered):
        path = sid.split("::", 1)[0]
        supported_name = PurePosixPath(path).name.startswith("test_") or path.endswith("_test.py")
        excluded[sid] = "compound_statement" if supported_name else "unsupported_filename"
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
        if p.is_file() and not p.is_relative_to(project / "corpus/real-v3")
    }
    require(set(receipt.corpus_sha256) == historical, "Historical corpus inventory changed")
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
    require(set(frozen.analyzer_sha256) == CURRENT_SOURCES, "Engine inventory mismatch")
    expected = (
        DOCUMENTS
        | {f"{folder}/{case.id}.json" for case in cases for folder in ("cases", "provenance")}
        | {f"licenses/{case.id}-{side}.txt" for case in cases for side in ("base", "head")}
    )
    require(set(frozen.files_sha256) == expected, "Frozen input inventory mismatch")
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
    require(
        actual <= expected | {"frozen-inputs.json", "first-run.json", "baseline.json"},
        "Unexpected dataset file",
    )
    total = 0
    for path, expected_hash in frozen.files_sha256.items():
        file = safe_file(directory, path)
        require(file_hash(file) == expected_hash, f"Frozen input changed: {path}")
        total += file.stat().st_size
    for path in ("frozen-inputs.json", "first-run.json", "baseline.json"):
        if (directory / path).exists():
            total += read_metadata(directory / path)[1]
    require(total <= MAX_CORPUS_BYTES, "V3 total size limit exceeded")
    for path, expected_hash in frozen.analyzer_sha256.items():
        require(file_hash(safe_file(project, path)) == expected_hash, f"Engine changed: {path}")
    audit = read_metadata(directory / "discovery.json")[0]
    require(
        audit == {case.id: discovery_audit(case.request.head) for case in cases},
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
    baseline = ReplayBaseline.model_validate(read_metadata(directory / "baseline.json")[0])
    require(initial.reference_commit == frozen.reference_commit, "First-run reference mismatch")
    require(
        initial.frozen_inputs_sha256 == canonical_hash(frozen.model_dump()),
        "First-run frozen input mismatch",
    )
    require(
        canonical_hash(initial.model_dump()) == baseline.first_run_sha256,
        "First measurement changed",
    )
    report = evaluate_real(
        directory,
        annotations={key: value.model_dump() for key, value in baseline.annotations.items()},
    )
    matches = measurement(report) == initial.measurement
    if not matches:
        report["evaluation"]["regressions"].append("v3: measurement differs from frozen first run")
    report.update(
        holdout_evaluation_schema_version="1.0",
        active_baseline="first-run",
        first_measurement_matches=matches,
        first_run_sha256=baseline.first_run_sha256,
        frozen_inputs=frozen.model_dump(),
        initial_regressions=initial.initial_regressions,
        discovery=read_metadata(directory / "discovery.json")[0],
        interpretation=(
            "Fresh v3 first measurement replay; agent-drafted source labels, human review pending. "
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
        default_output=Path("reports/real-v3-evaluation.json"),
    )


if __name__ == "__main__":
    raise SystemExit(main())
