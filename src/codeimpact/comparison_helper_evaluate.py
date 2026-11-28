"""Replay exact-instance comparisons that reach a changed helper."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.fresh_evaluate import (
    COMPARISON_HELPER_TRANSITION,
    PROJECT,
    comparison_helper_source_hash,
)
from codeimpact.parameter_replace_equality_evaluate import evaluate_parameter_replace_equality
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_comparison_helper(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt(
        "comparison-helper-v1", COMPARISON_HELPER_TRANSITION, comparison_helper_source_hash
    )
    return measure(
        directory,
        evaluate_parameter_replace_equality(directory),
        receipt,
        "comparison-helper",
        "Comparison helper",
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_comparison_helper,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-comparison-helper-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
