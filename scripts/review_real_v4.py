"""Prepare offline v4 review materials and validate separate review records."""

import argparse
import ast
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from codeimpact.corpus import CorpusCase, Nonblank, StrictModel
from codeimpact.discovery import V2_POLICY
from codeimpact.fresh_evaluate import file_hash
from codeimpact.real_evaluate import SHA256, CaseID, Provenance, load_real, read_metadata, require
from codeimpact.v4_evaluate import DIRECTORY, FREEZE, inventories, stable_bytes, validate_frozen
from scripts.review_real import python_diff, review_pack

Classification = Literal["affected", "unaffected", "uncertain"]
PILOT_CASES = ("humanize_small_delta", "oyaml_error_context")
DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


class SourceSpan(StrictModel):
    revision: Literal["base", "head"]
    path: Nonblank
    line: int = Field(ge=1, strict=True)
    end_line: int = Field(ge=1, strict=True)


class Decision(StrictModel):
    original: Classification
    proposed: Classification
    rationale: Nonblank
    evidence: list[SourceSpan] = Field(min_length=1, max_length=12)


class ReviewRecord(StrictModel):
    schema_version: Literal["1.0"]
    case: CaseID
    frozen_inputs_sha256: SHA256
    labels_sha256: SHA256
    reviewer: Nonblank
    reviewed_on: date
    review_reference: Nonblank
    discovery_notes: Nonblank
    decisions: dict[Nonblank, Decision]


def build_pack(directory: Path) -> str:
    _, cases, _, _ = load_real(directory, discovery_policy=V2_POLICY)
    audit = inventories(cases)
    pack = review_pack(
        directory,
        discovery_policy=V2_POLICY,
        outside={cid: r["head"]["outside_discovery"] for cid, r in audit.items()},
    )
    # Present a whitespace-clean diff. Snapshot strings retain their exact bytes.
    return "\n".join(line.rstrip() for line in pack.splitlines()) + "\n"


@dataclass(frozen=True)
class ReviewInputs:
    freeze_sha256: str
    cases: dict[str, CorpusCase]
    provenance: dict[str, Provenance]
    audit: dict[str, Any]


def load_inputs(directory: Path) -> ReviewInputs:
    _, cases, audit = validate_frozen(directory)
    _, _, provenance, _ = load_real(directory, discovery_policy=V2_POLICY)
    return ReviewInputs(
        file_hash(directory / FREEZE), {case.id: case for case in cases}, provenance, audit
    )


def draft_labels(case: CorpusCase) -> dict[str, tuple[Classification, str]]:
    groups: tuple[tuple[Classification, dict[str, str]], ...] = (
        ("affected", case.expected_affected),
        ("unaffected", case.expected_unaffected),
        ("uncertain", case.unclassified),
    )
    return {sid: (label, rationale) for label, group in groups for sid, rationale in group.items()}


def validate_record(inputs: ReviewInputs, record: ReviewRecord) -> dict[str, Any]:
    require(record.case in inputs.cases, "Unknown review case")
    case = inputs.cases[record.case]
    draft = inputs.provenance[record.case].label_review
    labels = draft_labels(case)
    require(inputs.freeze_sha256 == record.frozen_inputs_sha256, "Review freeze differs")
    require(draft.labels_sha256 == record.labels_sha256, "Review labels differ")
    require(
        record.reviewer.casefold() != draft.author.casefold(), "Reviewer must differ from author"
    )
    require(record.decisions.keys() <= labels.keys(), "Unknown review definition")
    for sid, decision in record.decisions.items():
        require(decision.original == labels[sid][0], f"Original label differs: {sid}")
        for span in decision.evidence:
            source = getattr(case.request, span.revision).files.get(span.path)
            require(
                source is not None and span.line <= span.end_line <= len(source.splitlines()),
                f"Invalid pinned source range for {sid}",
            )
    return {
        "case": record.case,
        "recorded": len(record.decisions),
        "remaining_ids": sorted(labels.keys() - record.decisions.keys()),
        "proposed_revisions": sorted(
            sid
            for sid, decision in record.decisions.items()
            if decision.original != decision.proposed
        ),
    }


def validate_review(directory: Path, record: ReviewRecord) -> dict[str, Any]:
    return validate_record(load_inputs(directory), record)


