"""Replay v4 with isolated inline parameter-row selection enabled."""

import hashlib
from pathlib import Path
from typing import Any, Literal

from codeimpact.corpus import StrictModel
from codeimpact.fresh_evaluate import PROJECT, file_hash
from codeimpact.holdout_evaluate import safe_file
from codeimpact.models import Recommendation
from codeimpact.real_evaluate import SHA256, read_metadata, require
from codeimpact.real_evaluate import main as real_main
from codeimpact.unittest_evaluate import LABELS, DiscoveryLabels, measure
from codeimpact.v4_evaluate import (
    DIRECTORY,
    PARAMETER_ROWS_SUCCESSOR,
    SUCCESSOR,
    VARIADIC_SUCCESSOR,
    stable_bytes,
)
from codeimpact.variadic_evaluate import BASELINE, SOURCES, evaluate_variadic

TARGET = "humanize_small_delta"
ENGINE = SOURCES | {"src/codeimpact/parameter_rows.py"}
OUTPUT = Path("reports/real-v4-parameter-rows-v1-evaluation.json")


class EvidenceChange(StrictModel):
    before: Recommendation
    after: Recommendation


class Delta(StrictModel):
    removed: list[str]
    retained: list[str]
    added: list[str]
    evidence_replacements: dict[str, EvidenceChange]


class Baseline(StrictModel):
    schema_version: Literal["1.0"]
    selection_policy: Literal["parameter-rows-v1"]
    predecessor_baseline_sha256: SHA256
    predecessor_report_sha256: SHA256
    analyzer_sha256: dict[str, SHA256]
    report_sha256: SHA256
    humanize_delta: Delta


def target_case(report: dict[str, Any]) -> dict[str, Any]:
    return next(item for item in report["evaluation"]["cases"] if item["case"]["id"] == TARGET)


def delta(previous: dict[str, Any], current: dict[str, Any]) -> Delta:
    def recs(report: dict[str, Any]) -> dict[str, Recommendation]:
        return {
            r["symbol"]: Recommendation.model_validate(r)
            for r in target_case(report)["analysis"]["recommendations"]
        }

    old, new = recs(previous), recs(current)
    common = sorted(old.keys() & new.keys())
    return Delta(
        removed=sorted(old.keys() - new.keys()),
        retained=common,
        added=sorted(new.keys() - old.keys()),
        evidence_replacements={
            sid: EvidenceChange(before=old[sid], after=new[sid])
            for sid in common
            if old[sid] != new[sid]
        },
    )


def evaluate_rows(
    directory: Path, *, successor: Path = PROJECT / PARAMETER_ROWS_SUCCESSOR
) -> dict[str, Any]:
    file = safe_file(successor, BASELINE)
    baseline = Baseline.model_validate(read_metadata(file)[0])
    require(
        file_hash(safe_file(PROJECT / VARIADIC_SUCCESSOR, BASELINE))
        == baseline.predecessor_baseline_sha256,
        "Predecessor variadic baseline changed",
    )
    require(set(baseline.analyzer_sha256) == ENGINE, "Parameter row engine inventory differs")
    for path, expected in baseline.analyzer_sha256.items():
        require(file_hash(PROJECT / path) == expected, f"Parameter row analyzer changed: {path}")
    previous = evaluate_variadic(directory)
    require(
        not previous["evaluation"]["regressions"]
        and hashlib.sha256(stable_bytes(previous)).hexdigest()
        == baseline.predecessor_report_sha256,
        "Frozen variadic replay differs",
    )
    labels = DiscoveryLabels.model_validate(
        read_metadata(safe_file(PROJECT / SUCCESSOR, LABELS))[0]
    )
    report = measure(directory, labels, variadic=True, parameter_rows=True)
    observed = delta(previous, report)
    regressions = []
    if (
        hashlib.sha256(stable_bytes(report)).hexdigest() != baseline.report_sha256
        or observed != baseline.humanize_delta
    ):
        regressions.append("v4 parameter rows: report differs from the recorded measurement")
    old, new = target_case(previous)["results"], target_case(report)["results"]
    if (
        observed.added
        or old["true_positives"] != new["true_positives"]
        or old["unclassified_recommendations"] != new["unclassified_recommendations"]
    ):
        regressions.append(
            "Humanize small delta: affected, uncertain or added recommendations differ"
        )
    predecessors = {item["case"]["id"]: item for item in previous["evaluation"]["cases"]}
    for item in report["evaluation"]["cases"]:
        cid = item["case"]["id"]
        if cid != TARGET and item != predecessors[cid]:
            regressions.append(f"{cid}: result changed outside the parameter-row slice")
    report["first_regressions"] = report["evaluation"]["regressions"]
    report["evaluation"]["regressions"] = regressions
    report.update(
        selection_policy=baseline.selection_policy,
        baseline_sha256=file_hash(file),
        predecessor_report_sha256=baseline.predecessor_report_sha256,
        humanize_delta=observed.model_dump(),
        interpretation="Inline parameter-row replay against frozen draft source dependency labels.",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    return real_main(
        argv,
        evaluator=evaluate_rows,
        default_corpus=DIRECTORY,
        default_output=OUTPUT,
        protected_inputs=(PROJECT / "corpus",),
    )


if __name__ == "__main__":
    raise SystemExit(main())
