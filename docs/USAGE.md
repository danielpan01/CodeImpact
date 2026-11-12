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

1. Choose **Load demo** on the initial input screen. The checkout demo changes
   `discount(total)` from 10% to 15%. Successful analyses open **Tests** and collapse
   the input form; **New analysis** reopens PR input, snapshot upload and the demo.
2. Select `test_create_order`. Its reason and dependency trail appear in the evidence
   inspector: `test_create_order → create_order → checkout → discount`.
   Priorities (82, 72 and 62 for this demo) are heuristics, not failure probabilities.
3. On phones and tablets, selecting a test opens a full-width evidence pane. Use
   **Back to results** or Escape to return, or **View evidence** to reopen the current
   selection. Map, Tests and Changes remain accessible above the pane.
4. Choose **Open changed code**. **Changes** shows `discount` before and after with
   source line numbers, side by side on wider screens and stacked on phones. The test
   explanation is retained; reopen **View evidence** on small screens to see it.
   Dependencies visibly distinguish **Before only**, **After only**, **Both revisions**
   and **Mixed revisions**. Expand **Before**/**After** evidence for source locations.
5. Switch between **Tests**, **Map**, and **Changes** without losing the selected test
   or expanded evidence. Selecting a changed symbol directly replaces the inspector
   with that symbol's own details. **Changed files & symbols** expands/collapses file
   navigation; added, modified and removed symbols have text labels.
6. Choose **Focus path in Map** in the evidence inspector (or **Focus path** in Map).
   Focus shows only the exact recorded path, including any module fallback. Use
   **Jump to path symbol** to center a step at readable scale, **Inspect test** to
   return to its explanation, and **Fit view** to see the entire path. Pan/zoom
   persists across view switches. **Reset map** clears graph search/module/focus
   settings and fits the overview; it retains the selected symbol.
   In the overview, use symbol search, **Module dependencies**, pan and zoom to
   inspect the broader graph. Arrows point from caller to dependency; solid edges
   are resolved calls and dashed edges are conservative fallback. The initial zoom
   favors readable nodes; Fit view provides an overview, which can be dense on large
   reports. Nodes can be selected using Enter or Space as well as a pointer.
7. Export the report. The disclosure beside **Export report** reminds you that it
   contains source. If no tests are recommended, **Review changed code** opens Changes;
   an empty list does not establish that omitted tests are safe.

Tests initially retains the analyzer's order and scores. **Search tests** matches test
and file names, ignoring case and surrounding spaces; multiple words must all match.
**Explanation** filters resolved calls, conservative fallback or changed tests.
Category counts describe the full report; the result count shows filtered/total tests.
**Sort tests** offers analysis order, test name, file name or ascending priority;
name/file sorts use deterministic code-point ordering and full-symbol tie breakers.
Row numbers retain the original analysis rank. **Reset tests** restores the full list
and original order. A hidden selection keeps its evidence; **Show selected test**
resets the controls and focuses that row. Controls persist across views and reset
when a new analysis loads. Exports always contain every original recommendation.

Changed code uses lightweight Python syntax coloring over the bounded, escaped
preview; malformed source stays visible. It does not execute or parse source in the
browser. The current theme is light with local system fonts; there is no theme
switcher or saved report history.

To inspect a deleted function and a mixed path, choose **New analysis → Analyze snapshots** to upload
[`tests/fixtures/mixed-revisions.json`](../tests/fixtures/mixed-revisions.json). Select
**Tests → test_g → Open changed code**. The before panel shows `a.py::f`; the after
panel identifies the present but empty file. The explanation says **Mixed revisions**:
`test_g → g` exists only after, while `g → f` exists only before. Neither revision
contains that entire shown path. This is a conservative estimate, not an executable
call sequence from one revision. **New analysis → Load demo** restores the original example.

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

1. Open **New analysis** if a report is loaded. Paste an exact `https://github.com/owner/repo/pull/number` URL into **Analyze a
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