def review_template(inputs: ReviewInputs, cid: str) -> dict[str, Any]:
    require(cid in inputs.cases, "Unknown review case")
    return {
        "schema_version": "1.0",
        "case": cid,
        "frozen_inputs_sha256": inputs.freeze_sha256,
        "labels_sha256": inputs.provenance[cid].label_review.labels_sha256,
        "reviewer": "",
        "reviewed_on": "",
        "review_reference": "",
        "discovery_notes": "",
        "decisions": {
            sid: {"original": label, "proposed": label, "rationale": "", "evidence": []}
            for sid, (label, _) in sorted(draft_labels(inputs.cases[cid]).items())
        },
    }


def definition_lines(tree: ast.Module, qualified: str) -> tuple[int, int] | None:
    scope = tree.body
    for part in qualified.split("."):
        definitions = [n for n in scope if isinstance(n, DEFINITIONS) and n.name == part]
        if len(definitions) != 1:
            return None
        node = definitions[0]
        scope = node.body
    first = min([node.lineno, *(d.lineno for d in node.decorator_list)])
    return first, node.end_lineno or node.lineno


def pilot_packet(inputs: ReviewInputs, cid: str) -> str:
    require(cid in PILOT_CASES, "Case is outside the v4 review pilot")
    case = inputs.cases[cid]
    provenance = inputs.provenance[cid]
    labels = draft_labels(case)
    lines = [
        f"# Source-label review packet for `{cid}`",
        "",
        f"Repository: `{provenance.repository}`",
        f"Base commit: `{provenance.base.commit.sha}`",
        f"Head commit: `{provenance.head.commit.sha}`",
        f"Frozen inputs SHA-256: `{inputs.freeze_sha256}`",
        f"Draft labels SHA-256: `{provenance.label_review.labels_sha256}`",
        f"Draft author: {provenance.label_review.author}",
        "",
        case.description,
        "",
        "Review the pinned change, applicable calls, test inputs and setup in both revisions.",
        "Label source dependency as affected, unaffected or uncertain.",
        "Give a rationale and cite a revision, path and inclusive line range for each decision.",
        "Use the companion JSON template and delete entries you have not reviewed.",
        "",
        "## Discovery inventory",
        "",
    ]
    for revision in ("base", "head"):
        inv = inputs.audit[cid][revision]
        lines.append(
            f"- {revision}: {len(inv['discovered_ids'])} discovered definitions, "
            f"{len(inv['outside_discovery'])} outside discovery, "
            f"{len(inv['unparseable_files'])} unparseable files."
        )
        lines.extend(
            f"  - `{sid}` — {reason}" for sid, reason in sorted(inv["outside_discovery"].items())
        )
        lines.extend(f"  - Unparseable: `{path}`" for path in sorted(inv["unparseable_files"]))
    counts = Counter(label for label, _ in labels.values())
    lines += [
        "",
        f"Draft head labels: {counts['affected']} affected, {counts['unaffected']} unaffected, "
        f"{counts['uncertain']} uncertain.",
        "",
        "## Complete captured Python diff",
        "",
        "````diff",
        *python_diff(case),
        "````",
        "",
        "## Draft labels and pinned definition spans",
        "",
    ]
    sources = {
        side: dict(sorted(getattr(case.request, side).files.items())) for side in ("base", "head")
    }
    anchors = {
        (side, path): f"source-{side}-{i}"
        for side, files in sources.items()
        for i, path in enumerate(files, 1)
    }
    trees = {
        (side, path): ast.parse(source, filename=path)
        for side, files in sources.items()
        for path, source in files.items()
        if path not in inputs.audit[cid][side]["unparseable_files"]
    }
    for sid, (label, rationale) in sorted(labels.items()):
        path, qualified = sid.split("::", 1)
        links = []
        for side in sources:
            tree = trees.get((side, path))
            span = definition_lines(tree, qualified) if tree else None
            if span:
                first, last = span
                links.append(f"[{side} `{path}:{first}–{last}`](#{anchors[side, path]})")
            else:
                links.append(f"{side}: no pinned definition span")
        lines.append(f"- [ ] `{sid}` — **{label}**. {rationale} ({' · '.join(links)})")
    for side, files in sources.items():
        receipt = getattr(provenance, side)
        lines += ["", f"## {side.title()} source", ""]
        for path, source in files.items():
            lines += [
                f'<a id="{anchors[side, path]}"></a>',
                "",
                f"### `{path}`",
                "",
                f"Source SHA-256: `{receipt.source_sha256[path]}`",
                "",
                "````text",
                *(f"{i:>5} | {line}" for i, line in enumerate(source.splitlines(), 1)),
                "````",
                "",
            ]
        lines += [
            f"### {side.title()} license notice",
            "",
            "````text",
            receipt.license.text.rstrip("\n"),
            "````",
        ]
    return "\n".join(lines) + "\n"


