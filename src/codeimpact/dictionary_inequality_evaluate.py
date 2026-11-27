"""Replay builtin dictionary inequality against the exact-class inequality predecessor."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.fresh_evaluate import DICTIONARY_INEQUALITY_TRANSITION, PROJECT
from codeimpact.inequality_evaluate import evaluate_inequality
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_dictionary_inequality(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt("dictionary-inequality-v1", DICTIONARY_INEQUALITY_TRANSITION)
    return measure(
        directory, evaluate_inequality(directory), receipt, True, "Dictionary inequality"
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_dictionary_inequality,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-dictionary-inequality-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
