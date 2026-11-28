"""Replay bounded test callbacks from literal namespace tables."""

from pathlib import Path
from typing import Any

from codeimpact.dictionary_comparison_helper_evaluate import evaluate_dictionary_comparison_helper
from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.fresh_evaluate import NAMESPACE_CALLBACK_TRANSITION, PROJECT
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_namespace_callback(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt("namespace-callback-v1", NAMESPACE_CALLBACK_TRANSITION)
    return measure(
        directory,
        evaluate_dictionary_comparison_helper(directory),
        receipt,
        True,
        "Namespace callback",
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_namespace_callback,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-namespace-callback-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
