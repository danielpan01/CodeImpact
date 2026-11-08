# CodeImpact daily maintenance report

Checked on **2026-11-08** (America/New_York).

Generated automatically by the daily project health workflow. This is a maintenance observation, not a new research result or application test run.

**Summary:** 0 failed checks; 0 unverified external checks.

| Check | Status | Observation |
| --- | --- | --- |
| README.md | PASS | Required file exists and is nonempty |
| CONTRIBUTING.md | PASS | Required file exists and is nonempty |
| pyproject.toml | PASS | Required file exists and is nonempty |
| requirements-dev.lock | PASS | Required file exists and is nonempty |
| web/package.json | PASS | Required file exists and is nonempty |
| web/package-lock.json | PASS | Required file exists and is nonempty |
| docs/ARCHITECTURE.md | PASS | Required file exists and is nonempty |
| docs/VALIDATION.md | PASS | Required file exists and is nonempty |
| docs/media/desktop.png | PASS | Required file exists and is nonempty |
| docs/media/mobile.png | PASS | Required file exists and is nonempty |
| README.md: CONTRIBUTING.md | PASS | Local target exists; fragment not checked |
| README.md: docs/ARCHITECTURE.md | PASS | Local target exists; fragment not checked |
| README.md: docs/BUILD_PLAN.md | PASS | Local target exists; fragment not checked |
| README.md: docs/CODEX_PROMPT.md | PASS | Local target exists; fragment not checked |
| README.md: docs/PROJECT_CONTEXT.md | PASS | Local target exists; fragment not checked |
| README.md: docs/VALIDATION.md | PASS | Local target exists; fragment not checked |
| README.md: docs/media/desktop.png | PASS | Local target exists; fragment not checked |
| Python syntax: src/codeimpact/__init__.py | PASS | Parsed without importing or executing the application |
| Python syntax: src/codeimpact/analyzer.py | PASS | Parsed without importing or executing the application |
| Python syntax: src/codeimpact/api.py | PASS | Parsed without importing or executing the application |
| Python syntax: src/codeimpact/cli.py | PASS | Parsed without importing or executing the application |
| Python syntax: src/codeimpact/demo.py | PASS | Parsed without importing or executing the application |
| Python syntax: src/codeimpact/models.py | PASS | Parsed without importing or executing the application |

## Dependency release watch

Live PyPI metadata compared alongside the declared constraints. The reported latest release may be outside those constraints. This does not resolve installed versions, test compatibility, audit vulnerabilities, or upgrade packages.

| Package | Repository constraint | PyPI latest | Latest release requires Python |
| --- | --- | --- | --- |
| Pygments | ==2.21.0 | 2.21.0 | >=3.9 |
| annotated-doc | ==0.0.5 | 0.0.5 | >=3.9 |
| annotated-types | ==0.8.0 | 0.8.0 | >=3.10 |
| anyio | ==4.16.0 | 4.16.0 | >=3.10 |
| certifi | ==2026.10.23 | 2026.10.23 | >=3.7 |
| click | ==8.5.0 | 8.5.1 | >=3.10 |
| coverage | ==7.17.2 | 7.17.2 | >=3.11 |
| fastapi | ==0.162.0 | 0.162.2 | >=3.10 |
| h11 | ==0.16.0 | 0.16.0 | >=3.8 |
| httpcore | ==1.0.9 | 1.0.9 | >=3.8 |
| httpx | ==0.28.1 | 0.28.1 | >=3.8 |
| idna | ==3.20 | 3.20 | >=3.9 |
| iniconfig | ==2.3.1 | 2.3.1 | >=3.10 |
| librt | ==0.16.0 | 0.16.0 | >=3.9 |
| mypy | ==1.20.2 | 2.4.1 | >=3.10 |
| mypy_extensions | ==1.2.0 | 1.2.0 | >=3.10 |
| opentelemetry-api | ==1.45.2 | 1.45.2 | >=3.10 |
| packaging | ==26.3 | 26.3 | >=3.9 |
| pathspec | ==1.1.1 | 1.1.1 | >=3.9 |
| pluggy | ==1.7.0 | 1.7.0 | >=3.10 |
| pydantic | ==2.14.3 | 2.14.3 | >=3.10 |
| pydantic_core | ==2.50.4 | 2.50.4 | >=3.10 |
| pytest-cov | ==7.1.0 | 7.1.0 | >=3.9 |
| pytest | ==9.2.0 | 9.2.0 | >=3.10 |
| ruff | ==0.17.4 | 0.17.4 | >=3.7 |
| starlette | ==1.10.0 | 1.10.0 | >=3.11 |
| typing-inspection | ==0.4.5 | 0.4.5 | >=3.10 |
| typing_extensions | ==4.16.0 | 4.16.0 | >=3.9 |
| uvicorn | ==0.54.0 | 0.54.0 | >=3.10 |

## Scope and history

Checks required repository files, documentation targets, Python source syntax, and live PyPI metadata for the pinned development environment. Does not execute analyzed repositories, change analyzer code or report schemas, modify dependencies, or claim full application or browser test coverage. Feature work remains separate from this generated maintenance report.

Local link checks cover inline Markdown and HTML file targets; heading fragments and reference-style links are not validated. External checks verify HTTP responses only, not page content. WARN means unverified, not a confirmed broken link.

The current report is replaced after each check; Git history preserves earlier observations. Same-day reruns with identical results produce no new commit.

[Workflow and attribution details](AUTOMATION.md)
