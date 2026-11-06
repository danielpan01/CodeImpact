"""Local API. Snapshot sources are parsed as data and never executed."""

from fastapi import FastAPI, HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from codeimpact.analyzer import analyze
from codeimpact.demo import demo_request
from codeimpact.models import AnalysisRequest, Report


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
