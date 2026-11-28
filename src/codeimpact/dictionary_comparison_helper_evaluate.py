"""Replay comparisons after a verified literal dictionary conversion."""

from pathlib import Path
from typing import Any

from codeimpact.comparison_helper_evaluate import evaluate_comparison_helper
from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.fresh_evaluate import DICTIONARY_COMPARISON_HELPER_TRANSITION, PROJECT
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_dictionary_comparison_helper(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt(
        "dictionary-comparison-helper-v1", DICTIONARY_COMPARISON_HELPER_TRANSITION
    )
    return measure(
        directory,
        evaluate_comparison_helper(directory),
        receipt,
        True,
        "Dictionary comparison helper",
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_dictionary_comparison_helper,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-dictionary-comparison-helper-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
