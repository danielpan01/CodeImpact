"""Replay the first unconditional equality assertion against its factory predecessor."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.factory_evaluate import evaluate_factories
from codeimpact.fresh_evaluate import FIRST_ASSERTION_TRANSITION, PROJECT
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_first_assertion(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt("first-assertion-v1", FIRST_ASSERTION_TRANSITION)
    return measure(
        directory, evaluate_factories(directory), receipt, True, "First equality assertion"
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_first_assertion,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-first-assertion-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
