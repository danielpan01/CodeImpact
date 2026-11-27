"""Replay keyed min/max calls from literal pytest tables."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.fresh_evaluate import (
    KEYED_PARAMETERS_TRANSITION,
    PROJECT,
    keyed_parameters_source_hash,
)
from codeimpact.keyed_extrema_evaluate import evaluate_keyed_extrema
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_keyed_parameters(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt(
        "keyed-parameters-v1", KEYED_PARAMETERS_TRANSITION, keyed_parameters_source_hash
    )
    return measure(
        directory,
        evaluate_keyed_extrema(directory),
        receipt,
        "keyed-parameters",
        "Keyed parameters",
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_keyed_parameters,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-keyed-parameters-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
