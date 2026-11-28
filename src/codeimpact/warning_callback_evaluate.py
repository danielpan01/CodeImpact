"""Replay bounded keyed extrema callbacks in a warning context."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.fresh_evaluate import PROJECT, WARNING_CALLBACK_TRANSITION
from codeimpact.namespace_callback_evaluate import evaluate_namespace_callback
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_warning_callback(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt("warning-callback-v1", WARNING_CALLBACK_TRANSITION)
    return measure(
        directory, evaluate_namespace_callback(directory), receipt, True, "Warning callback"
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_warning_callback,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-warning-callback-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
