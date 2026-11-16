"""Serve a built dashboard and protected API locally, using one bounded API process."""

import argparse
import logging
from pathlib import Path

import uvicorn

from codeimpact.api import create_app
from codeimpact.service import ServiceSettings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--static-dir", type=Path, default=Path("web/dist"))
    args = parser.parse_args(argv)
    try:
        if not 1 <= args.port <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        settings = ServiceSettings.from_env(require_key=True)
        application = create_app(settings, static_dir=args.static_dir)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Pilot configuration error: {exc}\n")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    uvicorn.run(
        application,
        host=args.host,
        port=args.port,
        workers=1,
        limit_concurrency=16,
        timeout_keep_alive=5,
        timeout_graceful_shutdown=5,
        proxy_headers=False,
        access_log=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
