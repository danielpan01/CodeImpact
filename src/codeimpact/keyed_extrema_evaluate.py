"""Replay keyed builtin extrema against the raises greater-than predecessor."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.fresh_evaluate import KEYED_EXTREMA_TRANSITION, PROJECT, keyed_extrema_source_hash
from codeimpact.raises_greater_than_evaluate import evaluate_raises_greater_than
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_keyed_extrema(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt(
        "keyed-extrema-v1", KEYED_EXTREMA_TRANSITION, keyed_extrema_source_hash
    )
    return measure(
        directory,
        evaluate_raises_greater_than(directory),
        receipt,
        "keyed-extrema",
        "Keyed extrema",
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_keyed_extrema,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-keyed-extrema-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
