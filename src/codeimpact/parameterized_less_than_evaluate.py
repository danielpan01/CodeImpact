"""Replay literal pytest parameter comparisons against the dictionary predecessor."""

from pathlib import Path
from typing import Any

from codeimpact.dictionary_inequality_evaluate import evaluate_dictionary_inequality
from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.fresh_evaluate import PARAMETERIZED_LESS_THAN_TRANSITION, PROJECT
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_parameterized_less_than(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt("parameterized-less-than-v1", PARAMETERIZED_LESS_THAN_TRANSITION)
    return measure(
        directory,
        evaluate_dictionary_inequality(directory),
        receipt,
        True,
        "Parameterized less-than",
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_parameterized_less_than,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-parameterized-less-than-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
