"""Replay class-preserving factories against the frozen exact-equality predecessor."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import evaluate_equality, measure, verified_receipt
from codeimpact.fresh_evaluate import FACTORY_TRANSITION, PROJECT, factory_source_hash
from codeimpact.real_evaluate import main as real_main
from codeimpact.v5_evaluate import DIRECTORY


def evaluate_factories(directory: Path) -> dict[str, Any]:
    receipt = verified_receipt("prerelease-factories-v1", FACTORY_TRANSITION, factory_source_hash)
    return measure(
        directory, evaluate_equality(directory), receipt, "factories", "Class-preserving factory"
    )


if __name__ == "__main__":
    raise SystemExit(
        real_main(
            evaluator=evaluate_factories,
            default_corpus=DIRECTORY,
            default_output=Path("reports/real-v5-prerelease-factories-v1-evaluation.json"),
            protected_inputs=(PROJECT / "corpus", PROJECT / "datasets", PROJECT / "benchmarks"),
        )
    )
