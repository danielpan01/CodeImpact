"""HTTP admission, access controls and source-free request logs for one API process."""

import asyncio
import hmac
import json
import logging
import math
import os
import threading
import time
import uuid
from dataclasses import dataclass, field

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from codeimpact.execution import MAX_INPUT, WorkerLimits

ANALYSIS_PATHS = {"/api/analyze", "/api/github/pr", "/api/demo"}
PRIVATE_PATHS = {"/api/analyze", "/api/github/pr"}
LOGGER = logging.getLogger("codeimpact.requests")


@dataclass(frozen=True)
class ServiceSettings:
    access_key: str = field(default="", repr=False)
    concurrency: int = 2
    requests_per_minute: int = 30
    body_seconds: float = 10
    request_seconds: float = 90
    worker: WorkerLimits = WorkerLimits()

    def __post_init__(self) -> None:
        if self.access_key and (
            len(self.access_key) < 32
            or len(self.access_key) > 256
            or not self.access_key.isascii()
            or not self.access_key.isprintable()
            or any(char.isspace() for char in self.access_key)
        ):
            raise ValueError(
                "Pilot access key must be 32–256 printable ASCII characters without spaces"
            )
        if type(self.concurrency) is not int or not 1 <= self.concurrency <= 8:
            raise ValueError("Concurrent analyses must be between 1 and 8")
        if type(self.requests_per_minute) is not int or not 1 <= self.requests_per_minute <= 600:
            raise ValueError("Request rate must be between 1 and 600 per minute")
        for value in (self.body_seconds, self.request_seconds):
            if not math.isfinite(value) or not 0 < value <= 120:
                raise ValueError("HTTP time budgets must be positive and at most 120 seconds")

    @classmethod
    def from_env(cls, *, require_key: bool = False) -> "ServiceSettings":
        key = os.environ.get("CODEIMPACT_ACCESS_KEY", "")
        if require_key and not key:
            raise ValueError("Set CODEIMPACT_ACCESS_KEY before starting the pilot server")
        return cls(
            access_key=key,
            concurrency=int(os.environ.get("CODEIMPACT_CONCURRENCY", "2")),
            requests_per_minute=int(os.environ.get("CODEIMPACT_REQUESTS_PER_MINUTE", "30")),
        )


class Admission:
    def __init__(self, settings: ServiceSettings):
        self.slots = threading.BoundedSemaphore(settings.concurrency)
        self.rate = settings.requests_per_minute
        self.tokens = float(self.rate)
        self.updated = time.monotonic()
        self.lock = threading.Lock()

    def rate_allowed(self) -> bool:
        with self.lock:
            now = time.monotonic()
            self.tokens = min(float(self.rate), self.tokens + (now - self.updated) * self.rate / 60)
            self.updated = now
            if self.tokens < 1:
                return False
            self.tokens -= 1
            return True


class RequestBoundary:
    """Authorize/admit before buffering bodies. Disconnects cancel and reap workers."""

    def __init__(self, app: ASGIApp, settings: ServiceSettings):
        self.app, self.settings = app, settings
        self.admission = Admission(settings)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        analysis = path in ANALYSIS_PATHS
        request_id = uuid.uuid4().hex
        started, status, response_started = time.monotonic(), 500, False
        acquired = False
        app_task: asyncio.Task[None] | None = None
        disconnect_task: asyncio.Task[None] | None = None

        async def secured_send(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started, status = True, message["status"]
                headers = list(message.get("headers", []))
                headers += [
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"x-request-id", request_id.encode()),
                ]
                if path.startswith("/api/"):
                    headers += [(b"cache-control", b"no-store")]
                message = {**message, "headers": headers}
            await send(message)

        async def reject(code: int, reason: str, message: str, *, retry: bool = False) -> None:
            delay = math.ceil(60 / self.admission.rate) if reason == "rate_limited" else 2
            headers = {"Retry-After": str(delay)} if retry else {}
            await JSONResponse(
                {"detail": {"code": reason, "message": message, "retryable": retry}},
                status_code=code,
                headers=headers,
            )(scope, receive, secured_send)

        try:
            if path in PRIVATE_PATHS and self.settings.access_key:
                auth = [
                    value
                    for key, value in scope.get("headers", [])
                    if key.lower() == b"authorization"
                ]
                expected = ("Bearer " + self.settings.access_key).encode("ascii")
                if len(auth) != 1 or not hmac.compare_digest(auth[0], expected):
                    await reject(
                        401,
                        "access_required",
                        "Enter the pilot access key to analyze your own code. The demo is public.",
                    )
                    return
            if analysis:
                if not self.admission.rate_allowed():
                    await reject(
                        429,
                        "rate_limited",
                        "The pilot request limit was reached. Wait before retrying.",
                        retry=True,
                    )
                    return
                acquired = self.admission.slots.acquire(blocking=False)
                if not acquired:
                    await reject(
                        503, "busy", "All analysis workers are busy. Retry shortly.", retry=True
                    )
                    return
            body = bytearray()
            try:
                async with asyncio.timeout(self.settings.body_seconds):
                    while True:
                        message = await receive()
                        if message["type"] == "http.disconnect":
                            status = 499
                            return
                        body.extend(message.get("body", b""))
                        if len(body) > MAX_INPUT:
                            await reject(413, "too_large", "Request too large")
                            return
                        if not message.get("more_body", False):
                            break
            except TimeoutError:
                await reject(
                    408, "body_timeout", "Request upload timed out. Retry with a smaller snapshot."
                )
                return
            delivered = False
            disconnected = asyncio.Event()

            async def replay() -> Message:
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                await disconnected.wait()
                return {"type": "http.disconnect"}

            async def disconnect() -> None:
                while True:
                    if (await receive())["type"] == "http.disconnect":
                        disconnected.set()
                        return

            async def dispatch() -> None:
                await self.app(scope, replay, secured_send)

            app_task = asyncio.create_task(dispatch())
            disconnect_task = asyncio.create_task(disconnect())
            done, _ = await asyncio.wait(
                {app_task, disconnect_task},
                timeout=self.settings.request_seconds,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if app_task in done:
                await app_task
            elif disconnect_task in done:
                status = 499
            else:
                if not response_started:
                    await reject(
                        504,
                        "request_timeout",
                        "The request exceeded the pilot time limit. Retry a smaller change.",
                    )
                else:
                    status = 504  # cannot replace headers already sent to a slow client
        except asyncio.CancelledError:
            status = 499
            raise
        finally:
            for task in (app_task, disconnect_task):
                if task is not None and not task.done():
                    task.cancel()
            await asyncio.gather(
                *(t for t in (app_task, disconnect_task) if t is not None), return_exceptions=True
            )
            if acquired:
                self.admission.slots.release()
            if analysis:
                LOGGER.info(
                    json.dumps(
                        {
                            "event": "analysis_request",
                            "request_id": request_id,
                            "route": path,
                            "status": status,
                            "duration_ms": round((time.monotonic() - started) * 1000, 2),
                        },
                        sort_keys=True,
                    )
                )
