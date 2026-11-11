"""Read public GitHub objects as bounded data. Never clone, import or execute source."""

import asyncio
import base64
import binascii
import hashlib
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Annotated, Literal, TypeVar

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from codeimpact import __version__
from codeimpact.models import (
    MAX_FILE_BYTES,
    MAX_TOTAL_BYTES,
    AnalysisRequest,
    GitHubSource,
    Snapshot,
)

API_ROOT = "https://api.github.com"
OWNER = r"[A-Za-z0-9][A-Za-z0-9-]{0,38}"
REPO = r"[A-Za-z0-9_.-]{1,100}"
PR_URL = re.compile(rf"https://github\.com/({OWNER})/({REPO})/pull/([1-9][0-9]{{0,9}})")
REPOSITORY = re.compile(rf"{OWNER}/{REPO}")
EXCLUDED_DIRS = {".venv", "venv", "node_modules", "vendor", ".git"}
MAX_RESPONSE_BYTES = 4_000_000
MAX_NETWORK_BYTES = 20_000_000
MAX_REQUESTS = 650
MAX_TREE_ENTRIES = 20_000
MAX_SECONDS = 60
CONCURRENCY = 4
SHA = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]


class GitHubError(Exception):
    def __init__(self, code: str, message: str, status: int = 422, retryable: bool = False):
        super().__init__(message)
        self.code, self.message, self.status, self.retryable = code, message, status, retryable

    def detail(self) -> dict[str, str | bool]:
        return {"code": self.code, "message": self.message, "retryable": self.retryable}


class GitObject(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)


class Repository(GitObject):
    full_name: str
    private: bool


class Revision(GitObject):
    sha: SHA
    repo: Repository | None


class PullRequest(GitObject):
    number: int
    title: str = Field(max_length=1024)
    base: Revision
    head: Revision


class ObjectID(GitObject):
    sha: SHA


class Comparison(GitObject):
    base_commit: ObjectID
    merge_base_commit: ObjectID


class Commit(ObjectID):
    tree: ObjectID


class TreeEntry(GitObject):
    path: str = Field(min_length=1, max_length=500)
    mode: Literal["100644", "100755", "040000", "120000", "160000"]
    type: Literal["blob", "tree", "commit"]
    sha: SHA
    size: int | None = Field(default=None, ge=0)


class Tree(ObjectID):
    truncated: bool
    tree: list[TreeEntry]


class Blob(ObjectID):
    encoding: Literal["base64"]
    size: int = Field(ge=0, le=MAX_FILE_BYTES)
    content: str


@dataclass
class ImportedPR:
    request: AnalysisRequest
    source: GitHubSource
    warnings: list[str]


def parse_pr_url(url: str) -> tuple[str, int]:
    match = PR_URL.fullmatch(url)
    if not match or match[2] in {".", ".."}:
        raise GitHubError(
            "invalid_url", "Enter an exact https://github.com/owner/repo/pull/123 URL."
        )
    return f"{match[1]}/{match[2]}", int(match[3])


def public_repository(repository: Repository | None) -> str:
    if repository is None:
        raise GitHubError("unavailable_repository", "The PR's source repository is unavailable.")
    name = repository.full_name
    if not REPOSITORY.fullmatch(name) or name.split("/")[1] in {".", ".."}:
        raise GitHubError(
            "invalid_response", "GitHub returned an invalid repository identity.", 502
        )
    if repository.private:
        raise GitHubError("private_repository", "Only public repositories are supported.")
    return name


T = TypeVar("T", bound=GitObject)


