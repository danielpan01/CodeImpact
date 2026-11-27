"""Replay v5's exact-class equality successor against a separate receipt."""

from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from codeimpact.corpus import StrictModel
from codeimpact.equality import EqualityMode
from codeimpact.fresh_evaluate import EQUALITY_TRANSITION, PROJECT, equality_source_hash, file_hash
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

OUTPUT = Path("reports/real-v5-exact-equality-v1-evaluation.json")


class Delta(StrictModel):
    added: dict[str, Recommendation]
    removed: list[str]
    changed: dict[str, Recommendation]
    remaining: Discrepancies


class Receipt(StrictModel):
    schema_version: Literal["1.0"]
    name: Literal[
        "exact-equality-v1",
        "prerelease-factories-v1",
        "first-assertion-v1",
        "exact-less-than-v1",
        "exact-inequality-v1",
        "dictionary-inequality-v1",
        "parameterized-less-than-v1",
        "string-parameter-less-than-v1",
        "raises-less-than-v1",
    ]
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


def verified_receipt(
    name: str,
    transition_path: Path,
    source_hash: Callable[[Path, str, str], str] | None = None,
) -> Receipt:
    receipt = Receipt.model_validate(metadata(PROJECT, f"datasets/real-v5-successors/{name}.json"))
    require(receipt.name == name, f"Wrong successor for {name}")
    transition = safe_file(PROJECT, transition_path.as_posix())
    require(
        file_hash(transition) == receipt.preservation_sha256, f"{name} preservation receipt changed"
    )
    recorded = metadata(PROJECT, transition_path.as_posix())
    for path, digest in sorted(recorded["current_sources_sha256"].items()):
        actual = file_hash(safe_file(PROJECT, path))
        if source_hash:
            actual = source_hash(PROJECT, path, actual)
        require(actual == digest, f"{name} source changed: {path}")
    return receipt


def evaluate_equality(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt("exact-equality-v1", EQUALITY_TRANSITION, equality_source_hash)
    return measure(directory, evaluate_v5(directory), receipt, "exact-class", "Exact equality")


def measure(
    directory: Path,
    before: dict[str, Any],
    receipt: Receipt,
    mode: EqualityMode,
    title: str,
) -> dict[str, Any]:
    require(
        not before["evaluation"]["regressions"]
        and file_digest(before) == receipt.predecessor_report_sha256,
        f"{title} predecessor replay differs",
    )
    after = collect(directory, equality=mode)
    delta = changes(before, after)
    after["evaluation"]["regressions"] = (
        [f"{title} report differs from the successor receipt"]
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
