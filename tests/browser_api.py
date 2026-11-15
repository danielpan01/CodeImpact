"""Playwright-only API: real importer/analyzer, deterministic mocked GitHub transport.

Never load this module in the development server. No test switch in the public API.
"""

import httpx
from test_github import FakeGitHub

from codeimpact.api import create_app, github_reader
from codeimpact.github import GitHubReader
from codeimpact.service import ServiceSettings

app = create_app(ServiceSettings(concurrency=8, requests_per_minute=600))


async def reader():
    # Fresh metadata per request; the fixture simulates branch movement after retrieval.
    server = FakeGitHub(fork=True)
    async with httpx.AsyncClient(transport=httpx.MockTransport(server)) as client:
        yield GitHubReader(client)


app.dependency_overrides[github_reader] = reader
