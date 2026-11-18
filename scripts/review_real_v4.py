"""Render a source-only v4 review pack or validate a separate reader's record."""

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import Field

from codeimpact.corpus import Nonblank, StrictModel
from codeimpact.discovery import CURRENT_POLICY
from codeimpact.fresh_evaluate import file_hash
from codeimpact.real_evaluate import SHA256, CaseID, load_real, read_metadata, require
from codeimpact.v4_evaluate import DIRECTORY, FREEZE, inventories, validate_frozen
from scripts.review_real import review_pack

Classification = Literal["affected", "unaffected", "uncertain"]


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
    _, cases, _, _ = load_real(directory, discovery_policy=CURRENT_POLICY)
    audit = inventories(cases)
    pack = review_pack(
        directory,
        discovery_policy=CURRENT_POLICY,
        outside={cid: r["head"]["outside_discovery"] for cid, r in audit.items()},
    )
    # Present a whitespace-clean diff. Snapshot strings retain their exact bytes.
    return "\n".join(line.rstrip() for line in pack.splitlines()) + "\n"


def review_context(directory: Path, cid: str):
    _, cases, _ = validate_frozen(directory)
    _, _, provenance, _ = load_real(directory, discovery_policy=CURRENT_POLICY)
    case = next((case for case in cases if case.id == cid), None)
    if case is None:
        raise ValueError("Unknown review case")
    labels = {
        sid: label
        for label, group in (
            ("affected", case.expected_affected),
            ("unaffected", case.expected_unaffected),
            ("uncertain", case.unclassified),
        )
        for sid in group
    }
    return case, provenance[cid].label_review, labels


def validate_review(directory: Path, record: ReviewRecord):
    case, draft, labels = review_context(directory, record.case)
    require(file_hash(directory / FREEZE) == record.frozen_inputs_sha256, "Review freeze differs")
    require(draft.labels_sha256 == record.labels_sha256, "Review labels differ")
    require(
        record.reviewer.casefold() != draft.author.casefold(), "Reviewer must differ from author"
    )
    require(record.decisions.keys() <= labels.keys(), "Unknown review definition")
    for sid, decision in record.decisions.items():
        require(decision.original == labels[sid], f"Original label differs: {sid}")
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DIRECTORY)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--template", metavar="CASE")
    mode.add_argument("--validate", type=Path, metavar="RECORD")
    args = parser.parse_args()
    if args.validate:
        record = ReviewRecord.model_validate(read_metadata(args.validate)[0])
        print(json.dumps(validate_review(args.corpus, record), indent=2))
    elif args.template:
        _, draft, labels = review_context(args.corpus, args.template)
        print(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "case": args.template,
                    "frozen_inputs_sha256": file_hash(args.corpus / FREEZE),
                    "labels_sha256": draft.labels_sha256,
                    "reviewer": "",
                    "reviewed_on": "",
                    "review_reference": "",
                    "discovery_notes": "",
                    "decisions": {
                        sid: {"original": label, "proposed": label, "rationale": "", "evidence": []}
                        for sid, label in sorted(labels.items())
                    },
                },
                indent=2,
            )
        )
    else:
        print(build_pack(args.corpus), end="")


if __name__ == "__main__":
    main()
