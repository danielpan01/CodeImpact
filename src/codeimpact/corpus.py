"""Authored dependency labels and bounded, data-only corpus loading."""

import ast
import json
import re
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from codeimpact.models import AnalysisRequest, Snapshot

MAX_CASE_BYTES = 1_000_000
MAX_CASES = 100
MAX_CORPUS_BYTES = 20_000_000
Nonblank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def discover_tests(snapshot: Snapshot) -> set[str]:
    """Independently apply CodeImpact's discovery rule, without importing source.

    This is not pytest collection. Only direct definitions in modules, classes and
    functions are visited; definitions under conditionals/loops are not indexed.
    """
    found: set[str] = set()

    def visit(path: str, body: list[ast.stmt], prefix: str = "") -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}.{node.name}" if prefix else node.name
                if not isinstance(node, ast.ClassDef) and node.name.startswith("test_"):
                    sid = f"{path}::{name}"
                    if sid in found:
                        raise ValueError(f"Ambiguous duplicate head test: {sid}")
                    found.add(sid)
                visit(path, node.body, name)

    for path, source in sorted(snapshot.files.items()):
        if not (PurePosixPath(path).name.startswith("test_") or path.endswith("_test.py")):
            continue
        try:
            tree = ast.parse(source, filename=path)
        except (SyntaxError, ValueError, RecursionError):
            continue
        visit(path, tree.body)
    return found


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class KnownDiscrepancies(StrictModel):
    false_positives: dict[Nonblank, Nonblank]
    false_negatives: dict[Nonblank, Nonblank]


class CorpusCase(StrictModel):
    schema_version: Literal["1.0"]
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{0,79}$")
    description: Nonblank
    category: Literal["supported", "known_limitation"]
    features: list[Nonblank] = Field(min_length=1)
    request: AnalysisRequest
    expected_affected: dict[Nonblank, Nonblank]
    expected_unaffected: dict[Nonblank, Nonblank]
    unclassified: dict[Nonblank, Nonblank]
    known_discrepancies: KnownDiscrepancies
    expected_unclassified_recommendations: list[Nonblank]
    limitations: list[Nonblank]

    @model_validator(mode="after")
    def validate_labels(self) -> "CorpusCase":
        if len(set(self.features)) != len(self.features):
            raise ValueError("Feature tags must be unique")
        if any(not re.fullmatch(r"[a-z][a-z0-9_]*", tag) for tag in self.features):
            raise ValueError("Feature tags must use lowercase letters, digits and underscores")
        affected, unaffected, unknown = (
            set(self.expected_affected),
            set(self.expected_unaffected),
            set(self.unclassified),
        )
        if affected & unaffected or affected & unknown or unaffected & unknown:
            raise ValueError("Affected, unaffected and unclassified labels must be disjoint")
        tests = discover_tests(self.request.head)
        labels = affected | unaffected | unknown
        if labels - tests:
            raise ValueError(f"Labels must identify a head test: {sorted(labels - tests)}")
        if tests - labels:
            raise ValueError(f"Every head test needs an explicit label: {sorted(tests - labels)}")
        discrepancies = self.known_discrepancies
        if not set(discrepancies.false_positives) <= unaffected:
            raise ValueError("Known false positives must be labeled unaffected")
        if not set(discrepancies.false_negatives) <= affected:
            raise ValueError("Known false negatives must be labeled affected")
        selected_unknown = self.expected_unclassified_recommendations
        if (
            len(set(selected_unknown)) != len(selected_unknown)
            or not set(selected_unknown) <= unknown
        ):
            raise ValueError(
                "Expected unclassified recommendations must be unique unclassified tests"
            )
        if self.category == "supported" and (
            discrepancies.false_positives or discrepancies.false_negatives or self.limitations
        ):
            raise ValueError("Supported cases cannot hide discrepancies or limitation annotations")
        if self.category == "known_limitation" and not self.limitations:
            raise ValueError("Known-limitation cases need an explanation")
        return self


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_corpus(directory: Path) -> list[CorpusCase]:
    """Read bounded JSON files only. Never materialize or execute their snapshots."""
    if directory.is_symlink():
        raise ValueError("Corpus directory must not be a symlink")
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise ValueError(f"No corpus cases in {directory}")
    if len(paths) > MAX_CASES:
        raise ValueError(f"Corpus exceeds {MAX_CASES} cases")
    cases: dict[str, CorpusCase] = {}
    total = 0
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Case must be a regular file, not a symlink: {path.name}")
        with path.open("rb") as stream:
            raw = stream.read(MAX_CASE_BYTES + 1)
        total += len(raw)
        if len(raw) > MAX_CASE_BYTES or total > MAX_CORPUS_BYTES:
            raise ValueError(f"Corpus size limit exceeded at {path.name}")
        try:
            data = json.loads(raw, object_pairs_hook=_unique_object)
            case = CorpusCase.model_validate(data)
        except (ValueError, RecursionError) as exc:
            raise ValueError(f"{path.name}: {exc}") from exc
        if case.id in cases:
            raise ValueError(f"Duplicate case ID: {case.id}")
        cases[case.id] = case
    return [cases[key] for key in sorted(cases)]
