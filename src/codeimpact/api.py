"""Local API. Snapshot sources are parsed as data and never executed."""

import os
from collections.abc import AsyncIterator
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from codeimpact.analyzer import analyze
from codeimpact.demo import demo_request
from codeimpact.github import CONCURRENCY, GitHubError, GitHubReader
from codeimpact.models import AnalysisRequest, GitHubPRReport, GitHubPRRequest, Report


class BodyLimit:
    """Bound even chunked JSON bodies before FastAPI allocates/parses the request."""

    def __init__(self, app: ASGIApp, limit: int = 6_000_000) -> None:
        self.app, self.limit = app, limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        chunks: list[Message] = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.limit:
                await send(
                    {
                        "type": "http.response.start",
                        "status": 413,
                        "headers": [(b"content-type", b"application/json")],
                    }
                )
                await send(
                    {"type": "http.response.body", "body": b'{"detail":"Request too large"}'}
                )
                return
            chunks.append(message)
            if not message.get("more_body", False):
                break
        position = 0

        async def replay() -> Message:
            nonlocal position
            if position < len(chunks):
                message = chunks[position]
                position += 1
                return message
            return await receive()

        await self.app(scope, replay, send)


app = FastAPI(title="CodeImpact", version="0.1.0")
app.add_middleware(BodyLimit)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/demo", response_model=Report)
def demo() -> Report:
    return analyze(demo_request())


@app.get("/api/demo/snapshots", response_model=AnalysisRequest)
def snapshots() -> AnalysisRequest:
    return demo_request()


@app.post("/api/analyze", response_model=Report)
def compare(request: AnalysisRequest) -> Report:
    try:
        return analyze(request)
    except (ValueError, RecursionError) as exc:
        raise HTTPException(status_code=422, detail="Unsupported or overly complex source") from exc


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


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    if request.url.path == "/api/github/pr":
        return JSONResponse(
            status_code=422,
            content={
                "detail": {
                    "code": "invalid_request",
                    "message": "Provide one public GitHub PR URL in the url field.",
                    "retryable": False,
                }
            },
        )
    return await request_validation_exception_handler(request, exc)


@app.post("/api/github/pr", response_model=GitHubPRReport)
async def compare_github(
    request: GitHubPRRequest, reader: Annotated[GitHubReader, Depends(github_reader)]
) -> GitHubPRReport:
    try:
        imported = await reader.read(request.url)
        report = await run_in_threadpool(analyze, imported.request)
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
