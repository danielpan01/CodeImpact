# CodeImpact

**See what a Python change could affect—and follow the evidence.**

CodeImpact compares two repository snapshots, builds an AST dependency graph, traces
potential impact, and prioritizes relevant tests. Every recommendation includes a
path from the test to a changed symbol. Paste a public GitHub PR URL, upload snapshots,
or read a local Git history. This is a working portfolio project, with
deliberate limitations; it is not yet a hosted GitHub App or a safe test-skipping system.

![CodeImpact impact explorer](docs/media/desktop.png)

## Run it

Prerequisites: Python 3.12+, Node 24, npm, Git. Dependencies are installed in the
active local Codex checkout. Start it from the repository root:

```sh
make dev
```

Open **http://127.0.0.1:5173**. API documentation: **http://127.0.0.1:8000/docs**.
Keep the terminal open; Ctrl-C stops both services. Ports 5173 and 8000 must be free.
This local server is not a phone-accessible deployment.

If another app uses port 8000, run `CODEIMPACT_API_PORT=8001 make dev` instead.
`CODEIMPACT_WEB_PORT` changes the website port. The website's API reference link and
proxy follow these settings. Restart `make dev` after backend changes. Browser tests
start their own servers on ports 8002 and 5174; those two ports must be free.

For a fresh checkout, install the pinned dependencies first:

```sh
make setup
make check
cd web
npm run install:browsers
npm run test:e2e
cd ..
make dev
```

Use `python3.12 -m venv .venv` first if your `python3` is older than 3.12.

## Try the demo

1. The checkout demo changes `discount(total)` from 10% to 15%.
2. The changed function turns coral. Dependent callers and tests turn amber.
3. Click a test and follow the evidence chain. The API test depends on
   `create_order → checkout → discount`; the health test has no path to the change.
4. Toggle **Module dependencies** to inspect the broader fallback graph.
5. Export the report, or upload a JSON snapshot pair to analyze your own code.

The displayed timing is measured for that request. It is not a benchmark claim.

## Analyze a public GitHub PR

1. Paste an exact `https://github.com/owner/repo/pull/number` URL into **Analyze a
   GitHub pull request**, then press Enter or **Analyze PR**.
