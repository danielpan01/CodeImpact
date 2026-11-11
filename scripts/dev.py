"""Run the API and web app; stop both when either exits or Ctrl-C is pressed."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
api_port = int(os.environ.get("CODEIMPACT_API_PORT", "8000"))
web_port = int(os.environ.get("CODEIMPACT_WEB_PORT", "5173"))
if not all(1 <= port <= 65535 for port in (api_port, web_port)):
    sys.exit("CodeImpact ports must be between 1 and 65535.")
processes: list[subprocess.Popen[bytes]] = []
exit_code = 0
try:
    processes.append(
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "codeimpact.api:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(api_port),
            ],
            cwd=root,
            start_new_session=True,
        )
    )
    processes.append(
        subprocess.Popen(["npm", "run", "dev"], cwd=root / "web", start_new_session=True)
    )
    print(
        f"CodeImpact: http://127.0.0.1:{web_port} | API: http://127.0.0.1:{api_port}/docs",
        flush=True,
    )
    while all(process.poll() is None for process in processes):
        time.sleep(0.5)
    exit_code = next((p.returncode for p in processes if p.returncode), 1)
except KeyboardInterrupt:
    pass
finally:
    for process in processes:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
    for process in processes:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
sys.exit(exit_code)
