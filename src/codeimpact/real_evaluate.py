"""Offline evaluation of pinned real Python trees against explicitly reviewed/draft labels.

This wrapper leaves evaluation 1.0 and analysis 2.0 unchanged. No upstream source
is imported, executed, unpacked, or written as an importable Python module.
"""

import argparse
import hashlib
import json
import sys
import tempfile
from collections import Counter, defaultdict
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from codeimpact.corpus import (
    MAX_CORPUS_BYTES,
    CorpusCase,
    Nonblank,
    StrictModel,
    _unique_object,
    load_corpus,
)
from codeimpact.evaluate import Counts, evaluate, metrics
from codeimpact.github import (
    EXCLUDED_DIRS,
    MAX_TREE_ENTRIES,
    REPOSITORY,
    SHA,
    Commit,
    ObjectID,
    Tree,
)
from codeimpact.models import Snapshot

MAX_METADATA_BYTES = 4_000_000
SHA256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
CaseID = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,79}$")]


def canonical_hash(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def blob_hash(raw: bytes, kind: str = "blob") -> str:
    return hashlib.sha1(f"{kind} {len(raw)}\0".encode() + raw).hexdigest()


def label_hash(case: CorpusCase) -> str:
    return canonical_hash(
        {
            name: getattr(case, name)
            for name in ("expected_affected", "expected_unaffected", "unclassified")
        }
    )


class Selected(StrictModel):
    id: CaseID
    repository: str
    base: SHA
    head: SHA
    license: Literal["MIT", "BSD-3-Clause"]
    reason: Nonblank

    @model_validator(mode="after")
    def repository_name(self) -> "Selected":
        if not REPOSITORY.fullmatch(self.repository) or self.repository.split("/")[1] in {
            ".",
            "..",
        }:
            raise ValueError("Invalid repository identity")
        if self.base == self.head:
            raise ValueError("A source change requires different pinned revisions")
        return self


class Exclusion(StrictModel):
    repository: Nonblank
    revision: SHA
    reason: Nonblank


class Selection(StrictModel):
    schema_version: Literal["1.0"]
    policy: Nonblank
    cases: list[Selected]
    exclusions: list[Exclusion]

    @model_validator(mode="after")
    def pilot_size(self) -> "Selection":
        repos = Counter(case.repository for case in self.cases)
        changes = {(case.repository, case.base, case.head) for case in self.cases}
        if (
            len(self.cases) != 6
            or len({case.id for case in self.cases}) != 6
            or len(changes) != 6
            or len(repos) != 3
            or set(repos.values()) != {2}
        ):
            raise ValueError("v1 requires six unique changes, two each across three repositories")
        return self


class CapturedCommit(Commit):
    parents: list[ObjectID]
    message: str


class License(StrictModel):
    path: Nonblank
    spdx: Literal["MIT", "BSD-3-Clause"]
    text: str = Field(min_length=1)
    sha256: SHA256


class RevisionReceipt(StrictModel):
    commit: CapturedCommit
    tree: Tree
    source_sha256: dict[str, SHA256]
    license: License


class LabelReview(StrictModel):
    status: Literal["draft", "reviewed"]
    author: Nonblank
    reviewer: Nonblank | None
    review_reference: Nonblank | None
    drafted_before_analysis: Literal[True]
    labels_sha256: SHA256

    @model_validator(mode="after")
    def honest_status(self) -> "LabelReview":
        if self.status == "reviewed" and (not self.reviewer or not self.review_reference):
            raise ValueError("Reviewed labels need a named reviewer and review_reference")
        if self.status == "draft" and (self.reviewer or self.review_reference):
            raise ValueError("Draft labels cannot claim a completed review")
        return self


class Provenance(StrictModel):
    schema_version: Literal["1.0"]
    id: CaseID
    repository: Nonblank
    change_url: Nonblank
    selection_reason: Nonblank
    warnings: list[str]
    base: RevisionReceipt
    head: RevisionReceipt
    label_review: LabelReview


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_revision(
    snapshot: Snapshot, receipt: RevisionReceipt, sha: str, license_id: str
) -> dict[str, Any]:
    """Verify recursive tree hashes plus every supported source blob and its license.

    SHA-1 ties the recorded tree inventory to its recorded root; SHA-256 also
    checks source bytes. This is integrity verification, not signed GitHub identity.
    """
    require(receipt.commit.sha == sha, "Pinned commit hash mismatch")
    tree = receipt.tree
    require(not tree.truncated, "Refusing a truncated tree")
    require(len(tree.tree) <= MAX_TREE_ENTRIES, "Git tree entry limit exceeded")
    require(tree.sha == receipt.commit.tree.sha, "Commit/tree hash mismatch")
    entries = {entry.path: entry for entry in tree.tree}
    require(len(entries) == len(tree.tree), "Duplicate tree paths")
    children: dict[str, list[Any]] = defaultdict(list)
    for entry in tree.tree:
        entry_path = PurePosixPath(entry.path)
        require(
            not entry_path.is_absolute()
            and str(entry_path) == entry.path
            and not any(part in {".", ".."} for part in entry_path.parts)
            and not any(ch in entry.path for ch in "\\\0:"),
            "Unsafe tree path",
        )
        expected_type = {"040000": "tree", "160000": "commit"}.get(entry.mode, "blob")
        require(entry.type == expected_type, "Inconsistent tree mode/type")
        parent = str(entry_path.parent)
        require(
            parent == "." or (parent in entries and entries[parent].type == "tree"),
            "Missing parent tree",
        )
        children[parent].append(entry)
    # Git trees contain raw immediate entries, sorted as though directories end in '/'.
    for directory, expected in [
        (".", tree.sha),
        *[(p, e.sha) for p, e in entries.items() if e.type == "tree"],
    ]:
        ordered = sorted(
            children[directory],
            key=lambda e: (PurePosixPath(e.path).name + ("/" if e.type == "tree" else "")).encode(),
        )
        raw = b"".join(
            e.mode.lstrip("0").encode()
            + b" "
            + PurePosixPath(e.path).name.encode()
            + b"\0"
            + bytes.fromhex(e.sha)
            for e in ordered
        )
        require(blob_hash(raw, "tree") == expected, f"Git tree hash mismatch: {directory}")
    supported = {
        p: e
        for p, e in entries.items()
        if e.type == "blob"
        and e.mode in {"100644", "100755"}
        and p.endswith(".py")
        and not EXCLUDED_DIRS.intersection(PurePosixPath(p).parts[:-1])
    }
    require(
        set(snapshot.files) == set(supported),
        "Snapshot must contain the complete supported Python tree",
    )
    require(set(receipt.source_sha256) == set(supported), "Source hash inventory mismatch")
    for path, source in snapshot.files.items():
        raw = source.encode("utf-8")
        entry = supported[path]
        require(
            blob_hash(raw) == entry.sha and entry.size == len(raw),
            f"Source blob hash/size mismatch: {path}",
        )
        require(
            hashlib.sha256(raw).hexdigest() == receipt.source_sha256[path],
            f"Source SHA256 hash mismatch: {path}",
        )
    license = receipt.license
    license_entry = entries.get(license.path)
    raw = license.text.encode("utf-8")
    require(
        license_entry is not None
        and license_entry.type == "blob"
        and license_entry.mode in {"100644", "100755"}
        and license_entry.size == len(raw)
        and license_entry.sha == blob_hash(raw)
        and license.sha256 == hashlib.sha256(raw).hexdigest()
        and license.spdx == license_id,
        "Pinned license hash, size or SPDX mismatch",
    )
    return {
        "commit": sha,
        "tree_sha": tree.sha,
        "python_files": len(supported),
        "python_bytes": sum(len(s.encode()) for s in snapshot.files.values()),
        "excluded_python_paths": sorted(
            p for p in entries if p.endswith(".py") and p not in supported
        ),
        "symlink_paths": sorted(p for p, e in entries.items() if e.mode == "120000"),
        "submodule_paths": sorted(p for p, e in entries.items() if e.mode == "160000"),
        "non_python_blob_count": sum(
            e.type == "blob" and not p.endswith(".py") for p, e in entries.items()
        ),
        "license": license.model_dump(),
    }


def read_metadata(path: Path) -> tuple[Any, int]:
    require(
        not path.is_symlink() and path.is_file(),
        f"Metadata must be a regular file, not a symlink: {path.name}",
    )
    with path.open("rb") as stream:
        raw = stream.read(MAX_METADATA_BYTES + 1)
    require(len(raw) <= MAX_METADATA_BYTES, "Metadata size limit exceeded")
    return json.loads(raw, object_pairs_hook=_unique_object), len(raw)


def load_real(
    directory: Path,
) -> tuple[Selection, list[CorpusCase], dict[str, Provenance], dict[str, Any]]:
    for path in (directory, directory / "cases", directory / "provenance"):
        require(
            not path.is_symlink() and path.is_dir(),
            f"Dataset directory missing or symlink: {path.name}",
        )
    raw_selection, total = read_metadata(directory / "selection.json")
    selection = Selection.model_validate(raw_selection)
    cases = load_corpus(directory / "cases")
    selected = {s.id: s for s in selection.cases}
    require({c.id for c in cases} == set(selected), "Case IDs differ from selection")
    require(
        {p.name for p in (directory / "cases").iterdir()} == {f"{id}.json" for id in selected},
        "Unexpected case files",
    )
    require(
        {p.name for p in (directory / "provenance").iterdir()} == {f"{id}.json" for id in selected},
        "Missing or extra provenance files",
    )
    provenance, coverage = {}, {}
    for case in cases:
        raw, size = read_metadata(directory / "provenance" / f"{case.id}.json")
        total += size
        require(total <= MAX_CORPUS_BYTES, "Metadata total size limit exceeded")
        p = Provenance.model_validate(raw)
        s = selected[case.id]
        require(p.id == case.id and p.repository == s.repository, "Provenance identity mismatch")
        require(
            p.change_url == f"https://github.com/{s.repository}/commit/{s.head}",
            "Change URL mismatch",
        )
        require(p.selection_reason == s.reason, "Selection reason mismatch")
        require(
            bool(p.head.commit.parents) and p.head.commit.parents[0].sha == s.base,
            "Pinned first parent mismatch",
        )
        require(
            p.label_review.labels_sha256 == label_hash(case),
            "Frozen label hash mismatch; record a deliberate label revision",
        )
        coverage[case.id] = {
            side: validate_revision(
                getattr(case.request, side), getattr(p, side), getattr(s, side), s.license
            )
            for side in ("base", "head")
        }
        provenance[case.id] = p
    return selection, cases, provenance, coverage


def summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counts()
    reasons: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    for case in cases:
        for key in Counts.model_fields:
            setattr(counts, key, getattr(counts, key) + case["metrics"]["counts"][key])
        reasons.update(case["reason_counts"])
        statuses[case["label_review"]["status"]] += 1
    return {
        "case_count": len(cases),
        "test_count": sum(c["test_count"] for c in cases),
        "selected_count": sum(c["selected_count"] for c in cases),
        "selected_tests": [
            {"case": c["id"], "test_id": sid} for c in cases for sid in c["selected_test_ids"]
        ],
        "unclassified_test_count": sum(c["unclassified_test_count"] for c in cases),
        "unclassified_recommendation_count": counts.unclassified_recommendations,
        "reason_counts": dict(sorted(reasons.items())),
        "label_status_counts": dict(sorted(statuses.items())),
        "metrics": metrics(counts).model_dump(),
    }


def evaluate_real(
    directory: Path, *, annotations: dict[str, dict[str, Any]] | None = None
) -> dict[str, Any]:
    selection, cases, provenance, coverage = load_real(directory)
    original_cases = cases
    if annotations is not None:
        require(set(annotations) == {case.id for case in cases}, "Baseline case inventory mismatch")
        require(
            all(
                set(value) == {"category", "known_discrepancies", "limitations"}
                for value in annotations.values()
            ),
            "Baseline may only override discrepancy annotations",
        )
        cases = [
            CorpusCase.model_validate(case.model_dump() | annotations[case.id]) for case in cases
        ]
    # evaluate() validates every recommendation's typed path and revision evidence.
    evaluation = evaluate(cases)
    results = []
    for result in evaluation.cases:
        case = result.case
        recs = result.analysis["recommendations"]
        p = provenance[case.id]
        results.append(
            {
                "id": case.id,
                "repository": p.repository,
                "change_url": p.change_url,
                "label_review": p.label_review.model_dump(),
                "coverage": coverage[case.id],
                "test_count": len(case.expected_affected)
                + len(case.expected_unaffected)
                + len(case.unclassified),
                "selected_test_ids": sorted(r["symbol"] for r in recs),
                "selected_count": len(recs),
                "unclassified_test_ids": sorted(case.unclassified),
                "unclassified_test_count": len(case.unclassified),
                "unclassified_recommendation_count": len(
                    result.results.unclassified_recommendations
                ),
                "reason_counts": dict(sorted(Counter(r["reason"] for r in recs).items())),
                "metrics": result.results.metrics.model_dump(),
            }
        )
    digest = canonical_hash(
        {
            "selection": selection.model_dump(),
            "cases": [c.model_dump() for c in original_cases],
            "provenance": {id: p.model_dump() for id, p in sorted(provenance.items())},
        }
    )
    return {
        "dataset_schema_version": "1.0",
        "dataset_sha256": digest,
        "interpretation": (
            "Small purposive real-source pilot with agent-drafted dependency labels. "
            "Not independent review, runtime failures, production accuracy, "
            "or permission to skip tests."
        ),
        "volatile_fields_excluded": ["evaluation.cases[].analysis.stats.elapsed_ms"],
        "selection": selection.model_dump(),
        "summary": summarize(results),
        "repositories": {
            repo: summarize([c for c in results if c["repository"] == repo])
            for repo in sorted({c["repository"] for c in results})
        },
        "cases": results,
        "evaluation": evaluation.model_dump(mode="json"),
    }


def main(
    argv: list[str] | None = None,
    *,
    evaluator: Callable[[Path], dict[str, Any]] = evaluate_real,
    default_corpus: Path = Path("corpus/real"),
    default_output: Path = Path("reports/real-evaluation.json"),
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=default_corpus)
    parser.add_argument("--output", type=Path, default=default_output)
    args = parser.parse_args(argv)
    try:
        require(
            not args.output.resolve().is_relative_to(args.corpus.resolve()),
            "Report output must be outside the corpus directory",
        )
        report = evaluator(args.corpus)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Atomic replacement avoids partially written reports and cannot overwrite
        # dataset bytes through a pre-existing hard link at the output path.
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=args.output.parent, delete=False
            ) as stream:
                temporary = Path(stream.name)
                stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
            temporary.replace(args.output)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    except (OSError, ValueError, RecursionError) as exc:
        print(f"Real evaluation error: {exc}", file=sys.stderr)
        return 2
    print(report["interpretation"])
    for case in [*report["cases"], {"id": "overall", **report["summary"]}]:
        print(
            f"{case['id']}: selected={case['selected_count']}/{case['test_count']}; "
            f"unclassified={case['unclassified_test_count']}; {case['metrics']['counts']}"
        )
    regressions = report["evaluation"]["regressions"]
    print("Baseline: " + ("CHANGED" if regressions else "matches recorded discrepancies"))
    for regression in regressions:
        print(regression)
    print(f"JSON report (all IDs and evidence): {args.output}")
    return 1 if regressions else 0


if __name__ == "__main__":
    raise SystemExit(main())
