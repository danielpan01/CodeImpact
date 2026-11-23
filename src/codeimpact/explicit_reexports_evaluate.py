"""Replay v4 with evidence-only qualified package re-export resolution."""

import hashlib
from pathlib import Path
from typing import Any, Literal

from codeimpact.corpus import StrictModel
from codeimpact.fresh_evaluate import PROJECT, file_hash, replay_source_matches
from codeimpact.holdout_evaluate import safe_file
from codeimpact.models import Edge
from codeimpact.parameter_rows_evaluate import ENGINE as ROWS_ENGINE
from codeimpact.parameter_rows_evaluate import Delta, delta, evaluate_rows, target_case
from codeimpact.real_evaluate import SHA256, read_metadata, require
from codeimpact.real_evaluate import main as real_main
from codeimpact.unittest_evaluate import LABELS, DiscoveryLabels, measure
from codeimpact.v4_evaluate import (
    DIRECTORY,
    PARAMETER_ROWS_SUCCESSOR,
    REEXPORTS_SUCCESSOR,
    SUCCESSOR,
    stable_bytes,
)
from codeimpact.variadic_evaluate import BASELINE

ENGINE = ROWS_ENGINE | {"src/codeimpact/explicit_reexports.py"}
OUTPUT = Path("reports/real-v4-explicit-reexports-v1-evaluation.json")


class EdgeChange(StrictModel):
    before: Edge | None
    after: Edge


class Baseline(StrictModel):
    schema_version: Literal["1.0"]
    selection_policy: Literal["explicit-reexports-v1"]
    predecessor_baseline_sha256: SHA256
    predecessor_report_sha256: SHA256
    analyzer_sha256: dict[str, SHA256]
    report_sha256: SHA256
    recommendation_delta: Delta
    added_call_evidence: dict[str, EdgeChange]


def edge_changes(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, EdgeChange]:
    old = {edge["id"]: edge for edge in target_case(previous)["analysis"]["edges"]}
    new = {edge["id"]: edge for edge in target_case(current)["analysis"]["edges"]}
    require(old.keys() <= new.keys(), "Re-export resolution removed an independent edge")
    added = {}
    for eid in sorted(new):
        if old.get(eid) == new[eid]:
            continue
        after = Edge.model_validate(new[eid])
        require(after.kind == "call", "Non-call evidence changed during re-export resolution")
        before = Edge.model_validate(old[eid]) if eid in old else None
        if before:
            require(
                all(item in after.before for item in before.before)
                and all(item in after.after for item in before.after),
                "Previous call evidence was replaced",
            )
        added[eid] = EdgeChange(before=before, after=after)
    return added


def evaluate_reexports(
    directory: Path, *, successor: Path = PROJECT / REEXPORTS_SUCCESSOR
) -> dict[str, Any]:
    file = safe_file(successor, BASELINE)
    baseline = Baseline.model_validate(read_metadata(file)[0])
    require(
        file_hash(safe_file(PROJECT / PARAMETER_ROWS_SUCCESSOR, BASELINE))
        == baseline.predecessor_baseline_sha256,
        "Predecessor parameter-row baseline changed",
    )
    require(set(baseline.analyzer_sha256) == ENGINE, "Re-export engine inventory differs")
    for path, expected in baseline.analyzer_sha256.items():
        require(
            replay_source_matches(PROJECT, path, expected), f"Re-export analyzer changed: {path}"
        )
    previous = evaluate_rows(directory)
    require(
        not previous["evaluation"]["regressions"]
        and hashlib.sha256(stable_bytes(previous)).hexdigest()
        == baseline.predecessor_report_sha256,
        "Frozen parameter-row replay differs",
    )
    labels = DiscoveryLabels.model_validate(
        read_metadata(safe_file(PROJECT / SUCCESSOR, LABELS))[0]
    )
    report = measure(directory, labels, variadic=True, parameter_rows=True, reexports=True)
    observed = delta(previous, report)
    evidence = edge_changes(previous, report)
    regressions = []
    if (
        hashlib.sha256(stable_bytes(report)).hexdigest() != baseline.report_sha256
        or observed != baseline.recommendation_delta
        or evidence != baseline.added_call_evidence
    ):
        regressions.append("v4 explicit re-exports: report differs from the recorded measurement")
    if observed.added or observed.removed:
        regressions.append("Humanize small delta: selected IDs changed during evidence refinement")
    predecessors = {item["case"]["id"]: item for item in previous["evaluation"]["cases"]}
    target = target_case(previous)["case"]["id"]
    for item in report["evaluation"]["cases"]:
        cid = item["case"]["id"]
        if cid != target and item != predecessors[cid]:
            regressions.append(f"{cid}: result changed outside the re-export slice")
    report["first_regressions"] = report["evaluation"]["regressions"]
    report["evaluation"]["regressions"] = regressions
    report.update(
        selection_policy=baseline.selection_policy,
        baseline_sha256=file_hash(file),
        predecessor_report_sha256=baseline.predecessor_report_sha256,
        recommendation_delta=observed.model_dump(),
        added_call_evidence={eid: change.model_dump() for eid, change in evidence.items()},
        interpretation="Explicit package re-export replay against frozen draft source labels.",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    return real_main(
        argv,
        evaluator=evaluate_reexports,
        default_corpus=DIRECTORY,
        default_output=OUTPUT,
        protected_inputs=(PROJECT / "corpus",),
    )


if __name__ == "__main__":
    raise SystemExit(main())
