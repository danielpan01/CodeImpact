"""Replay v5's exact-class equality successor against a separate receipt."""

from pathlib import Path
from typing import Any, Literal

from codeimpact.corpus import StrictModel
from codeimpact.fresh_evaluate import EQUALITY_TRANSITION, PROJECT, file_hash
from codeimpact.holdout_evaluate import safe_file
from codeimpact.models import Recommendation
from codeimpact.real_evaluate import SHA256, require
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import (
    DIRECTORY,
    Discrepancies,
    collect,
    discrepancies,
    evaluate_v5,
    file_digest,
    metadata,
)

RECEIPT = Path("datasets/real-v5-successors/exact-equality-v1.json")
OUTPUT = Path("reports/real-v5-exact-equality-v1-evaluation.json")


class Delta(StrictModel):
    added: dict[str, Recommendation]
    removed: list[str]
    changed: dict[str, Recommendation]
    remaining: Discrepancies


class Receipt(StrictModel):
    schema_version: Literal["1.0"]
    name: Literal["exact-equality-v1"]
    preservation_sha256: SHA256
    predecessor_report_sha256: SHA256
    report_sha256: SHA256
    cases: dict[str, Delta]


def changes(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Delta]:
    earlier = {
        item["case"]["id"]: {r["symbol"]: r for r in item["analysis"]["recommendations"]}
        for item in before["evaluation"]["cases"]
    }
    remaining = discrepancies(after)
    result = {}
    for item in after["evaluation"]["cases"]:
        cid = item["case"]["id"]
        old = earlier[cid]
        new = {r["symbol"]: r for r in item["analysis"]["recommendations"]}
        result[cid] = Delta.model_validate(
            {
                "added": {sid: new[sid] for sid in sorted(new.keys() - old.keys())},
                "removed": sorted(old.keys() - new.keys()),
                "changed": {
                    sid: new[sid] for sid in sorted(old.keys() & new.keys()) if old[sid] != new[sid]
                },
                "remaining": remaining[cid],
            }
        )
    return result


def evaluate_equality(directory: Path) -> dict[str, Any]:
    receipt = Receipt.model_validate(metadata(PROJECT, RECEIPT.as_posix()))
    transition = safe_file(PROJECT, EQUALITY_TRANSITION.as_posix())
    require(
        file_hash(transition) == receipt.preservation_sha256,
        "Equality preservation receipt changed",
    )
    recorded = metadata(PROJECT, EQUALITY_TRANSITION.as_posix())
    for path, digest in sorted(recorded["current_sources_sha256"].items()):
        require(file_hash(safe_file(PROJECT, path)) == digest, f"Equality source changed: {path}")

    before = evaluate_v5(directory)
    require(
        not before["evaluation"]["regressions"]
        and file_digest(before) == receipt.predecessor_report_sha256,
        "Frozen v5 replay differs",
    )
    after = collect(directory, equality=True)
    delta = changes(before, after)
    after["evaluation"]["regressions"] = (
        ["Exact equality report differs from the successor receipt"]
        if file_digest(after) != receipt.report_sha256 or delta != receipt.cases
        else []
    )
    after.update(
        successor=receipt.name,
        predecessor_report_sha256=receipt.predecessor_report_sha256,
        successor_report_sha256=receipt.report_sha256,
        delta={cid: item.model_dump(mode="json") for cid, item in delta.items()},
    )
    return after


def main(argv: list[str] | None = None) -> int:
    return real_main(
        argv,
        evaluator=evaluate_equality,
        default_corpus=DIRECTORY,
        default_output=OUTPUT,
        protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
    )


if __name__ == "__main__":
    raise SystemExit(main())
