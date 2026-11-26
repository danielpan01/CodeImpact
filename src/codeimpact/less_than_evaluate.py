"""Replay exact-class less-than evidence against the first-assertion predecessor."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.first_assertion_evaluate import evaluate_first_assertion
from codeimpact.fresh_evaluate import LESS_THAN_TRANSITION, PROJECT
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_less_than(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt("exact-less-than-v1", LESS_THAN_TRANSITION)
    return measure(directory, evaluate_first_assertion(directory), receipt, True, "Exact less-than")


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_less_than,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-exact-less-than-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
