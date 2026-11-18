"""Verify the real built pilot server over localhost with an ephemeral access key."""

import json
import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx

from codeimpact.holdout_evaluate import current_baseline
from codeimpact.real_evaluate import canonical_hash

ROOT = Path(__file__).resolve().parents[1]


def verify():
    dataset = ROOT / "corpus/real-v3"
    expected = current_baseline(dataset).measurement["analysis_sha256"]["inflection_title"]
    request = json.loads((dataset / "cases/inflection_title.json").read_text())["request"]
    key = secrets.token_urlsafe(32)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    environment = dict(os.environ, CODEIMPACT_ACCESS_KEY=key)
    # Logs contain only route/status/timing/request IDs; never print or persist the key.
    with subprocess.Popen(
        [
            sys.executable,
            "-m",
            "codeimpact.serve",
            "--port",
            str(port),
            "--static-dir",
            str(ROOT / "web/dist"),
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) as server:
        try:
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=30) as client:
                for _ in range(100):
                    if server.poll() is not None:
                        raise RuntimeError(
                            "Pilot server failed to start; verify configuration/build"
                        )
                    try:
                        if client.get("/ready").status_code == 200:
                            break
                    except httpx.ConnectError:
                        pass
                    time.sleep(0.1)
                else:
                    raise RuntimeError("Pilot server readiness timed out")
                assert client.get("/").status_code == 200
                assert "assets/" in client.get("/").text
                assert client.get("/health").status_code == 200
                assert client.get("/api/config").json() == {"access_required": True}
                assert client.get("/api/demo").status_code == 200
                assert client.post("/api/analyze", content="unparsed source").status_code == 401
                response = client.post(
                    "/api/analyze", json=request, headers={"Authorization": f"Bearer {key}"}
                )
                assert response.status_code == 200
                assert response.headers["cache-control"] == "no-store"
                assert key not in response.text
                report = response.json()
                report["stats"].pop("elapsed_ms")
                assert canonical_hash(report) == expected
                assert (
                    client.post(
                        "/api/github/pr", json={"url": "https://github.com/acme/repo/pull/1"}
                    ).status_code
                    == 401
                )
                assert client.get("/../pyproject.toml").status_code == 404
                assert client.get("/api/reports/unknown").status_code == 404
                print(
                    "Local pilot verified: readiness, static UI, public demo, protected analyses, "
                    "exact current report for the frozen input, no report storage."
                )
        finally:
            server.terminate()
            try:
                server.wait(timeout=8)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()


if __name__ == "__main__":
    verify()