2. Try [MarkupSafe PR #469](https://github.com/pallets/markupsafe/pull/469), the small
   public PR checked for this milestone. It changes `escape` in Python source.
3. Expand **Exact analyzed revisions**. The before snapshot is the merge base;
   the after snapshot is the pinned PR head. The target branch SHA is also recorded.
4. Use **Tests** to inspect recommendations and their evidence. Use search to find
   `escape` in the map. The graph may be large; zoom or filter it to read individual nodes.
5. Export the JSON report to retain the revision metadata. A later submission reads
   the PR's current revisions again, so it may legitimately produce a different report.

The server downloads complete Python snapshots within the supported scope, including
unchanged callers and tests. It never executes, imports, checks out or installs the
downloaded code. Public fork PRs are supported. Private repositories are rejected.

No token is required. Anonymous GitHub limits can be exhausted by repeated analyses;
the app displays a retry message instead of returning a partial report. An optional
`CODEIMPACT_GITHUB_TOKEN` may be supplied through the **server's environment** before
starting it. Keep it out of browser settings, URLs, source control and chat. Do not
prefix it with `VITE_`. The launcher does not automatically load `.env` files.

Limits per revision: 300 Python files, 200,000 bytes per file, 2,000,000 source bytes.
Truncated or oversized listings fail explicitly. Symlinks, submodules and Python
files in `.venv`, `venv`, `node_modules`, `vendor` or `.git` are skipped with warnings.
Non-UTF-8 Python files are rejected. Other languages are outside the analysis scope.
See [network bounds and failure behavior](docs/ARCHITECTURE.md#public-github-ingestion).

The equivalent API request, through the running website proxy:

```sh
mkdir -p reports
curl --fail-with-body http://127.0.0.1:5173/api/github/pr \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://github.com/pallets/markupsafe/pull/469"}' \
  > reports/github-pr.json
```

## Analyze a real local pull-request branch

CodeImpact reads committed Git objects without switching branches or executing code.
It compares the merge base of `base` and `head` with `head`, matching PR-style scope.
Uncommitted working-tree changes are not included.

```sh
mkdir -p reports
.venv/bin/codeimpact --repo /absolute/path/to/python-repo \
  --base main --head feature-branch > reports/impact.json

# Export input for the dashboard's Analyze snapshots button:
.venv/bin/codeimpact --repo /absolute/path/to/python-repo \
  --base main --head feature-branch --snapshots > reports/snapshots.json

# A self-contained example without a Git history:
.venv/bin/codeimpact --demo --snapshots > reports/demo-snapshots.json
```

Snapshot input:

```json
{
  "label": "My change",
  "base": {"files": {"app.py": "def price(): return 10\n"}},
  "head": {"files": {"app.py": "def price(): return 15\n"}}
}
```

## What works today

- Python module, class, function, nested-function and test symbol indexing.
- Selected absolute/relative imports, aliases, direct calls and `src/` layouts.
- AST comparison that ignores comments, whitespace and source line movement.
- Base/head graph union that retains deleted dependencies; renames as remove+add.
- Cycle-safe reverse traversal, deterministic ranking and inspectable evidence paths.
- Distinct resolved-call evidence and conservative module/import estimates.
- Stateless FastAPI API, Git CLI, responsive React/TypeScript graph, JSON upload/export.
- Public GitHub PR input with pinned merge-base/head snapshots, fork support and provenance.
- Backend, API and temporary Git-repository tests; desktop/mobile browser tests; CI.

## What comes next

Private-repository GitHub App permissions, persisted jobs, cross-request caching,
hosted deployment and real-repository accuracy evaluation are **not
implemented**. Follow [the phased build plan](docs/BUILD_PLAN.md).

Static Python analysis cannot fully resolve dynamic dispatch, runtime imports,
re-exports, inheritance or pytest fixtures. A missing path does not establish safety.
Scores are explainable prioritization heuristics, not failure probabilities.
Keep the complete test suite as your merge gate.

## Project map

```text
src/codeimpact/    AST engine, contracts, GitHub ingestion, API, demo and Git CLI
web/              React + TypeScript + React Flow dashboard and browser tests
tests/            Correctness, API and Git integration tests
scripts/dev.py    Local process launcher
.github/          CI and pull-request template
docs/             Architecture, roadmap, context, validation and Codex prompt
```

- [Architecture and exact scoring](docs/ARCHITECTURE.md)
- [Build and portfolio plan](docs/BUILD_PLAN.md)
- [Copyable Codex implementation prompt](docs/CODEX_PROMPT.md)
- [Cross-device project context](docs/PROJECT_CONTEXT.md)
- [Validation record](docs/VALIDATION.md)
- [Contribution workflow](CONTRIBUTING.md)

## Review, commit and push

The active local Codex project is `/Users/danny/Documents/ChatGPT/CodeImpact`.
This milestone started from local commit `34eb6b0` on `main` (the empty-module fix).
Agent changes remain unstaged and uncommitted; no remote update is claimed.
Review them and use your own Git identity:

```sh
git status
git config --get user.name
git config --get user.email
make check
git diff --check
git diff
# Also review new files shown by git status before staging.
git add README.md docs/ARCHITECTURE.md docs/BUILD_PLAN.md docs/PROJECT_CONTEXT.md \
  docs/VALIDATION.md pyproject.toml scripts/dev.py src/codeimpact/api.py \
  src/codeimpact/models.py src/codeimpact/github.py tests/test_github.py \
  tests/browser_api.py web/src/main.tsx web/src/types.ts web/src/style.css \
  web/tests/app.spec.ts web/vite.config.ts web/playwright.config.ts
git diff --cached --stat
git diff --cached
git commit -m "Add bounded public GitHub PR analysis"
git push -u origin main
```

Remote: [danielpan01/codeimpact](https://github.com/danielpan01/codeimpact).
No automatic file sync was configured. Push reviewed changes yourself before another
checkout or cloud chat can retrieve them from GitHub. GitHub connector access to this
private repository was verified; cloud checkout access is environment-dependent.
Choose an open-source license and change visibility when you are ready to publish.

