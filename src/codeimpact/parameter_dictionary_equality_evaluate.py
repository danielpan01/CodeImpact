"""Replay factory equality evidence from string and dictionary pytest columns."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.fresh_evaluate import PARAMETER_DICTIONARY_EQUALITY_TRANSITION, PROJECT
from codeimpact.keyed_parameters_evaluate import evaluate_keyed_parameters
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_parameter_dictionary_equality(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt(
        "parameter-dictionary-equality-v1", PARAMETER_DICTIONARY_EQUALITY_TRANSITION
    )
    return measure(
        directory,
        evaluate_keyed_parameters(directory),
        receipt,
        True,
        "Parameter dictionary equality",
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_parameter_dictionary_equality,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-parameter-dictionary-equality-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
