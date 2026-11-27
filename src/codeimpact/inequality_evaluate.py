"""Replay exact-class inequality evidence against the less-than predecessor."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.fresh_evaluate import INEQUALITY_TRANSITION, PROJECT
from codeimpact.less_than_evaluate import evaluate_less_than
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_inequality(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt("exact-inequality-v1", INEQUALITY_TRANSITION)
    return measure(directory, evaluate_less_than(directory), receipt, True, "Exact inequality")


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_inequality,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-exact-inequality-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
