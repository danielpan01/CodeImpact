"""Exact corpus changes and successor receipt checks for the package addition."""

import json
import shutil
from pathlib import Path

import pytest

from codeimpact import fresh_evaluate, holdout_evaluate
from codeimpact.additive_exports import AdditiveExports
from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest
from codeimpact.real_evaluate import canonical_hash

ROOT = Path(__file__).parents[1]
PREFIX = "iso8601/test_iso8601.py::"
REMOVED = {
    PREFIX + "test_fixedoffset_eq",
    PREFIX + "test_iso8601_regex",
    PREFIX + "test_parse_no_timezone_different_default",
    PREFIX + "test_parse_utc_different_default",
}


def test_validator_receipt_and_retained_evidence(monkeypatch):
    dataset = ROOT / "corpus/real-v3"
    case = json.loads((dataset / "cases/iso8601_validator.json").read_text())
    assert '"is_iso8601" "ParseError"' in case["request"]["head"]["files"]["iso8601/__init__.py"]
    request = AnalysisRequest.model_validate(case["request"])
    before = json.loads((dataset / "baselines/literal-tables-v1.json").read_text())["measurement"]
    after = json.loads((dataset / "baselines/additive-exports-v1.json").read_text())["measurement"]
    assert {
        k for k, v in after["analysis_sha256"].items() if v != before["analysis_sha256"][k]
    } == {"iso8601_validator"}
    current = analyze(request)
    validate_report(request, current)
    stable = current.model_dump(mode="json")
    stable["stats"].pop("elapsed_ms")
    assert canonical_hash(stable) == after["analysis_sha256"]["iso8601_validator"]
    finite = json.loads((dataset / "baselines/finite-string-guards-v1.json").read_text())
    assert canonical_hash(stable) == finite["measurement"]["analysis_sha256"]["iso8601_validator"]
    wrapped = [rec for rec in current.recommendations if rec.distance != 0]
    assert {rec.symbol for rec in wrapped} == {
        PREFIX + "test_hypothesis_valid_naive_datetimes",
        PREFIX + "test_hypothesis_valid_datetimes_with_timezone",
    }
    for rec in wrapped:
        assert rec.reason == "Conservative module/import dependency"
        assert rec.evidence_path == [
            rec.symbol,
            "iso8601/test_iso8601.py::<module>",
            "iso8601/__init__.py::<module>",
        ]
        assert (rec.score, rec.distance, rec.path_revision) == (32, 2, "both")
    monkeypatch.setattr(AdditiveExports, "allows", lambda *_: True)
    previous = analyze(request)
    validate_report(request, previous)
    stable = previous.model_dump(mode="json")
    stable["stats"].pop("elapsed_ms")
    assert canonical_hash(stable) == before["analysis_sha256"]["iso8601_validator"]
    assert {r.symbol for r in previous.recommendations} - {
        r.symbol for r in current.recommendations
    } == REMOVED
    assert len(current.recommendations) == 4
    assert {r.symbol for r in current.recommendations if r.distance == 0} == set(
        case["expected_affected"]
    )
    assert current.recommendations == [
        r for r in previous.recommendations if r.symbol not in REMOVED
    ]
    assert current.impacted == [item for item in previous.impacted if item not in REMOVED]
    for field in ("nodes", "edges", "changed", "changes", "removed", "source_files", "warnings"):
        assert getattr(current, field) == getattr(previous, field)


@pytest.mark.parametrize(
    ("dataset", "module", "evaluate"),
    [
        ("real-v2", fresh_evaluate, fresh_evaluate.evaluate_fresh),
        ("real-v3", holdout_evaluate, holdout_evaluate.evaluate_holdout),
    ],
)
def test_literal_tables_receipt_is_checked_before_analysis(
    tmp_path, monkeypatch, dataset, module, evaluate
):
    directory = tmp_path / dataset
    shutil.copytree(ROOT / "corpus" / dataset, directory)
    with (directory / "baselines/literal-tables-v1.json").open("ab") as stream:
        stream.write(b"\n")
    monkeypatch.setattr(module, "evaluate_real", lambda *_a, **_k: pytest.fail("ran analysis"))
    with pytest.raises(ValueError, match="Preserved literal tables baseline changed"):
        evaluate(directory)
