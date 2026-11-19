"""Replay the frozen v4 labels with guarded callable-instance selection enabled."""

import hashlib
from pathlib import Path
from typing import Any, Literal

from codeimpact.corpus import StrictModel
from codeimpact.fresh_evaluate import PROJECT, file_hash, replay_source_matches
from codeimpact.holdout_evaluate import safe_file
from codeimpact.real_evaluate import SHA256, read_metadata, require
from codeimpact.real_evaluate import main as real_main
from codeimpact.unittest_evaluate import (
    BASELINE as PREVIOUS_BASELINE,
)
from codeimpact.unittest_evaluate import (
    LABELS,
    DiscoveryLabels,
    evaluate_unittest,
    measure,
)
from codeimpact.v4_evaluate import (
    DIRECTORY,
    ENGINE,
    SUCCESSOR,
    VARIADIC_SUCCESSOR,
    stable_bytes,
)

BASELINE = "baseline.json"
TARGET = "icecream_local_time"
SOURCES = ENGINE | {"src/codeimpact/variadic_fallback.py"}
OUTPUT = Path("reports/real-v4-variadic-dispatch-v1-evaluation.json")


class Delta(StrictModel):
    removed: list[str]
    retained: list[str]
    added: list[str]
    evidence_replaced: list[str]


class Baseline(StrictModel):
    schema_version: Literal["1.0"]
    selection_policy: Literal["variadic-dispatch-v1"]
    predecessor_baseline_sha256: SHA256
    predecessor_report_sha256: SHA256
    analyzer_sha256: dict[str, SHA256]
    report_sha256: SHA256
    timestamp_delta: Delta


def timestamp_case(report: dict[str, Any]) -> dict[str, Any]:
    return next(item for item in report["evaluation"]["cases"] if item["case"]["id"] == TARGET)


def delta(previous: dict[str, Any], current: dict[str, Any]) -> Delta:
    def recommendations(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return {r["symbol"]: r for r in timestamp_case(report)["analysis"]["recommendations"]}

    old, new = recommendations(previous), recommendations(current)
    common = old.keys() & new.keys()
    return Delta(
        removed=sorted(old.keys() - new.keys()),
        retained=sorted(common),
        added=sorted(new.keys() - old.keys()),
        evidence_replaced=sorted(sid for sid in common if old[sid] != new[sid]),
    )


def evaluate_variadic(
    directory: Path, *, successor: Path = PROJECT / VARIADIC_SUCCESSOR
) -> dict[str, Any]:
    baseline_file = safe_file(successor, BASELINE)
    baseline = Baseline.model_validate(read_metadata(baseline_file)[0])
    previous_dir = PROJECT / SUCCESSOR
    require(
        file_hash(safe_file(previous_dir, PREVIOUS_BASELINE))
        == baseline.predecessor_baseline_sha256,
        "Predecessor successor baseline changed",
    )
    require(set(baseline.analyzer_sha256) == SOURCES, "Variadic engine inventory differs")
    for path, expected in baseline.analyzer_sha256.items():
        require(
            replay_source_matches(PROJECT, path, expected), f"Variadic analyzer changed: {path}"
        )
    previous = evaluate_unittest(directory)
    require(
        not previous["evaluation"]["regressions"]
        and hashlib.sha256(stable_bytes(previous)).hexdigest()
        == baseline.predecessor_report_sha256,
        "Frozen unittest discovery replay differs",
    )
    labels = DiscoveryLabels.model_validate(read_metadata(safe_file(previous_dir, LABELS))[0])
    report = measure(directory, labels, variadic=True)
    observed = delta(previous, report)
    regressions = []
    if (
        hashlib.sha256(stable_bytes(report)).hexdigest() != baseline.report_sha256
        or observed != baseline.timestamp_delta
    ):
        regressions.append("v4 variadic dispatch: report differs from the recorded measurement")
    old, new = timestamp_case(previous)["results"], timestamp_case(report)["results"]
    if (
        observed.added
        or old["true_positives"] != new["true_positives"]
        or old["unclassified_recommendations"] != new["unclassified_recommendations"]
    ):
        regressions.append(
            "IceCream timestamp: affected, uncertain or added recommendations differ"
        )
    predecessors = {item["case"]["id"]: item for item in previous["evaluation"]["cases"]}
    for item in report["evaluation"]["cases"]:
        cid = item["case"]["id"]
        if cid != TARGET and item != predecessors[cid]:
            regressions.append(f"{cid}: result changed outside the timestamp slice")

    report["first_regressions"] = report["evaluation"]["regressions"]
    report["evaluation"]["regressions"] = regressions
    report.update(
        selection_policy=baseline.selection_policy,
        baseline_sha256=file_hash(baseline_file),
        predecessor_report_sha256=baseline.predecessor_report_sha256,
        timestamp_delta=observed.model_dump(),
        interpretation="Variadic dispatch replay against frozen draft source dependency labels.",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    return real_main(
        argv,
        evaluator=evaluate_variadic,
        default_corpus=DIRECTORY,
        default_output=OUTPUT,
        protected_inputs=(PROJECT / "corpus",),
    )


if __name__ == "__main__":
    raise SystemExit(main())
