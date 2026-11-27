"""Replay equality after class-preserving replacement from literal pytest rows."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.fresh_evaluate import (
    PARAMETER_REPLACE_EQUALITY_TRANSITION,
    PROJECT,
    parameter_replace_equality_source_hash,
)
from codeimpact.parameter_dictionary_equality_evaluate import evaluate_parameter_dictionary_equality
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_parameter_replace_equality(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt(
        "parameter-replace-equality-v1",
        PARAMETER_REPLACE_EQUALITY_TRANSITION,
        parameter_replace_equality_source_hash,
    )
    return measure(
        directory,
        evaluate_parameter_dictionary_equality(directory),
        receipt,
        "parameter-replace-equality",
        "Parameter replacement equality",
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_parameter_replace_equality,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-parameter-replace-equality-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
