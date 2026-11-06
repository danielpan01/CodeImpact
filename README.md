# CodeImpact

**See what a Python change could affect—and follow the evidence.**

CodeImpact compares two repository snapshots, builds an AST dependency graph, traces
potential impact, and prioritizes relevant tests. Every recommendation includes a
path from the test to a changed symbol. This is a working portfolio starter, with
deliberate limitations; it is not yet a hosted GitHub App or a safe test-skipping system.

![CodeImpact impact explorer](docs/media/desktop.png)

## Run it

Prerequisites: Python 3.12+, Node 24, npm, Git. Dependencies are already installed in
the original local checkout. Start it from the repository root:

```sh
make dev
```

Open **http://127.0.0.1:5173**. API documentation: **http://127.0.0.1:8000/docs**.
Keep the terminal open; Ctrl-C stops both services. Ports 5173 and 8000 must be free.
This local server is not a phone-accessible deployment.

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
- Backend, API and temporary Git-repository tests; desktop/mobile browser tests; CI.

## What comes next

Live GitHub PR URL ingestion, private-repository GitHub App permissions, persisted
jobs, SHA-keyed caching, hosted deployment and real-repository evaluation are **not
implemented**. Follow [the phased build plan](docs/BUILD_PLAN.md).

Static Python analysis cannot fully resolve dynamic dispatch, runtime imports,
re-exports, inheritance or pytest fixtures. A missing path does not establish safety.
Scores are explainable prioritization heuristics, not failure probabilities.
Keep the complete test suite as your merge gate.

## Project map

```text
src/codeimpact/    AST engine, contracts, API, demo and Git CLI
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

## Your first commit and push

The setup agent created a private GitHub repository and a local `main` branch with
`origin` configured. It did **not** commit, stage, or push these project files.
Review them and use your own Git identity:

```sh
git status
git config --get user.name
git config --get user.email
make check
git add .
git diff --cached --stat
git diff --cached
git commit -m "Build CodeImpact analysis MVP"
git push -u origin main
```

Remote: [danielpan01/codeimpact](https://github.com/danielpan01/codeimpact).
The repository remains empty on GitHub until you push. No automatic file sync was
configured. After your first push, the cloud chat can attempt to read it through your
connected GitHub account; connector access to this new private repo was verified.
Choose an open-source license and change visibility when you are ready to publish.

