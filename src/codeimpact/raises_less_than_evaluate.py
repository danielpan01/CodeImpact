"""Replay pytest.raises comparisons against the direct string assertion predecessor."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import measure, verified_receipt
from codeimpact.fresh_evaluate import PROJECT, RAISES_LESS_THAN_TRANSITION
from codeimpact.real_evaluate import main as real_main
from codeimpact.string_parameter_less_than_evaluate import evaluate_string_parameter_less_than
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_raises_less_than(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt("raises-less-than-v1", RAISES_LESS_THAN_TRANSITION)
    return measure(
        directory, evaluate_string_parameter_less_than(directory), receipt, True, "Raises less-than"
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_raises_less_than,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-raises-less-than-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