class GitHubReader:
    """One reader per import: bounded concurrent requests and request-local blob reuse."""

    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.requests = 0
        self.network_bytes = 0
        self.blobs: dict[str, bytes] = {}
        self.slots = asyncio.Semaphore(CONCURRENCY)

    async def get(self, path: str, model: type[T], limit: int = MAX_RESPONSE_BYTES) -> T:
        # Callers construct paths from validated names/SHAs, never response-supplied URLs.
        self.requests += 1
        if self.requests > MAX_REQUESTS:
            raise GitHubError("too_large", "This PR exceeds the GitHub request budget.")
        async with self.slots:
            async with self.client.stream(
                "GET", API_ROOT + path, follow_redirects=False, timeout=httpx.Timeout(10, connect=5)
            ) as response:
                if response.status_code in {403, 429}:
                    limited = (
                        response.status_code == 429
                        or response.headers.get("x-ratelimit-remaining") == "0"
                        or "retry-after" in response.headers
                    )
                    raise GitHubError(
                        "rate_limited" if limited else "github_forbidden",
                        "GitHub limited this request. Wait before retrying, or use the demo "
                        "or snapshot upload while the limit resets."
                        if limited
                        else "GitHub refused access. Check public visibility and retry later.",
                        429 if limited else 503,
                        True,
                    )
                if response.status_code == 404:
                    raise GitHubError(
                        "not_found",
                        "PR or revision not found. Check the URL and public visibility.",
                        404,
                    )
                if response.status_code == 401:
                    raise GitHubError(
                        "github_auth", "The server's optional GitHub token was rejected.", 503
                    )
                if 300 <= response.status_code < 400:
                    raise GitHubError(
                        "redirect", "GitHub redirected this repository. Use its current PR URL."
                    )
                if response.status_code != 200:
                    raise GitHubError(
                        "github_unavailable",
                        "GitHub could not provide this revision. Try again later.",
                        502,
                        True,
                    )
                content = bytearray()
                async for chunk in response.aiter_bytes(64_000):
                    self.network_bytes += len(chunk)
                    if len(content) + len(chunk) > limit or self.network_bytes > MAX_NETWORK_BYTES:
                        raise GitHubError(
                            "too_large", "GitHub returned more data than this analysis allows."
                        )
                    content.extend(chunk)
                try:
                    return model.model_validate_json(content)
                except (ValidationError, ValueError) as exc:
                    raise GitHubError(
                        "invalid_response", "GitHub returned incomplete or unsupported data.", 502
                    ) from exc

    async def read(self, url: str) -> ImportedPR:
        repository, number = parse_pr_url(url)
        try:
            async with asyncio.timeout(MAX_SECONDS):
                pr = await self.get(f"/repos/{repository}/pulls/{number}", PullRequest)
                base_repo, head_repo = (
                    public_repository(pr.base.repo),
                    public_repository(pr.head.repo),
                )
                if base_repo.lower() != repository.lower() or pr.number != number:
                    raise GitHubError("invalid_response", "GitHub returned a different PR.", 502)
                # Pin both revisions once. Branch names and subsequent PR metadata are never used.
                head_owner = head_repo.split("/")[0]
                comparison = await self.get(
                    f"/repos/{base_repo}/compare/{pr.base.sha}...{head_owner}:{pr.head.sha}?per_page=1",
                    Comparison,
                )
                if comparison.base_commit.sha != pr.base.sha:
                    raise GitHubError("invalid_response", "GitHub returned a different base.", 502)
                merge_base = comparison.merge_base_commit.sha
                warnings: list[str] = []
                before = await self.snapshot(base_repo, merge_base, "base", warnings)
                after = await self.snapshot(head_repo, pr.head.sha, "head", warnings)
                if not before.files and not after.files:
                    warnings.append("No Python files were found in the supported analysis scope.")
                return ImportedPR(
                    AnalysisRequest(
                        base=before, head=after, label=f"{base_repo}#{number}: {pr.title}"[:160]
                    ),
                    GitHubSource(
                        repository=base_repo,
                        head_repository=head_repo,
                        pr_number=number,
                        pr_url=f"https://github.com/{base_repo}/pull/{number}",
                        title=pr.title,
                        base_sha=pr.base.sha,
                        head_sha=pr.head.sha,
                        merge_base_sha=merge_base,
                        analyzer_version=__version__,
                    ),
                    sorted(set(warnings)),
                )
        except (TimeoutError, httpx.TimeoutException) as exc:
            raise GitHubError(
                "timeout",
                "GitHub analysis timed out. Retry later or use a smaller repository.",
                504,
                True,
            ) from exc
        except httpx.HTTPError as exc:
            # Never surface upstream request objects, bodies, or credential-bearing exceptions.
            raise GitHubError(
                "network", "Could not connect to GitHub. Check connectivity and retry.", 502, True
            ) from exc

    async def snapshot(
        self, repository: str, sha: str, revision: str, warnings: list[str]
    ) -> Snapshot:
        commit = await self.get(f"/repos/{repository}/git/commits/{sha}", Commit)
        if commit.sha != sha:
            raise GitHubError("invalid_response", "GitHub returned a different commit.", 502)
        tree = await self.get(f"/repos/{repository}/git/trees/{commit.tree.sha}?recursive=1", Tree)
        if tree.sha != commit.tree.sha or tree.truncated:
            raise GitHubError(
                "incomplete_tree",
                "GitHub's file listing is incomplete. Choose a smaller repository; "
                "a partial impact report would omit dependencies.",
            )
        if len(tree.tree) > MAX_TREE_ENTRIES:
            raise GitHubError(
                "too_large", "Repository exceeds the 20,000-entry file listing limit."
            )
        files: dict[str, TreeEntry] = {}
        seen: set[str] = set()
        skipped: dict[str, list[str]] = {
            "symlinks": [],
            "submodules": [],
            "excluded Python files": [],
        }
        total = 0
        for entry in tree.tree:
            parsed_path = PurePosixPath(entry.path)
            if (
                parsed_path.is_absolute()
                or ".." in parsed_path.parts
                or "\\" in entry.path
                or ":" in entry.path
                or str(parsed_path) != entry.path
                or entry.path in seen
            ):
                raise GitHubError("invalid_path", "The repository contains unsupported file paths.")
            seen.add(entry.path)
            if entry.mode == "120000":
                skipped["symlinks"].append(entry.path)
                continue
            if entry.mode == "160000":
                skipped["submodules"].append(entry.path)
                continue
            if (entry.type, entry.mode) == ("tree", "040000"):
                continue
            if entry.type != "blob" or entry.mode not in {"100644", "100755"}:
                raise GitHubError(
                    "invalid_response", "GitHub returned an unsupported tree entry.", 502
                )
            if not entry.path.endswith(".py"):
                continue
            if any(part in EXCLUDED_DIRS for part in parsed_path.parts):
                skipped["excluded Python files"].append(entry.path)
                continue
            if entry.size is None:
                raise GitHubError("invalid_response", "GitHub omitted a Python file's size.", 502)
            total += entry.size
            if entry.size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES or len(files) >= 300:
                raise GitHubError(
                    "too_large",
                    "Repository exceeds 300 Python files, 200 KB per file, or 2 MB "
                    "per revision. Choose a smaller repository.",
                )
            files[entry.path] = entry
        for kind, paths in skipped.items():
            if paths:
                examples = ", ".join(sorted(paths)[:5])
                warnings.append(f"{revision}: skipped {len(paths)} {kind} ({examples}).")

        unique = {entry.sha: entry for entry in files.values()}
        tasks = [asyncio.create_task(self.blob(repository, entry)) for entry in unique.values()]
        try:
            await asyncio.gather(*tasks)
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        sources: dict[str, str] = {}
        for path, entry in sorted(files.items()):
            raw = self.blobs[entry.sha]
            if len(raw) != entry.size:
                raise GitHubError(
                    "invalid_response", "GitHub returned inconsistent file sizes.", 502
                )
            try:
                sources[path] = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise GitHubError(
                    "unsupported_encoding",
                    f"Python file is not UTF-8: {path}. No partial report was produced.",
                ) from exc
        return Snapshot(files=sources)

    async def blob(self, repository: str, entry: TreeEntry) -> None:
        if entry.sha in self.blobs:
            return
        blob = await self.get(f"/repos/{repository}/git/blobs/{entry.sha}", Blob, 400_000)
        try:
            raw = base64.b64decode("".join(blob.content.split()), validate=True)
        except (ValueError, binascii.Error) as exc:
            raise GitHubError(
                "invalid_response", "GitHub returned an invalid source blob.", 502
            ) from exc
        digest = hashlib.sha1(
            f"blob {len(raw)}\0".encode() + raw, usedforsecurity=False
        ).hexdigest()
        if blob.sha != entry.sha or digest != entry.sha or blob.size != len(raw):
            raise GitHubError(
                "invalid_response", "GitHub source content failed integrity checks.", 502
            )
        self.blobs[entry.sha] = raw
