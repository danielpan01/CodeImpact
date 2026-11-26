"""Replay class-preserving factories against the frozen exact-equality predecessor."""

from pathlib import Path
from typing import Any

from codeimpact.equality_evaluate import Receipt, evaluate_equality, measure
from codeimpact.fresh_evaluate import FACTORY_TRANSITION, PROJECT, file_hash
from codeimpact.holdout_evaluate import safe_file
from codeimpact.real_evaluate import main as real_main
from codeimpact.real_evaluate import require
from codeimpact.v5_evaluate import DIRECTORY, metadata

RECEIPT = "datasets/real-v5-successors/prerelease-factories-v1.json"


def evaluate_factories(directory: Path) -> dict[str, Any]:
    receipt = Receipt.model_validate(metadata(PROJECT, RECEIPT))
    require(receipt.name == "prerelease-factories-v1", "Wrong factory successor")
    transition = safe_file(PROJECT, FACTORY_TRANSITION.as_posix())
    require(
        file_hash(transition) == receipt.preservation_sha256, "Factory preservation receipt changed"
    )
    recorded = metadata(PROJECT, FACTORY_TRANSITION.as_posix())
    for path, digest in sorted(recorded["current_sources_sha256"].items()):
        require(file_hash(safe_file(PROJECT, path)) == digest, f"Factory source changed: {path}")
    return measure(
        directory, evaluate_equality(directory), receipt, True, "Class-preserving factory"
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
