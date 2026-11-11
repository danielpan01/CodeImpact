"""Versioned API contracts and resource limits shared by every entry point."""

from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_FILE_BYTES = 200_000
MAX_TOTAL_BYTES = 2_000_000


class Snapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    files: dict[str, str] = Field(max_length=300)

    @model_validator(mode="after")
    def validate_sources(self) -> "Snapshot":
        total = 0
        for name, source in self.files.items():
            path = PurePosixPath(name)
            if (
                not name.endswith(".py")
                or path.is_absolute()
                or ".." in path.parts
                or "\\" in name
                or ":" in name
                or str(path) != name
                or len(name) > 500
            ):
                raise ValueError("Paths must be normalized, relative POSIX Python file paths")
            size = len(source.encode("utf-8"))
            if size > MAX_FILE_BYTES:
                raise ValueError(f"File exceeds {MAX_FILE_BYTES} bytes: {name}")
            total += size
        if total > MAX_TOTAL_BYTES:
            raise ValueError(f"Snapshot exceeds {MAX_TOTAL_BYTES} bytes")
        return self


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base: Snapshot
    head: Snapshot
    label: str = Field(default="Snapshot comparison", max_length=160)


class Symbol(BaseModel):
    id: str
    name: str
    path: str
    line: int
    end_line: int
    kind: Literal["module", "function", "class", "test"]
    fingerprint: str = Field(exclude=True)


class SourceRange(BaseModel):
    """Inclusive, one-based lines; definitions start at their first decorator."""

    line: int
    end_line: int


class SourceLocation(SourceRange):
    path: str


class SourceRevision(BaseModel):
    text: str
    parse_status: Literal["parsed", "unparseable"]


class SourceFile(BaseModel):
    path: str
    before: SourceRevision | None
    after: SourceRevision | None


class SymbolChange(BaseModel):
    symbol: str
    path: str
    status: Literal["added", "modified", "removed"]
    before: SourceRange | None
    after: SourceRange | None


class DependencyEvidence(BaseModel):
    text: str
    location: SourceLocation
    target_location: SourceLocation


EdgeKind = Literal["call", "import", "module"]
RevisionPresence = Literal["before", "after", "both"]


class Edge(BaseModel):
    id: str
    source: str
    target: str
    kind: EdgeKind
    revision: RevisionPresence
    before: list[DependencyEvidence]
    after: list[DependencyEvidence]


class Recommendation(BaseModel):
    symbol: str
    score: int
    distance: int
    reason: str
    evidence_path: list[str]
    evidence_edges: list[str]
    path_revision: Literal["before", "after", "both", "mixed"]


class Report(BaseModel):
    schema_version: Literal["2.0"] = "2.0"
    label: str
    nodes: list[Symbol]
    edges: list[Edge]
    changed: list[str]
    changes: list[SymbolChange]
    source_files: list[SourceFile]
    removed: list[str]
    impacted: list[str]
    recommendations: list[Recommendation]
    warnings: list[str]
    stats: dict[str, int | float]


class GitHubPRRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(min_length=1, max_length=300)


class GitHubSource(BaseModel):
    kind: Literal["github_pr"] = "github_pr"
    repository: str
    head_repository: str
    pr_number: int
    pr_url: str
    title: str
    base_sha: str
    head_sha: str
    merge_base_sha: str
    analyzer_version: str


class GitHubPRReport(Report):
    """The same versioned report as demo/upload/CLI, with pinned GitHub provenance."""

    source: GitHubSource
