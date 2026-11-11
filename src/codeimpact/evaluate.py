"""Deterministic agreement with authored dependency labels, not runtime accuracy."""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from codeimpact.analyzer import analyze, build_index
from codeimpact.corpus import CorpusCase, discover_tests, load_corpus
from codeimpact.models import AnalysisRequest, DependencyEvidence, Report


class Counts(BaseModel):
    tp: int = 0
    fn: int = 0
    fp: int = 0
    tn: int = 0
    unclassified_recommendations: int = 0


class Ratio(BaseModel):
    numerator: int
    denominator: int
    value: float | None


class Metrics(BaseModel):
    counts: Counts
    precision: Ratio
    recall: Ratio


class Classification(BaseModel):
    true_positives: list[str]
    false_negatives: list[str]
    false_positives: list[str]
    true_negatives: list[str]
    unclassified_recommendations: list[str]
    metrics: Metrics


class CaseResult(BaseModel):
    case: CorpusCase
    results: Classification
    regressions: list[str]
    analysis: dict[str, Any]


class Evaluation(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    analysis_schema_version: Literal["2.0"] = "2.0"
    interpretation: str = (
        "Agreement with authored dependency labels; not externally validated ground truth, "
        "runtime failure probabilities or permission to skip the full test suite."
    )
    corpus_sha256: str
    case_count: int
    group_case_counts: dict[str, int]
    totals: Metrics
    groups: dict[str, Metrics]
    cases: list[CaseResult]
    regressions: list[str]


def metrics(counts: Counts) -> Metrics:
    def ratio(denominator: int) -> Ratio:
        return Ratio(
            numerator=counts.tp,
            denominator=denominator,
            value=counts.tp / denominator if denominator else None,
        )

    return Metrics(
        counts=counts, precision=ratio(counts.tp + counts.fp), recall=ratio(counts.tp + counts.fn)
    )


def classify(case: CorpusCase, selected: set[str]) -> Classification:
    affected, unaffected, unknown = (
        set(case.expected_affected),
        set(case.expected_unaffected),
        set(case.unclassified),
    )
    if selected - (affected | unaffected | unknown):
        raise ValueError("Recommendations must identify explicitly classified head tests")
    tp, fn, fp, tn = (
        affected & selected,
        affected - selected,
        unaffected & selected,
        unaffected - selected,
    )
    outside = selected & unknown
    return Classification(
        true_positives=sorted(tp),
        false_negatives=sorted(fn),
        false_positives=sorted(fp),
        true_negatives=sorted(tn),
        unclassified_recommendations=sorted(outside),
        metrics=metrics(
            Counts(
                tp=len(tp),
                fn=len(fn),
                fp=len(fp),
                tn=len(tn),
                unclassified_recommendations=len(outside),
            )
        ),
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"Invalid analyzer report: {message}")


def _evidence_key(item: DependencyEvidence) -> tuple[int, int, str]:
    return item.location.line, item.location.end_line, item.text


def validate_report(request: AnalysisRequest, report: Report) -> None:
    """Check path contracts independently of selection labels.

    Re-indexing checks that the returned union retains each revision's evidence;
    it does not certify that the index resolves Python semantics correctly. The
    authored labels, separate discovery and existing analyzer tests cover that gap.
    """
    before, after = build_index(request.base), build_index(request.head)
    nodes = {node.id: node for node in report.nodes}
    _require(len(nodes) == len(report.nodes), "duplicate nodes")
    _require(set(nodes) == before.nodes.keys() | after.nodes.keys(), "node union")
    _require([node.id for node in report.nodes] == sorted(nodes), "node ordering")
    _require(report.removed == sorted(before.nodes.keys() - after.nodes.keys()), "removed symbols")
    _require(set(report.changed) <= nodes.keys(), "unknown changed symbol")
    edges = {edge.id: edge for edge in report.edges}
    keys = [(edge.source, edge.target, edge.kind) for edge in report.edges]
    _require(len(edges) == len(report.edges) == len(set(keys)), "duplicate edges")
    _require(set(keys) == before.edges.keys() | after.edges.keys(), "typed edge union")
    _require(keys == sorted(keys), "edge ordering")
    for edge in report.edges:
        key = edge.source, edge.target, edge.kind
        _require(edge.source in nodes and edge.target in nodes, "unknown edge endpoint")
        _require(
            edge.id == hashlib.sha256(json.dumps(key, ensure_ascii=True).encode()).hexdigest(),
            "unstable edge ID",
        )
        expected_before = (
            sorted(before.edges[key].evidence, key=_evidence_key) if key in before.edges else []
        )
        expected_after = (
            sorted(after.edges[key].evidence, key=_evidence_key) if key in after.edges else []
        )
        _require(
            edge.before == expected_before and edge.after == expected_after,
            "revision evidence differs from snapshot index",
        )
        revision = (
            "both"
            if expected_before and expected_after
            else "before"
            if expected_before
            else "after"
        )
        _require(edge.revision == revision, "edge revision")
        for snapshot, evidence in ((request.base, edge.before), (request.head, edge.after)):
            for item in evidence:
                for location in (item.location, item.target_location):
                    _require(location.path in snapshot.files, "evidence file absent in revision")
                    source = snapshot.files[location.path].replace("\r\n", "\n").replace("\r", "\n")
                    line_count = max(1, len(source.split("\n")) - int(source.endswith("\n")))
                    _require(
                        1 <= location.line <= location.end_line <= line_count, "evidence range"
                    )
                _require(item.location.path == nodes[edge.source].path, "caller evidence path")
                _require(
                    item.target_location.path == nodes[edge.target].path, "dependency evidence path"
                )
    tests = discover_tests(request.head)
    selected = [rec.symbol for rec in report.recommendations]
    _require(len(set(selected)) == len(selected), "duplicate recommendations")
    _require(set(selected) <= tests - set(report.removed), "non-head or removed recommended test")
    _require(
        report.recommendations
        == sorted(report.recommendations, key=lambda rec: (-rec.score, rec.symbol)),
        "recommendation ordering",
    )
    for rec in report.recommendations:
        path = rec.evidence_path
        _require(bool(path) and path[0] == rec.symbol, "path must start at test")
        _require(path[-1] in report.changed, "path must end at changed symbol")
        _require(
            len(path) == rec.distance + 1 and len(rec.evidence_edges) == len(path) - 1,
            "path lengths",
        )
        _require(len(set(path)) == len(path), "path cycle")
        available = {"before", "after"}
        kinds = []
        for source, target, eid in zip(path, path[1:], rec.evidence_edges, strict=False):
            _require(eid in edges, "missing typed edge")
            edge = edges[eid]
            _require(
                (edge.source, edge.target) == (source, target),
                "caller-to-dependency path direction",
            )
            kinds.append(edge.kind)
            available &= {side for side in ("before", "after") if getattr(edge, side)}
        if len(path) == 1:
            available = {
                side
                for side, index in (("before", before), ("after", after))
                if rec.symbol in index.nodes
            }
            reason = "Test itself changed"
        elif all(kind == "call" for kind in kinds) and nodes[path[-1]].kind != "module":
            reason = "Resolved call path"
        else:
            reason = "Conservative module/import dependency"
        _require(rec.reason == reason, "resolved/fallback reason")
        path_revision = (
            "both" if len(available) == 2 else next(iter(available)) if available else "mixed"
        )
        _require(rec.path_revision == path_revision, "path revision intersection")


def evaluate_case(case: CorpusCase) -> CaseResult:
    report = analyze(case.request)
    validate_report(case.request, report)
    result = classify(case, {rec.symbol for rec in report.recommendations})
    regressions = []
    for label, actual, expected in (
        ("false positives", result.false_positives, case.known_discrepancies.false_positives),
        ("false negatives", result.false_negatives, case.known_discrepancies.false_negatives),
        (
            "unclassified recommendations",
            result.unclassified_recommendations,
            case.expected_unclassified_recommendations,
        ),
    ):
        if set(actual) != set(expected):
            regressions.append(
                f"{case.id}: {label}: expected {sorted(expected)}, observed {actual}"
            )
    return CaseResult(
        case=case,
        results=result,
        regressions=regressions,
        analysis=report.model_dump(mode="json", exclude={"stats": {"elapsed_ms"}}),
    )


def _aggregate(results: list[CaseResult]) -> Metrics:
    counts = Counts()
    for result in results:
        for key in Counts.model_fields:
            setattr(counts, key, getattr(counts, key) + getattr(result.results.metrics.counts, key))
    return metrics(counts)


def evaluate(cases: list[CorpusCase]) -> Evaluation:
    if not cases or len({case.id for case in cases}) != len(cases):
        raise ValueError("Evaluation needs nonempty cases with unique IDs")
    cases = sorted(cases, key=lambda case: case.id)
    results = [evaluate_case(case) for case in cases]
    canonical = json.dumps(
        [case.model_dump(mode="json") for case in cases], sort_keys=True, separators=(",", ":")
    )
    groups = {
        group: [r for r in results if r.case.category == group]
        for group in ("supported", "known_limitation")
    }
    return Evaluation(
        corpus_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
        case_count=len(results),
        group_case_counts={key: len(value) for key, value in groups.items()},
        totals=_aggregate(results),
        groups={key: _aggregate(value) for key, value in groups.items()},
        cases=results,
        regressions=[message for result in results for message in result.regressions],
    )


def readable(report: Evaluation) -> str:
    def ratio(value: Ratio) -> str:
        suffix = f"{value.value:.1%}" if value.value is not None else "not applicable"
        return f"{value.numerator}/{value.denominator} ({suffix})"

    lines = [
        "Authored dependency-label agreement",
        f"Cases: {report.case_count}; corpus SHA256: {report.corpus_sha256}",
        report.interpretation,
    ]
    for name, value in [("overall", report.totals), *report.groups.items()]:
        c = value.counts
        lines.append(
            f"{name}: TP={c.tp} FN={c.fn} FP={c.fp} TN={c.tn}; "
            f"unclassified selected={c.unclassified_recommendations}; "
            f"precision={ratio(value.precision)}; recall={ratio(value.recall)}"
        )
    for result in report.cases:
        lines.append(f"\n{result.case.id} [{result.case.category}]: {result.case.description}")
        for label in (
            "true_positives",
            "false_negatives",
            "false_positives",
            "true_negatives",
            "unclassified_recommendations",
        ):
            lines.append(f"  {label}: {', '.join(getattr(result.results, label)) or '(none)'}")
        lines.append(
            f"  precision={ratio(result.results.metrics.precision)}; "
            f"recall={ratio(result.results.metrics.recall)}"
        )
        for note in result.case.limitations:
            lines.append(f"  limitation: {note}")
    lines.extend(
        [
            "\nBaseline: "
            + ("CHANGED" if report.regressions else "matches all recorded discrepancies"),
            *report.regressions,
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("corpus/cases"))
    parser.add_argument("--output", type=Path, default=Path("reports/corpus-evaluation.json"))
    parser.add_argument("--case", dest="case_id", help="Evaluate one stable case ID")
    args = parser.parse_args(argv)
    try:
        cases = load_corpus(args.corpus)
        if args.case_id:
            cases = [case for case in cases if case.id == args.case_id]
            if not cases:
                raise ValueError(f"Unknown case: {args.case_id}")
        if args.output.resolve().is_relative_to(args.corpus.resolve()):
            raise ValueError("Report output must be outside the corpus directory")
        report = evaluate(cases)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError, RecursionError) as exc:
        print(f"Evaluation error: {exc}", file=sys.stderr)
        return 2
    print(readable(report))
    print(f"\nJSON report: {args.output}")
    return 1 if report.regressions else 0


if __name__ == "__main__":
    raise SystemExit(main())
