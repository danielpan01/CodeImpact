# Usage guide

Detailed local setup, demo walkthroughs, GitHub PR analysis, and CLI examples.

[Back to the project overview](../README.md)

## Start the application

Prerequisites: Python 3.12+, Node 24, npm, Git. After installing dependencies with `make setup`, start from the repository root:

```sh
make dev
```

Open **http://127.0.0.1:5173**. API documentation: **http://127.0.0.1:8000/docs**.
Keep the terminal open; Ctrl-C stops both services. Ports 5173 and 8000 must be free.
This local server is not a phone-accessible deployment.

If another app uses port 8000, run `CODEIMPACT_API_PORT=8001 make dev` instead.
`CODEIMPACT_WEB_PORT` changes the website port. The website's API reference link and
proxy follow these settings. Restart `make dev` after backend changes. If refreshed
pages still show old controls, restart the frontend too; a running Vite process can
retain old compiled modules in this local environment. Browser tests
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

Ensure `python3` selects Python 3.12 or newer before running `make setup`. The checked-in baseline uses Python 3.12 and Node 24.

## Try the demo

1. The checkout demo changes `discount(total)` from 10% to 15%.
2. The changed function turns coral. Dependent callers and tests turn amber.
3. Click a test and follow the evidence chain. The API test depends on
   `create_order → checkout → discount`; the health test has no path to the change.
4. Click **Open changed code**. **Changes** shows `discount` before and after with
   source line numbers; the test explanation stays beside it (below on mobile).
   Each dependency identifies **Before only**, **After only**, or **Both revisions**.
   Expand its **Before**/**After** evidence to inspect call/import locations.
5. Switch between **Map**, **Tests**, and **Changes**. Changes are grouped by file and
   labeled added, modified or removed. Module entries include module-level statements.
6. Toggle **Module dependencies** in Map to inspect the broader fallback graph.
7. Export the report, or upload a JSON snapshot pair to analyze your own code.

To inspect a deleted function and a mixed path, use **Analyze snapshots** to upload
[`tests/fixtures/mixed-revisions.json`](../tests/fixtures/mixed-revisions.json). Select
**Tests → test_g → Open changed code**. The before panel shows `a.py::f`; the after
panel identifies the present but empty file. The explanation says **Mixed revisions**:
`test_g → g` exists only after, while `g → f` exists only before. Neither revision
contains that entire shown path. This is a conservative estimate, not an executable
call sequence from one revision. **Load demo** restores the original example.

**Report schema 2.0 exports contain complete before/after source for files with
semantic changes**, including content beyond the displayed preview. Source is stored
once per file per revision, never once per symbol. Previews show at most 120 lines,
12,000 characters and 500 characters per line, with visible truncation notices.
Only the exact analyzed snapshots are used. Definitions include decorators; absent
files, empty files and parse failures have distinct displays. Source renders as text.
Old 1.0 reports require re-analysis from snapshots; update API and dashboard together.
Snapshot upload input is unchanged. See [the report contract](ARCHITECTURE.md#report-20-contract).

The displayed timing is measured for that request. It is not a benchmark claim.

## Analyze a public GitHub PR

1. Paste an exact `https://github.com/owner/repo/pull/number` URL into **Analyze a
   GitHub pull request**, then press Enter or **Analyze PR**.
2. Try [MarkupSafe PR #469](https://github.com/pallets/markupsafe/pull/469), the small
   public PR checked for this milestone. It changes `escape` in Python source.
3. Expand **Exact analyzed revisions**. The before snapshot is the merge base;
   the after snapshot is the pinned PR head. The target branch SHA is also recorded.
4. Use **Tests → Open changed code** to inspect a recommendation's changed endpoint
   and its before/after source. **Changes** also lists changed symbols by file.
   Use search to find `escape` in the map. The graph may be large; zoom or filter it.
5. Export the JSON report to retain the revision metadata, source and typed evidence.
   A later submission reads
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
See [network bounds and failure behavior](ARCHITECTURE.md#public-github-ingestion).

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

