"""Read immutable Git blobs; never check out or execute the repository."""

import argparse
import json
import subprocess
from pathlib import Path

from codeimpact.analyzer import analyze
from codeimpact.demo import demo_request
from codeimpact.models import MAX_FILE_BYTES, MAX_TOTAL_BYTES, AnalysisRequest, Snapshot


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout


def revision(repo: Path, ref: str) -> str:
    return (
        git(repo, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}").decode().strip()
    )


def read_snapshot(repo: Path, sha: str) -> Snapshot:
    records = git(repo, "ls-tree", "-rz", "--full-tree", sha).split(b"\0")
    files: dict[str, str] = {}
    total = 0
    for record in records:
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, kind, oid = metadata.split()
        path = raw_path.decode("utf-8")
        if kind != b"blob" or mode == b"120000" or not path.endswith(".py"):
            continue
        if any(
            part in {".venv", "venv", "node_modules", "vendor", ".git"} for part in path.split("/")
        ):
            continue
        size = int(git(repo, "cat-file", "-s", oid.decode()))
        total += size
        if size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES or len(files) >= 300:
            raise ValueError("Repository exceeds analysis limits; narrow its scope before analysis")
        files[path] = git(repo, "cat-file", "blob", oid.decode()).decode("utf-8")
    return Snapshot(files=files)


def main() -> None:
    parser = argparse.ArgumentParser(description="CodeImpact static Python change analysis")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", help="Base branch/ref; compared from its merge base with head")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument(
        "--snapshots", action="store_true", help="Export API input instead of a report"
    )
    args = parser.parse_args()
    try:
        if args.demo:
            request = demo_request()
        else:
            if not args.base:
                parser.error("Pass --base REF or --demo")
            base, head = revision(args.repo, args.base), revision(args.repo, args.head)
            merge_base = git(args.repo, "merge-base", base, head).decode().strip()
            request = AnalysisRequest(
                base=read_snapshot(args.repo, merge_base),
                head=read_snapshot(args.repo, head),
                label=f"{merge_base[:8]} → {head[:8]}",
            )
        output = request if args.snapshots else analyze(request)
        print(json.dumps(output.model_dump(), indent=2))
    except (ValueError, OSError, RecursionError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"Analysis failed: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
