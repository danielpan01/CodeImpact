"""Replay literal string comparisons against the tuple and list predecessor."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.fresh_evaluate import PROJECT, STRING_PARAMETER_LESS_THAN_TRANSITION
from codeimpact.parameterized_less_than_evaluate import evaluate_parameterized_less_than
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_string_parameter_less_than(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt(
        "string-parameter-less-than-v1", STRING_PARAMETER_LESS_THAN_TRANSITION
    )
    return measure(
        directory,
        evaluate_parameterized_less_than(directory),
        receipt,
        True,
        "String parameter less-than",
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_string_parameter_less_than,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-string-parameter-less-than-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
