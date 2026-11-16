"""Prepare data-only uploads for the deferred developer walkthrough, without analysis."""

import argparse
import json
import tempfile
from pathlib import Path

from codeimpact.holdout_evaluate import PROJECT, validate_frozen
from codeimpact.real_evaluate import load_real, require

CASES = ("inflection_title", "ordered_set_pop")


def prepare(directory: Path, output: Path) -> None:
    require(not output.exists() and not output.is_symlink(), "Pilot output already exists")
    require(
        not output.resolve().is_relative_to(directory.resolve())
        and not output.resolve().is_relative_to((PROJECT / "corpus").resolve()),
        "Pilot output must be outside the corpus",
    )
    validate_frozen(directory)
    _, cases, _, _ = load_real(directory)
    requests = {case.id: case.request.model_dump() for case in cases if case.id in CASES}
    require(set(requests) == set(CASES), "Pilot cases missing")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        bundle = Path(temporary) / "bundle"
        bundle.mkdir()
        for case_id in CASES:
            (bundle / f"{case_id}.json").write_text(
                json.dumps(requests[case_id], indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        (bundle / "README.txt").write_text(
            "Human pilot deferred by the owner on November 14, 2026.\n"
            "No participant observations have been recorded.\n"
            "Follow docs/DEVELOPER_PILOT.md in the CodeImpact checkout.\n"
            "Upload inflection_title.json for the evidence workflow, then\n"
            "ordered_set_pop.json for the expanded-discovery/evidence workflow.\n"
            "Source is JSON data; do not execute or install the upstream projects.\n",
            encoding="utf-8",
        )
        require(not output.exists() and not output.is_symlink(), "Pilot output already exists")
        bundle.rename(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("corpus/real-v3"))
    parser.add_argument("--output", type=Path, default=Path("reports/developer-pilot"))
    args = parser.parse_args(argv)
    try:
        prepare(args.corpus, args.output)
    except (OSError, ValueError, RecursionError) as exc:
        parser.exit(2, f"Pilot preparation error: {exc}\n")
    print(f"Walkthrough inputs: {args.output}; human pilot remains deferred.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
