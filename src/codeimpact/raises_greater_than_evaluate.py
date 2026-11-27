"""Replay greater-than calls inside pytest.raises against the less-than predecessor."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.fresh_evaluate import (
    PROJECT,
    RAISES_GREATER_THAN_TRANSITION,
    raises_greater_than_source_hash,
)
from codeimpact.raises_less_than_evaluate import evaluate_raises_less_than
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_raises_greater_than(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt(
        "raises-greater-than-v1", RAISES_GREATER_THAN_TRANSITION, raises_greater_than_source_hash
    )
    return measure(
        directory,
        evaluate_raises_less_than(directory),
        receipt,
        "raises-greater-than",
        "Raises greater-than",
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_raises_greater_than,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-raises-greater-than-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
