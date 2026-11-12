"""Optional online capture; only reads GitHub objects and writes JSON source data.

Run from the project root. Uses the same bounded reader as PR ingestion, with
GitHub CLI authentication when available. Never clones or executes an upstream.
"""

import argparse
import asyncio
import hashlib
import json
import subprocess
from pathlib import Path

import httpx

from codeimpact.github import (
    MAX_SECONDS,
    Commit,
    GitHubReader,
    ObjectID,
    Repository,
    Tree,
    public_repository,
)
from codeimpact.models import Snapshot
from codeimpact.real_evaluate import (
    RevisionReceipt,
    Selected,
    Selection,
    read_metadata,
    validate_revision,
)


class CaptureCommit(Commit):
    parents: list[ObjectID]
    message: str


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


async def capture(client, selected):
    Selected.model_validate(selected)
    reader = GitHubReader(client)
    repository = selected["repository"]
    actual = public_repository(await reader.get(f"/repos/{repository}", Repository))
    if actual.lower() != repository.lower():
        raise ValueError("Public repository identity mismatch")
    head = await reader.get(f"/repos/{repository}/git/commits/{selected['head']}", CaptureCommit)
    if head.sha != selected["head"] or not head.parents or head.parents[0].sha != selected["base"]:
        raise ValueError("Capture requires the selected commit and exact first parent")
    request, revisions, warnings = {}, {}, []
    for side, sha in (("base", head.parents[0].sha), ("head", head.sha)):
        commit = await reader.get(f"/repos/{repository}/git/commits/{sha}", CaptureCommit)
        if commit.sha != sha:
            raise ValueError("Commit identity mismatch")
        snapshot = await reader.snapshot(repository, sha, side, warnings)
        tree = await reader.get(
            f"/repos/{repository}/git/trees/{commit.tree.sha}?recursive=1", Tree
        )
        licenses = [
            entry for entry in tree.tree if entry.path in {"LICENSE.txt", "LICENSE.rst", "LICENSE"}
        ]
        if len(licenses) != 1:
            raise ValueError("Capture requires one explicit root license; review this repository")
        license_entry = licenses[0]
        if license_entry.type != "blob" or license_entry.mode not in {"100644", "100755"}:
            raise ValueError("License must be an ordinary blob")
        await reader.blob(repository, license_entry)
        license_raw = reader.blobs[license_entry.sha]
        request[side] = snapshot.model_dump()
        revisions[side] = {
            "commit": commit.model_dump(),
            "tree": tree.model_dump(),
            "source_sha256": {path: sha256(text.encode()) for path, text in snapshot.files.items()},
            "license": {
                "path": license_entry.path,
                "spdx": selected["license"],
                "text": license_raw.decode("utf-8"),
                "sha256": sha256(license_raw),
            },
        }
        validate_revision(
            Snapshot.model_validate(request[side]),
            RevisionReceipt.model_validate(revisions[side]),
            sha,
            selected["license"],
        )
    return {
        "request": request | {"label": selected["id"]},
        "provenance": {
            "repository": repository,
            "change_url": f"https://github.com/{repository}/commit/{head.sha}",
            "selection_reason": selected["reason"],
            "warnings": sorted(set(warnings)),
            "base": revisions["base"],
            "head": revisions["head"],
        },
    }


async def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, default=Path("corpus/real/selection.json"))
    parser.add_argument("--output", type=Path, default=Path("reports/real-capture"))
    args = parser.parse_args(argv)
    selection = Selection.model_validate(read_metadata(args.selection)[0])
    if args.output.resolve().is_relative_to(args.selection.parent.resolve()):
        raise ValueError("Capture output must be outside the dataset")
    headers = {"Accept": "application/vnd.github+json"}
    # Capture credentials in memory only; never print or persist them.
    try:
        token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        pass
    else:
        headers["Authorization"] = "Bearer " + token.stdout.strip()
    args.output.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(headers=headers) as client:
        for item in selection.cases:
            selected = item.model_dump()
            output = args.output / f"{selected['id']}.json"
            if output.exists():
                raise ValueError(f"Refusing to overwrite capture: {output}")
            async with asyncio.timeout(MAX_SECONDS):
                data = await capture(client, selected)
            with output.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
            print(
                selected["id"],
                {s: len(data["request"][s]["files"]) for s in ("base", "head")},
                flush=True,
            )


if __name__ == "__main__":
    asyncio.run(main())
