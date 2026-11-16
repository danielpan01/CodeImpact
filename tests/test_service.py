"""Admission/authentication before source buffering; cancellation releases service slots."""

import asyncio
import json
import logging

import httpx
import pytest
from fastapi.testclient import TestClient

from codeimpact.api import create_app
from codeimpact.demo import demo_request
from codeimpact.service import ServiceSettings

KEY = "test-only-pilot-key-with-at-least-32-characters"


def test_access_control_public_demo_and_source_free_logs(caplog):
    app = create_app(ServiceSettings(access_key=KEY, requests_per_minute=600))
    with TestClient(app) as client, caplog.at_level(logging.INFO, logger="codeimpact.requests"):
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 200
        assert client.get("/api/config").json() == {"access_required": True}
        assert client.get("/api/demo").status_code == 200
        assert client.get("/api/demo/snapshots").status_code == 200
        for headers in (
            {},
            {"Authorization": "Bearer wrong"},
            [("Authorization", f"Bearer {KEY}"), ("Authorization", "extra")],
        ):
            response = client.post("/api/analyze", content=b"not JSON", headers=headers)
            assert response.status_code == 401
            assert response.json()["detail"]["code"] == "access_required"
        assert client.post("/api/github/pr", json={"url": "private-label"}).status_code == 401
        response = client.post(
            "/api/analyze",
            json=demo_request().model_dump(),
            headers={"Authorization": f"Bearer {KEY}"},
        )
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert len(response.headers["x-request-id"]) == 32
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "fingerprint" not in response.text
        assert KEY not in response.text
        assert KEY not in caplog.text and "private-label" not in caplog.text
        entries = [json.loads(r.message) for r in caplog.records if r.name == "codeimpact.requests"]
        assert entries and all(
            set(e) == {"event", "request_id", "route", "status", "duration_ms"} for e in entries
        )
        assert "shop/pricing.py" not in caplog.text
    assert app.state.runner.closed
    assert not app.state.runner.processes


def test_authentication_happens_before_reading_body():
    async def exercise():
        app = create_app(ServiceSettings(access_key=KEY))
        messages = []

        async def receive():
            pytest.fail("unauthorized request body was read")

        async def send(message):
            messages.append(message)

        await app(
            {
                "type": "http",
                "path": "/api/analyze",
                "method": "POST",
                "headers": [],
                "query_string": b"",
                "http_version": "1.1",
            },
            receive,
            send,
        )
        assert messages[0]["status"] == 401
        assert not app.state.runner.processes

    asyncio.run(exercise())


def test_rate_limit_keeps_health_available():
    app = create_app(ServiceSettings(requests_per_minute=1))
    with TestClient(app) as client:
        assert client.get("/api/demo").status_code == 200
        response = client.get("/api/demo")
        assert response.status_code == 429
        assert response.headers["retry-after"]
        assert client.get("/health").status_code == 200


def test_capacity_cancellation_and_recovery(monkeypatch):
    async def exercise():
        app = create_app(ServiceSettings(concurrency=1))
        runner = app.state.runner
        original = runner.run
        entered, cancelled = asyncio.Event(), asyncio.Event()

        async def slow(request):
            entered.set()
            try:
                await asyncio.sleep(30)
            finally:
                cancelled.set()

        monkeypatch.setattr(runner, "run", slow)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            job = asyncio.create_task(client.get("/api/demo"))
            await entered.wait()
            response = await client.get("/api/demo")
            assert response.status_code == 503 and response.json()["detail"]["code"] == "busy"
            assert (await client.get("/health")).status_code == 200
            job.cancel()
            with pytest.raises(asyncio.CancelledError):
                await job
            assert cancelled.is_set()
            monkeypatch.setattr(runner, "run", original)
            assert (await client.get("/api/demo")).status_code == 200

    asyncio.run(exercise())