def summarize_pilot(inputs: ReviewInputs, records: list[ReviewRecord]) -> dict[str, Any]:
    by_case: dict[str, list[ReviewRecord]] = defaultdict(list)
    reviewer_cases: set[tuple[str, str]] = set()
    for record in sorted(records, key=lambda r: (r.case, r.reviewer.casefold())):
        require(record.case in PILOT_CASES, f"Case is outside the v4 review pilot: {record.case}")
        validate_record(inputs, record)
        key = record.case, record.reviewer.casefold()
        require(
            key not in reviewer_cases, f"Multiple records from {record.reviewer} for {record.case}"
        )
        reviewer_cases.add(key)
        by_case[record.case].append(record)

    cases = {}
    totals: Counter[str] = Counter()
    for cid in PILOT_CASES:
        labels = draft_labels(inputs.cases[cid])
        submissions = by_case[cid]
        votes: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for review in submissions:
            for sid, decision in review.decisions.items():
                votes[sid].append({"reviewer": review.reviewer, **decision.model_dump(mode="json")})
        groups: dict[str, dict[str, Any]] = {
            "agreements": {},
            "proposed_label_changes": {},
            "unresolved_disagreements": {},
        }
        for sid, decisions in sorted(votes.items()):
            proposed = sorted({decision["proposed"] for decision in decisions})
            original, _ = labels[sid]
            if len(proposed) > 1:
                group = "unresolved_disagreements"
            elif proposed == [original]:
                group = "agreements"
            else:
                group = "proposed_label_changes"
            groups[group][sid] = {
                "original": original,
                "proposed_labels": proposed,
                "submissions": decisions,
            }

        unreviewed = sorted(labels.keys() - votes.keys())
        uncertain = sorted(sid for sid, (label, _) in labels.items() if label == "uncertain")
        totals.update(
            definitions=len(labels),
            draft_uncertain=len(uncertain),
            records=len(submissions),
            unreviewed=len(unreviewed),
            **{group: len(rows) for group, rows in groups.items()},
        )
        cases[cid] = {
            "labels_sha256": inputs.provenance[cid].label_review.labels_sha256,
            "definition_count": len(labels),
            "draft_uncertain_ids": uncertain,
            "reviews": [
                r.model_dump(
                    mode="json",
                    include={"reviewer", "reviewed_on", "review_reference", "discovery_notes"},
                )
                for r in submissions
            ],
            "unreviewed_ids": unreviewed,
            **groups,
        }
    return {
        "schema_version": "1.0",
        "frozen_inputs_sha256": inputs.freeze_sha256,
        "status": (
            "ready_for_review"
            if not records
            else "partial"
            if totals["unreviewed"]
            else "coverage_complete"
        ),
        "totals": dict(totals),
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DIRECTORY)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--template", metavar="CASE")
    mode.add_argument("--validate", type=Path, metavar="RECORD")
    mode.add_argument("--pilot-packet", choices=PILOT_CASES, metavar="CASE")
    mode.add_argument("--summarize", nargs="*", type=Path, metavar="RECORD")
    args = parser.parse_args(argv)
    try:
        if args.validate:
            record = ReviewRecord.model_validate(read_metadata(args.validate)[0])
            print(json.dumps(validate_review(args.corpus, record), indent=2))
        elif args.template:
            print(json.dumps(review_template(load_inputs(args.corpus), args.template), indent=2))
        elif args.pilot_packet:
            print(pilot_packet(load_inputs(args.corpus), args.pilot_packet), end="")
        elif args.summarize is not None:
            records = [
                ReviewRecord.model_validate(read_metadata(path)[0]) for path in args.summarize
            ]
            print(stable_bytes(summarize_pilot(load_inputs(args.corpus), records)).decode(), end="")
        else:
            print(build_pack(args.corpus), end="")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Review error: {exc}\n")


if __name__ == "__main__":
    main()
