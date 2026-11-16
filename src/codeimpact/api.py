"""Stateless API with bounded, disposable analysis workers."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from codeimpact.demo import demo_request
from codeimpact.execution import WorkerError, WorkerRunner
from codeimpact.github import CONCURRENCY, GitHubError, GitHubReader
from codeimpact.models import AnalysisRequest, GitHubPRReport, GitHubPRRequest, Report
from codeimpact.service import RequestBoundary, ServiceSettings


async def github_reader() -> AsyncIterator[GitHubReader]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "CodeImpact/0.1",
    }
    if token := os.environ.get("CODEIMPACT_GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(
        headers=headers, follow_redirects=False, limits=httpx.Limits(max_connections=CONCURRENCY)
    ) as client:
        yield GitHubReader(client)


def create_app(
    settings: ServiceSettings | None = None, *, static_dir: Path | None = None
) -> FastAPI:
    settings = settings or ServiceSettings.from_env()
    runner = WorkerRunner(settings.worker)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        try:
            await runner.run(demo_request())  # verify spawning/monitoring before readiness
            application.state.ready = True
            yield
        finally:
            application.state.ready = False
            await runner.close()

    application = FastAPI(title="CodeImpact", version="0.1.0", lifespan=lifespan)
    application.state.ready = False
    application.state.runner = runner
    application.add_middleware(RequestBoundary, settings=settings)

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    @application.get("/ready")
    async def ready() -> JSONResponse:
        available = application.state.ready and not runner.closed
        return JSONResponse(
            {"status": "ready" if available else "unavailable"},
            status_code=200 if available else 503,
        )

    @application.get("/api/config")
    async def config() -> dict[str, bool]:
        return {"access_required": bool(settings.access_key)}

    @application.get("/api/demo", response_model=Report)
    async def demo() -> Report:
        return (await runner.run(demo_request())).report

    @application.get("/api/demo/snapshots", response_model=AnalysisRequest)
    async def snapshots() -> AnalysisRequest:
        return demo_request()

    @application.post("/api/analyze", response_model=Report)
    async def compare(request: AnalysisRequest) -> Report:
        return (await runner.run(request)).report

    @application.exception_handler(WorkerError)
    async def worker_error(_request: Request, exc: WorkerError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content={"detail": exc.detail()})

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        if request.url.path == "/api/github/pr":
            detail: str | dict[str, str | bool] = {
                "code": "invalid_request",
                "message": "Provide one public GitHub PR URL in the url field.",
                "retryable": False,
            }
        else:
            # Validation details can echo submitted source. Keep errors source-free.
            detail = "Invalid snapshot request. Check file paths, source sizes and request fields."
        return JSONResponse(status_code=422, content={"detail": detail})

    @application.post("/api/github/pr", response_model=GitHubPRReport)
    async def compare_github(
        request: GitHubPRRequest, reader: Annotated[GitHubReader, Depends(github_reader)]
    ) -> GitHubPRReport:
        try:
            imported = await reader.read(request.url)
            report = (await runner.run(imported.request)).report
            report.warnings = sorted(set(report.warnings + imported.warnings))
            return GitHubPRReport(**dict(report), source=imported.source)
        except GitHubError as exc:
            raise HTTPException(status_code=exc.status, detail=exc.detail()) from exc
        except (ValueError, RecursionError) as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "unsupported_source",
                    "message": "Unsupported or overly complex Python source.",
                    "retryable": False,
                },
            ) from exc

    if static_dir is not None:
        if not (static_dir / "index.html").is_file() or not (static_dir / "assets").is_dir():
            raise ValueError("Build the frontend before starting the pilot server")
        application.mount("/", StaticFiles(directory=static_dir, html=True, follow_symlink=False))
    return application


app = create_app()