def test_disconnect_cancels_inflight_work_and_frees_slot(monkeypatch):
    async def exercise():
        app = create_app(ServiceSettings(concurrency=1))
        original = app.state.runner.run
        entered, stopped = asyncio.Event(), asyncio.Event()
        incoming = asyncio.Queue()
        await incoming.put({"type": "http.request", "body": b"", "more_body": False})
        messages = []

        async def slow(request):
            entered.set()
            try:
                await asyncio.sleep(30)
            finally:
                stopped.set()

        async def send(message):
            messages.append(message)

        monkeypatch.setattr(app.state.runner, "run", slow)
        task = asyncio.create_task(
            app(
                {
                    "type": "http",
                    "path": "/api/demo",
                    "method": "GET",
                    "headers": [],
                    "query_string": b"",
                    "http_version": "1.1",
                },
                incoming.get,
                send,
            )
        )
        await entered.wait()
        await incoming.put({"type": "http.disconnect"})
        await asyncio.wait_for(task, 1)
        assert stopped.is_set()
        assert messages == []
        monkeypatch.setattr(app.state.runner, "run", original)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            assert (await client.get("/api/demo")).status_code == 200

    asyncio.run(exercise())


def test_total_request_and_body_timeouts_release_capacity(monkeypatch):
    async def exercise():
        app = create_app(ServiceSettings(concurrency=1, body_seconds=0.03, request_seconds=0.03))
        stopped = asyncio.Event()

        async def slow(request):
            try:
                await asyncio.sleep(30)
            finally:
                stopped.set()

        monkeypatch.setattr(app.state.runner, "run", slow)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/demo")
            assert response.status_code == 504 and stopped.is_set()

            async def slow_body():
                yield b"{"
                await asyncio.sleep(30)

            response = await client.post("/api/analyze", content=slow_body())
            assert response.status_code == 408
            assert (await client.get("/health")).status_code == 200

    asyncio.run(exercise())


def test_validation_and_large_body_errors_do_not_echo_source():
    client = TestClient(create_app())
    response = client.post("/api/analyze", json={"secret-source": "private source text"})
    assert response.status_code == 422
    assert "private source text" not in response.text
    assert client.post("/api/analyze", content=b"x" * 6_000_001).status_code == 413
    assert client.get("/api/demo").status_code == 200


def test_static_deployment_only_serves_built_assets(tmp_path):
    (tmp_path / "index.html").write_text("<h1>Built dashboard</h1>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/app.js").write_text("/* fixture asset */")
    app = create_app(ServiceSettings(access_key=KEY), static_dir=tmp_path)
    with TestClient(app) as client:
        assert "Built dashboard" in client.get("/").text
        assert client.get("/assets/app.js").status_code == 200
        assert client.get("/../../pyproject.toml").status_code == 404
        assert client.get("/api/reports/unknown").status_code == 404
        assert client.get("/ready").status_code == 200
    assert not app.state.ready


def test_pilot_configuration_fails_closed(monkeypatch, tmp_path, capsys):
    from codeimpact.serve import main

    monkeypatch.delenv("CODEIMPACT_ACCESS_KEY", raising=False)
    with pytest.raises(ValueError, match="CODEIMPACT_ACCESS_KEY"):
        ServiceSettings.from_env(require_key=True)
    with pytest.raises(SystemExit) as result:
        main(["--static-dir", str(tmp_path)])
    assert result.value.code == 2
    assert "CODEIMPACT_ACCESS_KEY" in capsys.readouterr().err
    monkeypatch.setenv("CODEIMPACT_ACCESS_KEY", KEY)
    with pytest.raises(ValueError, match="Build the frontend"):
        create_app(ServiceSettings.from_env(require_key=True), static_dir=tmp_path)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"access_key": "short"},
        {"access_key": "界" * 32},
        {"access_key": "\n" * 32},
        {"concurrency": 0},
        {"concurrency": 9},
        {"requests_per_minute": 0},
        {"body_seconds": float("nan")},
        {"request_seconds": 0},
    ],
)
def test_invalid_service_settings_fail_early(kwargs):
    with pytest.raises(ValueError):
        ServiceSettings(**kwargs)
