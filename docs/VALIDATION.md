# Validation record

## Original setup record

Verified locally on November 5, 2026, on macOS with Python 3.12.0 and Node 24.2.0.
This describes the starter delivered during setup, not future feature completion.

| Check | Observed result |
| --- | --- |
| Python tests | 33 passed |
| Python statement coverage | 92% overall; analyzer 100% of statements |
| Ruff lint and formatting | Passed |
| Strict mypy for source package | Passed |
| TypeScript check and Vite production build | Passed |
| Frontend Prettier format check | Passed |
| Playwright desktop/mobile browser cases | 6 passed |
| Python installed-dependency consistency | No broken requirements |
| npm installation audit | 0 reported vulnerabilities at install time |
| GitHub repository | danielpan01/codeimpact exists, private, owned by user |
| GitHub connector access | Read access to new private repo verified |
| Project Git history | No project commits, no staged files, no pushes by setup |
| Cloud chat | Created in CodeImpact; context response verified |
| Hosted CI / deployed app | Not run / not deployed |

Coverage measures executed statements, not correctness or accuracy. CLI tests use
subprocesses, whose executed lines are not fully included in the parent coverage
report. No real-repository precision, recall or latency benchmark is claimed.

Backend cases cover the relevant/unaffected demo tests, evidence paths, comments and
whitespace, deletion, removal of tests, rename semantics, aliases, relative imports,
src layout, package initialization, shadowing, cycles, syntax errors, module fallback,
nested/async/class symbols, duplicates, changed tests, dynamic/wildcard warnings,
non-execution of source, unsafe paths, request bounds and an actual temporary Git
history with diverged base/head branches. The CLI leaves its checkout untouched.

Browser cases cover real API-fed graph content, filtering to an unaffected test,
snapshot upload, empty state, invalid JSON, recovery and report download, at desktop
and Pixel 7 emulated dimensions. This is Chromium viewport testing, not testing on a
physical phone or Safari. Desktop/mobile screenshots are in docs/media/.

One upstream warning remains: the installed Starlette TestClient deprecates its
httpx integration in favor of httpx2. It does not fail tests; address this when
updating the HTTP test stack. The app itself does not need an HTTP client yet.

The macOS restricted environment initially prevented the browser from launching.
Authorized browser tests then exposed a rendering stall in the small headless-shell
binary. The checked-in configuration uses full Chromium headless with GPU disabled;
all six cases pass with that configuration. An empty-label test selector was corrected
to account for its subtitle. Export blob URLs are released after a short delay.

The first demo returns these priority/evidence results:

```text
82  test_discount → discount
72  test_checkout → checkout → discount
62  test_create_order → create_order → checkout → discount
```

The health test is unaffected in the static graph. These are heuristic priorities,
not probabilities that the tests fail. Timing varies per run and machine.

Reproduce with `make check`, then `cd web && npm run test:e2e`.

## Empty-module change detection milestone — November 5, 2026

Verified on this Mac in `/Users/danny/Documents/ChatGPT/CodeImpact` using Python
3.12.0, Node 24.2.0 and npm 11.3.0. This section records new observations separately
from the original setup above.

The attached Codex project folder was initially empty. The existing clean checkout
was found at the original location in PROJECT_CONTEXT.md and copied, including its
Git history, into the attached folder. The original checkout remains unchanged.
Codex then reported the local project as a Git repository. Branch `main`, commit
`0d5c06fbf7f168bac27eada6f4d2f56a67414c7f`, and the expected `origin` were verified;
`git ls-remote origin` returned that same commit for remote `main`. The GitHub
connector confirmed the existing repository is private and owned by danielpan01.
No project staging, commits, pushes, identity changes, PRs or deployment were done.

Dependencies were installed from `requirements-dev.lock` and `web/package-lock.json`
using the setup commands in the Makefile, with an explicit Python 3.12 environment:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pip install --no-deps -e .
cd web
npm ci --cache /private/tmp/codeimpact-npm-cache
npm run install:browsers
```

The initial plain `cd web && npm ci` failed with `EPERM`, syscall `open`, at
`/Users/danny/.npm/_cacache/tmp/6a749641`. The temporary-cache command above succeeded
without changing shared cache permissions or dependency pins. pip also reported its
shared cache was not writable, disabled that cache, and completed installation.

### Regression-first results

Before changing `src/codeimpact/analyzer.py`, ran:

```sh
.venv/bin/pytest tests/test_empty_modules.py -v --no-cov
```

Observed **3 failed, 8 passed**. The failing parameter cases in
`test_module_change_detection` were `empty-to-comment`,
`comment-and-whitespace-edits`, and `comment-line-movement`. Each incorrectly reported
`a.py::<module>` as changed. The executable-change, parse-transition, distinct/identical
invalid-source and removed-test controls passed before the correction.

The correction assigns an AST fingerprint on successful parsing, even with an empty
body, and uses a raw-source fingerprint only in the parse-failure branch. The same
focused command then reported **11 passed**.

The ten comparison cases include unchanged importing tests and an independent module
with its own test. They cover all eight requested scenarios, plus empty-to-invalid,
invalid-to-comment-only and line-movement boundaries. An additional case verifies
removed importing tests remain in the union graph but are never recommended.
Every recommendation in these cases is checked for a path beginning at the test,
ending at a changed symbol, and following valid consecutive returned graph edges.
Module/import fallback reasons and unaffected controls are asserted. Snapshot source
is supplied as strings, never imported or executed.

### Full validation

| Command / check | Observed result |
| --- | --- |
| `make check` | Passed: Ruff lint/format, strict mypy, 44 Python tests, TypeScript check and Vite production build |
| Coverage from `make check` | 92% statement coverage overall (339 statements, 27 missed); analyzer 100% (172 statements, 0 missed) |
| `.venv/bin/python -m pip check` | No broken requirements found |
| `cd web && npm run format:check` | Passed |
| npm installation audit | 0 vulnerabilities reported at installation time |
| Existing Playwright desktop/mobile cases, with temporary ports | 6 passed against this updated checkout |
| `git diff --check` | Passed |
| Project staging | No staged changes; task edits remain uncommitted |
| Hosted GitHub CI / deployment | Not run / not deployed |

The first `cd web && npm run test:e2e` exited 1: all six cases failed to launch
Chromium with `browserType.launch: Target page, context or browser has been closed`,
`signal=SIGABRT`, and `Error: kill EPERM` in the restricted environment. That run is
not counted as a pass. The original checkout's existing servers also occupied ports
8000 and 5173, so a temporary configuration was used to verify the updated checkout
on ports 8001 and 5174 with server reuse disabled. With authorized browser execution,
this command passed all six cases:

```sh
cd web
npm run test:e2e -- --config /private/tmp/codeimpact-validation-bdgciiku/playwright.config.ts
```

That temporary configuration imports the checked-in Playwright configuration and
retains its test cases, desktop/mobile projects and browser launch settings. It only
changes the test/output locations and server URLs/commands; a temporary Vite runner
points the API proxy at port 8001. No dashboard source or checked-in test configuration
was changed. Temporary test servers stopped after the run. The original servers were
left running; stop the original dev terminal before using the normal `make dev` or
browser-test commands against this checkout. Temporary configuration paths are local
validation artifacts, not dependencies required by the project.

The passing Python run still emits the existing Starlette/httpx deprecation warning.
The browser run also logged `ResizeObserver loop completed with undelivered
notifications` once; the six assertions passed, but the console error remains an
observed dashboard limitation outside this analyzer milestone. Node emitted a color
environment warning (`NO_COLOR` ignored because `FORCE_COLOR` is set).

Coverage is executed-statement coverage, not accuracy. No precision, recall,
performance benchmark, hosted CI result, model setting or cross-device sync result
is claimed. Static-analysis limitations and the full-suite merge gate remain as
documented in ARCHITECTURE.md.

## Public GitHub PR analysis milestone — November 8, 2026

Implemented and verified in `/Users/danny/Documents/ChatGPT/CodeImpact` on macOS,
Python 3.12.0, Node 24.2.0, npm 11.3.0. Starting branch was `main`, commit
`34eb6b05d193468df3903f8cccaf056ec688b8f5` (`Harden empty-module change detection`),
with a clean working tree and origin `https://github.com/danielpan01/codeimpact.git`.
The analyzer and its 11 empty-module regression cases were left unchanged. Existing
dependency lockfiles were retained; already-pinned httpx 0.28.1 is now declared as a
runtime dependency. No downloaded repository code was executed or installed.

### Automated results

| Command | Observed result |
| --- | --- |
| `.venv/bin/pytest tests/test_github.py --no-cov` | 63 passed |
| `make check` | Passed: Ruff lint/format, strict mypy, 107 Python tests, TypeScript check and Vite build |
| Coverage measured by `make check` | 94% overall (600 statements, 39 missed); importer 95% (214 statements, 10 missed); analyzer 100% (172 statements, none missed) |
| `.venv/bin/python -m pip check` | No broken requirements found; pip disabled its unwritable shared cache |
| `cd web && npm run format:check` | Passed |
| `cd web && npm run test:e2e` with authorized Chromium execution | 12 passed: six scenarios each on desktop and Pixel 7 emulation |
| `git diff --check` | Passed |
| Hosted GitHub CI / deployment | Not run / not deployed |

The first sandboxed `cd web && npm run test:e2e` exited 1 with all 12 cases unable
to launch Chromium: `browserType.launch: Target page, context or browser has been
closed`, `signal=SIGABRT`, and `Error: kill EPERM`. No page assertions ran in that
attempt. Running the same command with authorized browser execution passed all 12;
the final run after remaining changes also passed all 12. No assertions were removed
or weakened. The checked-in configuration now starts isolated test servers on
8002/5174 with reuse disabled, so it cannot silently validate an old dev server.

HTTP contract cases cover normal and fork PRs, merge-base scope, unchanged callers
and an unaffected control, deleted symbols/tests, rename-as-remove/add, comment-only
empty modules, branch movement after metadata retrieval, response identity checks,
URL rejection before network access, private/unavailable/404 repositories, redirects,
rate limits, upstream failures, timeouts, invalid encoding/content integrity, unsafe
paths, incomplete trees, source/tree/response/request budgets, skip warnings and an
empty Python scope. Download tests exercise four-way concurrency and cancellation
with no surviving tasks after failure. Fake optional credentials are asserted to
stay in server request headers and out of responses/logs. A source-file sentinel
test proves that fetched source is not executed. Real route reports match direct
analysis of the same complete snapshot pairs, excluding variable analysis timings.

The browser test server overrides only the GitHub HTTP transport, using a fresh
deterministic fixture per import; the actual importer, analyzer and API serialization
run. Browser cases verify keyboard PR submission, full SHA metadata, valid exported
evidence paths, an unaffected test, loading/disabled controls, clearing stale results,
rate-limit retry, correcting an invalid URL, and switching back to the demo. Existing
demo, snapshot upload/error recovery and export cases remain. Mobile checks assert no
horizontal page overflow. Success/error screenshots are generated under ignored
`web/test-results/`; desktop and mobile success images were visually inspected.
These are Chromium viewport tests, not physical-device or Safari validation.

The existing Starlette/httpx TestClient deprecation warning remains. Node logs that
`NO_COLOR` is ignored when `FORCE_COLOR` is set. An earlier successful browser run
logged React Flow's parent-size warning twice during report transitions; the final
passing run did not reproduce it. No claim of a fully warning-free browser is made.
Coverage is executed-statement coverage, not accuracy or safe test-skipping evidence.

### Live public PR smoke test

Anonymous GitHub access succeeded for
[pallets/markupsafe PR #469, “fix exact str check”](https://github.com/pallets/markupsafe/pull/469).
The real dev API, reached through Vite at `POST http://127.0.0.1:5173/api/github/pr`,
returned HTTP 200. No mocked provider was used in this smoke test.

| Recorded provenance / result | Observed value |
| --- | --- |
| Target base SHA | `b5291646cbabf945069db07c34b08fb1f623134d` |
| Merge-base SHA (analyzed before) | `b5291646cbabf945069db07c34b08fb1f623134d` |
| Head SHA (analyzed after) | `7add29c77b088299841e1017a7cd2f96133a6659` |
| Base and head repository | `pallets/markupsafe` |
| Analyzer version | `0.1.0` |
| Python files | 11 before, 11 after |
| Graph | 119 nodes, 164 edges |
| Changed | `src/markupsafe/__init__.py::escape` and its module node |
| Recommendations | 23: seven resolved-call paths, 16 conservative module/import paths |
| Warnings | 349, including dynamic/unresolved calls; retained in the report |
| Measured second import | 18 GitHub requests, 127,548 decoded response bytes |

A second live import produced the same source metadata. Its validated snapshots
were submitted to the existing `POST /api/analyze` route. All stable report fields
matched the PR response, with ingestion warnings combined and timing/provenance
excluded from the comparison. All 23 recommendations began at their test, ended at
a changed node and followed existing consecutive graph edges; none was a removed
test. For example, `tests/test_escape.py::test_escape` directly reaches the changed
`escape` function. These observations verify ingestion and contract parity, not that
all 23 tests would fail or that all affected tests were discovered. No source tests
from MarkupSafe were run.

Local ignored artifacts: `reports/github-smoke-report.json` and
`reports/github-smoke-snapshots.json`. The latter can be uploaded with **Analyze
snapshots** to reproduce the stored input without GitHub access. It is input data;
the report itself is not snapshot-upload input. To repeat the live request:

```sh
# Use this port override on this Mac because an unrelated app occupies 8000.
CODEIMPACT_API_PORT=8001 make dev
# In another terminal at the repository root:
curl --fail-with-body http://127.0.0.1:5173/api/github/pr \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://github.com/pallets/markupsafe/pull/469"}'
```

A later live request may see different metadata or GitHub rate limits; inspect its
returned SHAs. The previous CodeImpact dev pair was stopped and the updated app was
started on 8001/5173. The unrelated service on 8000 was left alone.

### Remaining limits and ownership

Public repositories only; complete regular Python files within documented bounds
and exclusions only. Large/truncated listings and unsupported encodings fail rather
than return partial analysis. Anonymous quotas may prevent otherwise valid imports.
Per-import network limits do not provide global request quotas, parser process
isolation or a hard analysis CPU deadline. Private auth, background jobs, durable
storage, cross-request caching and deployment remain future milestones. Existing
static-analysis blind spots and the full-test-suite merge gate still apply.

All task edits remain local, unstaged and uncommitted. No Git identity, visibility,
project history or remote content was changed. No hosted CI result, accuracy metric,
performance benchmark, active model setting or Mac/cloud synchronization is claimed.

## Inspectable changes and revision-aware evidence — November 10, 2026

Observed in `/Users/danny/Documents/ChatGPT/CodeImpact`, starting from clean `main`
at `2604fd74a372b30fe13812ccc1ec8b01c16c7ba7`, with origin
`https://github.com/danielpan01/codeimpact.git`. Existing Python 3.12.0 / Node 24.2.0
dependencies from the pinned lockfiles were reused; no dependency versions changed.
No analyzed source was executed, imported, installed or checked out.

### Regression-first observations

Before implementing the report/analyzer changes, ran:

```sh
.venv/bin/pytest tests/test_revision_evidence.py --no-cov
```

**16 failed** on missing schema-2.0 fields (`changes`, `source_files`, revision
evidence and typed recommendation paths). After implementation, those 16 plus the
existing analyzer/empty-module cases reported **47 passed**. The first complete
Python run then reported **123 passed**.

Review added four more focused cases. Before the corresponding line-range fixes,
the focused file reported **2 failed, 18 passed**: a parenthesized multiline decorator
started at line 2 instead of its `@` at line 1, and a Unicode separator inside a
string inflated the module's physical line count (4 instead of 3). After correcting
decorator prefix detection and universal-newline handling, **20 passed**.

The original four new browser scenarios were also added before the UI implementation:

```sh
cd web
npm run test:e2e -- tests/changes.spec.ts --workers=2
```

The first sandboxed attempt had **8 browser-launch failures** (`SIGABRT`, `kill EPERM`);
no page assertions ran. The same command with authorized Chromium execution reached
the app and had **8 expected failures**: missing Open changed code/Changes controls
and missing mixed-revision labels. After the UI implementation, the full then-current
suite reported **20 passed**. Additional assertions and one further scenario per
viewport expanded the final run to 22 cases; no assertions were removed or weakened.

### Final observed results

| Command / check | Observed result |
| --- | --- |
| `.venv/bin/pytest tests/test_revision_evidence.py --no-cov --tb=short` | 20 passed |
| `make check` | Passed: Ruff lint/format, strict mypy, 127 Python tests, TypeScript check and Vite production build |
| Statement coverage from `make check` | 94% overall (673 statements, 40 missed); analyzer 99% (214 statements, 1 missed) |
| `cd web && npm run format:check` | Passed |
| `cd web && npm run test:e2e` with authorized Chromium execution | 22 passed: 11 scenarios each on desktop and Pixel 7 emulation |
| `.venv/bin/python -m pip check` | No broken requirements; shared unwritable pip cache disabled |
| `git diff --check` | Passed |
| Existing dev website proxy at `127.0.0.1:5173` | Demo and mixed fixture returned schema 2.0; before/after source, unchanged demo scores and mixed path verified |
| Staging / commits / pushes / deployment | None by the agent; all changes left unstaged and uncommitted |
| Hosted CI / new live GitHub smoke / accuracy benchmark | Not run for this milestone |

The 20 focused backend cases cover modified/added/removed/renamed symbols, decorators
(including a multiline parenthesized decorator), nested definitions, line movement,
physical newlines, empty/comment-only modules, valid/invalid transitions, absent
files, before-only/after-only/shared evidence, retained repeated call/import locations,
mixed paths, conservative fallback, unaffected controls, removed-test exclusion,
stable edge IDs, deterministic ordering, cycles and source non-execution. The mixed
case reads the checked-in `tests/fixtures/mixed-revisions.json` as data. Typed-path
invariants check start test, changed endpoint, exact edge IDs/kinds/direction, distance,
revision intersection and removed-test exclusion. Existing API/CLI/GitHub tests now
also assert the 2.0 serialization and exact snapshot source. Demo priorities remain
82, 72, 62. GitHub source/network limits and immutable retrieval are unchanged.

Browser cases verify recommendation-to-code navigation, retained explanations,
file-grouped statuses, before/after line numbers, decorators, deleted-file source,
empty-file display, parse-failure raw text, mixed/shared/before/after labels, typed
export paths, source-inclusive export, truncation, HTML-like text without execution,
keyboard activation/tab order/focus, conservative module/import evidence, comment-only
controls and old-report-version recovery. The original demo, upload/error recovery,
public-PR loading/retry/error and provenance/export cases still pass. Public-PR cases
use the real importer/analyzer/API with a deterministic mocked GitHub HTTP transport;
they now also open the changed code and check its exact before/after content. No new
live GitHub result is implied by these tests. The November 8 live record is historical.

Desktop and mobile screenshots in ignored `web/test-results/` were visually inspected.
Desktop panes sit side by side; mobile stacks them above the retained explanation.
Browser assertions confirm no horizontal page overflow. These are Chromium viewport
tests, not physical-device/Safari tests. The existing Starlette/httpx deprecation and
Node color-environment warnings remain. An intermediate passing run logged React
Flow's parent-size warning twice during report transitions; the final 22-case run did
not reproduce it. Coverage measures statement execution, not analysis accuracy.

The already-running local API was still serving schema 1.0. After checking its
command and working directory, only that CodeImpact API process was restarted on
8001; the existing frontend on 5173 stayed running. Requests through that frontend's
proxy verified the demo and mixed fixture with the new schema. This is local
development, not a deployed website.

### Remaining limits and manual review

Static resolution limitations and the full-suite merge gate remain. Renames are
remove+add; modules aggregate nested changes; parse failures can make definitions
unavailable. A mixed label describes the shown path, not a claim that no alternative
single-revision path exists. Preview limits are 120 lines, 12,000 UTF-16 code units
and 500 code units per line; a long module may hide a changed statement beyond the
preview. Select its individual definition or export the complete source. Source is
stored once per changed file per revision; exports contain full source, including
content beyond the preview. Schema 1.0 consumers must upgrade and re-analyze their
snapshots. No inline line-diff, automatic rename matching, persistence or additional
infrastructure was added.

Manual clicks at `http://127.0.0.1:5173`:

1. Refresh, click **Load demo → Tests → test_create_order → Open changed code**.
   Inspect `discount` changing from `0.10` to `0.15`, line numbers, retained test path,
   and **Path exists in both revisions**. Expand a hop's Before/After evidence.
2. In **Changes**, select the `shop/pricing.py` module row, then `discount`. Switch
   to **Map** and **Tests** to verify both existing views remain.
3. Click **Analyze snapshots**, choose `tests/fixtures/mixed-revisions.json`, then
   **Tests → test_g → Open changed code**. Inspect removed `f`, the empty after file,
   **Mixed revisions**, and the after-only then before-only call hops.
4. Click **Export report**. Inspect `schema_version: "2.0"`, `source_files`, `changes`,
   revision evidence arrays and recommendation `evidence_edges` in the JSON.
5. To exercise real GitHub yourself, submit a public Python PR URL, expand **Exact
   analyzed revisions**, then use **Tests → Open changed code**. Anonymous rate
   limits and later PR revisions may change that result. Load demo remains available.

## Complete pre-push verification — November 10, 2026

This follow-up verifies the final local milestone after the owner's request to run
all tests and prepare push/merge instructions. Local `main` remains at `2604fd7`.
Read-only `git ls-remote --heads origin main codex/inspectable-changes` returned
remote `main` at the same full SHA, with no existing branch of the proposed name.
No staging, branch creation, commit, push, PR creation or merge was performed.

### Final suite and additional regression

The initial recheck passed all 127 application tests, all 8 maintenance-script tests
and the then-current 22 desktop/mobile cases. A further boundary test found that the
preview budget did not include rendered newlines: the fixture displayed 12,024 source
characters against the advertised 12,000 limit. Both desktop and mobile cases failed
before the correction. The preview now reserves one code unit per rendered newline.
The focused command reported **2 passed** after the fix, and the full final browser
suite reported **24 passed**. The regression also verifies complete exported source
and that opening a preview/export causes no additional API requests.

| Final command / check | Observed result |
| --- | --- |
| `make check` | Passed: 127 application tests, Ruff lint/format, strict mypy, TypeScript and Vite build |
| `.venv/bin/python -m unittest discover -s scripts -p 'test_*.py' -v` | 8 maintenance tests passed |
| `cd web && npm run format:check` | Passed |
| `cd web && npm run test:e2e` with authorized Chromium launch | 24 passed, 12 scenarios on each viewport |
| `.venv/bin/python -m pip check` | No broken requirements |
| `git diff --check` | Passed |
| `git diff --cached --stat` | Empty; changes remain unstaged |
| Hosted CI for these edits | Pending the owner's push; no hosted result claimed |

The existing Starlette/httpx and Node color-environment warnings remain non-failing.
Coverage remains 94% overall (673 statements, 40 missed), analyzer 99% (214 statements,
1 missed); these are statement-execution figures, not accuracy. Dependency pins were
unchanged. Maintenance fixtures use temporary files and mocked network responses.

### Actual running website and live GitHub verification

The owner's in-app browser initially retained the older interface. Refreshing did
not reveal Changes because the long-running Vite process was serving older compiled
modules. Its command and working directory were checked, then that frontend was
restarted. The browser visibly showed Changes and Open changed code afterwards.
The frontend was refreshed again after the final preview fix. The API remains on
8001 and the frontend/proxy on 5173. Restart both when verifying later code changes
if hot reload does not reflect them; isolated browser tests already start fresh servers.

Using the actual in-app browser and ordinary dev API (no GitHub transport override),
submitted `https://github.com/pallets/markupsafe/pull/469`, expanded the exact revisions,
opened changed code from `test_escape`, and downloaded the report using Export report.

| Live observation | Result |
| --- | --- |
| Target base / analyzed merge base | `b5291646cbabf945069db07c34b08fb1f623134d` |
| Analyzed head | `7add29c77b088299841e1017a7cd2f96133a6659` |
| Report schema | `2.0` |
| Python files | 11 before and 11 after |
| Graph | 119 nodes, 164 edges; all 164 shared across revisions |
| Changes | `src/markupsafe/__init__.py::<module>` and `::escape` |
| Source preview | Before lines 24–43 uses `s.__class__ is str`; after lines 24–45 uses `type(s) is str` |
| Recommendations | 23: 7 resolved-call paths, 16 conservative module/import paths |
| Path revisions | All 23 shown paths exist in both revisions |
| Warnings | 349, retained and visible |
| Export validation | All edge IDs unique; revision labels match evidence presence; source/target locations valid; all 23 typed paths begin at their test and end at a changed node, with matching direction, distance and revision intersection; no removed tests recommended |

The actual export was saved in the user's Downloads folder by the browser. An ignored
copy is at `reports/revision-review-live.json`; it contains public source and is not
part of the proposed commit. The source text and changed symbol ranges were checked
in that downloaded JSON, not inferred from the earlier milestone's smoke test. No
MarkupSafe source or tests were executed, imported or installed. Browser inspection
and export completed on the live PR analysis. The screenshot `/private/tmp/codeimpact-live-pr-review.jpg`
records its code view and is a local verification artifact.

### Owner handoff

README's **Review, commit and push** section now includes the exact changed-file
staging list, a feature-branch/rebase/push sequence, a ready-to-paste PR title/body,
and GitHub review/merge steps. The owner should wait for **Quality checks / check**
on the latest PR commit, inspect Files changed, and resolve any conflicts before
merging. The local validation is complete; approval, authoring commits, publishing
the branch and merging remain the owner's actions.

## Bounded analyzer correctness corpus — November 10, 2026

This is a separate milestone from the changed-code dashboard work above. The
active local checkout was `/Users/danny/Documents/ChatGPT/CodeImpact`, initially
clean on `main` at `546ee8e295c513d3137c4446c7ddde0b63e3075a`, with origin
`https://github.com/danielpan01/codeimpact.git`. The prior milestone was already
present in that commit. No existing uncommitted work needed preservation. Work was
performed on the Mac checkout, not in a cloud environment; no cross-environment
sync or downloadable cloud patch is claimed.

### Implemented scope

- 25 small, complete JSON base/head snapshot cases in `corpus/cases`, with authored
  affected/unaffected labels and rationales, explicit unclassified tests, feature
  tags, categories and exact explained known discrepancies.
- `src/codeimpact/corpus.py`: bounded data-only loading, duplicate JSON/case-ID
  checks, snapshot validation and independent AST test-discovery/label validation.
- `src/codeimpact/evaluate.py`: deterministic readable/JSON evaluation schema 1.0,
  per-case and aggregate metrics, separate supported/known-limitation groups,
  null zero-denominator ratios, exact discrepancy drift failures and validation of
  every recommendation's typed path and revision evidence.
- `tests/test_corpus.py` and `tests/test_evaluation.py`: positive and malformed-input
  controls, all-case baseline checks, intentional report corruption, exact-drift
  checks in both directions, no-execution sentinel, CLI failures and deterministic
  reports. Evidence examples also require reviewed explanations when resolution
  changes without changing the selected test set.
- `make evaluate`, a corpus guide, updated architecture/roadmap/context and an
  owner-only review/commit/push/merge handoff in README.

Labels were authored from source relationships before running the evaluator. A
one-off authoring helper wrote literal strings and labels without importing the
analyzer; all stored cases contain complete snapshots, not patches. They are
authored expectations, not external ground truth or independently reviewed labels.
No fixture source or fixture test was executed/imported/installed/checked out.
There are no skips or xfails for difficult cases. No analyzer bug blocked this
evaluation, so `analyzer.py`, existing analysis models, API/CLI and dashboard were
left unchanged. Scoring, IDs, graph direction/union, deletion handling, limits,
cycle traversal and the empty-module fix retain their existing regression tests.

The initial focused run, before implementing the new modules, failed collection
with two `ModuleNotFoundError: No module named 'codeimpact.corpus'` errors. This was
the expected missing implementation for the new tests, not a pre-existing analyzer
failure. After implementation and additional failure-mode checks, all 81 focused
tests passed. The independently authored fixture labels needed no changes to agree
with the deliberately recorded discrepancy baseline.

### Observed evaluation

| Population | Cases | TP | FN | FP | TN | Selected unclassified | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| All cases | 25 | 22 | 3 | 6 | 26 | 2 | 22/28 (78.6%) | 22/25 (88.0%) |
| Supported demonstrations | 14 | 15 | 0 | 0 | 15 | 0 | 15/15 (100%) | 15/15 (100%) |
| Known limitations | 11 | 7 | 3 | 6 | 11 | 2 | 7/13 (53.8%) | 7/10 (70.0%) |

There are 57 labeled case/test pairs, plus two unclassified pairs. All 30 returned
recommendations pass the typed-path/revision checks; two are unclassified, leaving
28 labeled recommendations for the precision denominator. All 25 cases match their
explicit baseline. This is not a claim that the 6 FPs or 3 FNs were fixed.

Observed false positives: unchanged sibling module function (1), shadowed
parameter/local callable (2), stale imported alias after module rebinding (1),
conditional-definition module fallback (1), and independent inherited method (1).
The module-rebinding false positive has a resolved-call explanation; that static
resolution is still semantically wrong for the reassigned name.

Observed misses: function-local import (1), pytest fixture injection (1), and
runtime import/reflective call (1). Re-export fallback selects the affected test
without a precise call edge, so its limitation has no selection error. Unclassified
selections are the invalid-to-invalid syntax case and the mixed-revision path case;
their explicit rationales remain in the case files and outside precision/recall.
All difficult cases and their labeled controls are included in overall totals.

### Commands and actual results

| Command / check | Observed result |
| --- | --- |
| `.venv/bin/pytest tests/test_corpus.py tests/test_evaluation.py --no-cov --tb=short` | 81 passed |
| `make evaluate` | Exit 0; all 25 cases matched the exact baseline; readable summary and JSON produced |
| `.venv/bin/python -m codeimpact.evaluate --corpus corpus/cases --output reports/corpus-repeat.json > reports/corpus-repeat.txt` | Exit 0; second independent CLI run |
| `cmp reports/corpus-evaluation.json reports/corpus-repeat.json` | Exit 0; byte-identical reports |
| `make check` | Passed: 208 application tests, Ruff lint/format, strict mypy for 9 source files, TypeScript and Vite build |
| `.venv/bin/python -m unittest discover -s scripts -p 'test_*.py' -v` | 8 maintenance tests passed |
| `git diff --check` | Passed |
| Frontend formatting and desktop/mobile browser tests | Not rerun: no dashboard files or behavior changed; the previous milestone's 24-case run is historical, not a new result |
| Hosted CI, human review and remote publishing | Not performed for these uncommitted changes |

Used the existing `.venv` and installed pinned dependencies; no dependency or lockfile
changes. The one existing Starlette/httpx deprecation warning remains non-failing.
Statement coverage: 91% overall (972 statements, 83 missed); analyzer 99% (214
statements, 1 missed). CLI subprocess checks run successfully but are not counted
in this in-process coverage report. Coverage measures executed lines, not correctness.
Passing regressions do not establish general analyzer accuracy; tiny authored
fixtures do not represent every repository. Dependency relevance is different from
whether a test actually fails, and the full suite remains the merge gate.

The ignored full JSON report is 493,947 bytes. Its SHA-256 is
`ff6d0154ad216dd50ca988bec37a4d6a1b2f050341acd1d18bb369b6854d21fc`.
Its canonical corpus digest is
`8d081ec3364683fb4a9e5a5e379427c61f8299c80ec628e274938d3802695d03`.
The report omits elapsed timing and includes complete fixture inputs, labels,
annotations and analyzer evidence. The digest identifies corpus data, not analyzer
code; retain the checkout version and pinned environment when reproducing it.
No performance benchmark was added. Repeated runs and reordered case/snapshot
inputs are also covered by automated checks.

### Handoff and remaining work

All milestone changes remain unstaged/uncommitted. The owner reviews the files and
report, creates `codex/analyzer-corpus`, stages the explicit README file list,
commits, rebases on current `origin/main`, rechecks, pushes and opens/merges the PR.
No agent stage, commit, push, identity change, PR, deployment or repository-visibility
change occurred. README provides exact commands and a proposed PR description.

[CORPUS.md](CORPUS.md) contains the full schema, case inventory, adding/reviewing
workflow and an interview walkthrough: transitive call → module false positive →
local-import miss. The next bounded development step is function-local import
resolution with alias/scope/shadowing regressions. Preserve authored labels and
deliberately update the recorded miss only after that separate fix is verified.
Other known limitations remain visible rather than being bundled into this milestone.

## Bounded function-local import resolution — November 10, 2026

This section records the initial implementation checks. The pre-commit verification
below supersedes its test counts and adds desktop/mobile coverage.

Started from clean local `main` at merged corpus commit
`4b50d9fd58d28809def15e753032595a66ba76ea` in
`/Users/danny/Documents/ChatGPT/CodeImpact`. Origin remained
`https://github.com/danielpan01/codeimpact.git`. Read AGENTS.md, README, architecture,
the actual analyzer, existing regression tests, and the corpus before editing.
All work below is local and unstaged/uncommitted. No branch, stage, commit, push,
identity change or PR was performed by the agent.

### Regression-first evidence

Added `tests/test_local_imports.py` before changing `analyzer.py`. The initial
58 checks reported **40 failed, 18 passed** with:

```sh
.venv/bin/pytest tests/test_local_imports.py --no-cov --tb=no -rN
```

Failures demonstrated the existing missed local import, unresolved module/function
aliases and relative/src imports, and incorrect fallback to a same-named module
alias before or instead of a local binding. Additional controls covered separate
functions, nested/async method scopes, shadowing, assignments/deletions, repeated
imports, exception/pattern captures, conditional imports, nonlocal mutation,
same-line ordering, wildcard/overdeep relative imports, scoped module fallback,
deletion/revision evidence, and a source-as-data sentinel. Source strings in those
checks were never executed or imported. Some negative controls are intentionally
parseable AST input whose full Python runtime validity is not asserted.

After implementation, those checks passed. A further local-import cycle regression
brings the file to **59 passing tests** and verifies finite deterministic evidence
paths. Existing analyzer, revision-evidence, corpus and evaluator tests remain
active; no skips or xfails were added.

The first full evaluation after the code fix, before annotation updates, exited
**1** with exactly this expected baseline drift:

```text
local_import: false negatives: expected ['tests/test_worker.py::test_read'], observed []
```

After inspecting that improvement, only `local_import` metadata changed: category
to `supported`, updated description/features, empty known-FN map and empty
limitation notes. Its complete snapshots and all authored label maps/rationales
were preserved. The evaluator guard test now uses the still-missed pytest fixture
case for unexpected misses and deliberately reinstates the old local-import FN
to verify that stale expectations still fail on an improvement.

### Implementation and preserved contracts

- Shared import-syntax decoding supports module/function aliases, relative package
  imports and `src/` layouts without importing source.
- Each function/async function gets its own local import bindings; separately
  indexed nested functions and methods can resolve their own imports. Calls must
  follow the import's end line/column, including statements sharing one line.
- Ambiguous or unsupported local import names reserve their scope and cannot
  incorrectly fall through to module-level aliases. Parameters, competing stores,
  deletions, duplicate imports, definitions, exception/pattern captures,
  global/nonlocal declarations and alias mutation conservatively suppress precise
  resolution. Nested assignments do not pollute the outer local alias, while a
  potential nested nonlocal/attribute write invalidates it.
- Direct local imports add conservative function-to-module import edges, using
  that statement's location. Module-constant changes can reach the importing
  function's callers without adding an import edge for unrelated sibling functions.
- Existing edge IDs, caller-to-dependency direction, base/head union, source ranges,
  deleted-test exclusion, cycle traversal, ordering and score formula are retained.
  Analysis/evaluation schemas remain 2.0/1.0; input limits, API, CLI entry point,
  dependency pins and dashboard files are unchanged.

The implementation is intentionally not a control-flow or runtime binding
interpreter. Any competing binding in the function can suppress the alias even
if unreachable or after a call. Imports nested under conditionals/loops/try,
class-body import bindings, closure propagation, and precise local-alias calls in
lambda/comprehension scopes remain unsupported. Rebinding can leave a conservative
import fallback, so lack of a precise call does not imply no recommendation. The
broader module-level rebinding, fixture injection, re-export and dynamic/runtime
dispatch limitations remain. See ARCHITECTURE.md for the exact boundary.

### Measured corpus comparison

The same 25 snapshots and 57 labeled case/test pairs were used before and after.
No new authored cases were added for this milestone. Two additional unclassified
case/test pairs remain separate from label ratios.

| Population | Cases | TP | FN | FP | TN | Selected unclassified | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Original overall | 25 | 22 | 3 | 6 | 26 | 2 | 22/28 (78.6%) | 22/25 (88.0%) |
| Updated overall | 25 | 23 | 2 | 6 | 26 | 2 | 23/29 (79.3%) | 23/25 (92.0%) |
| Updated supported | 15 | 16 | 0 | 0 | 16 | 0 | 16/16 (100%) | 16/16 (100%) |
| Updated known limitations | 10 | 7 | 2 | 6 | 10 | 2 | 7/13 (53.8%) | 7/9 (77.8%) |

`tests/test_worker.py::test_read` now follows the exact resolved path
`test_read → worker.read → core.price`, present in both revisions. Its independent
control remains unselected. All other **24 case reports**, including recommendations,
scores, graph edges, source evidence, warnings and classifications, are identical
to the saved pre-change evaluation (elapsed timing is already omitted). All **31**
current recommendations pass the evaluator's typed-path/revision checks.

These figures measure agreement with authored dependency labels, not production
accuracy or runtime failures. Statement coverage measures executed lines, not
correctness; the complete test suite remains the merge gate.

### Actual checks and artifacts

| Command / check | Observed result |
| --- | --- |
| `.venv/bin/pytest tests/test_local_imports.py tests/test_analyzer.py tests/test_revision_evidence.py tests/test_corpus.py tests/test_evaluation.py --no-cov --tb=short` | 180 passed, including all 59 local-import checks |
| `make check` | Passed: 267 application tests, Ruff lint/format, strict mypy, TypeScript and Vite production build |
| `make evaluate` | Exit 0; all 25 explicit baselines match |
| `.venv/bin/python -m codeimpact.evaluate --output reports/local-import-repeat.json > reports/local-import-repeat.txt` | Exit 0 |
| `cmp reports/corpus-evaluation.json reports/local-import-repeat.json` | Exit 0; byte-identical JSON |
| Snapshot/label comparison to saved pre-change evaluation | All 25 complete inputs and authored affected/unaffected/unclassified maps unchanged |
| Stable comparison of the other 24 case results | Identical |
| `git diff --check` | Passed |
| Dashboard formatting/browser tests | Not rerun; no dashboard behavior or files changed |
| Hosted CI for these edits | Not run; changes remain local and uncommitted |

The existing non-failing Starlette/httpx deprecation warning remains. Coverage was
92% overall (1,059 statements, 86 missed), with analyzer coverage 99% (301
statements, 4 missed). CLI subprocess execution is not included in this in-process
statement coverage. No performance claims or benchmarks were introduced.

Ignored reproducibility artifacts:

- `reports/local-import-milestone-before.json`: original analyzer/corpus evaluation.
- `reports/local-import-before-baseline-update.json`: improved selection with the
  intentionally stale known-miss annotation and its exit-1 discrepancy.
- `reports/corpus-evaluation.json`: final current report.
- `reports/local-import-repeat.json`: independent CLI repeat.

Final corpus digest:
`af41e279db16a3c6baa52dd0ce45d9e12d2e8166d4803bc4f7864aac05da68e8`.
Final JSON report SHA-256:
`610fdc3077e42d1c157ccad1d45ca63cadffc7612b41ce5919642852e38abe4d`.
The corpus digest includes the deliberately updated annotations; it does not
identify the analyzer code. Retain the eventual owner-created commit and pinned
environment when reproducing results.

### Owner handoff

Review `src/codeimpact/analyzer.py`, the new `tests/test_local_imports.py`, the
evaluator guard adjustment and the small metadata-only corpus diff. README,
ARCHITECTURE, CORPUS, BUILD_PLAN, PROJECT_CONTEXT and this record describe the new
boundary and actual results. The owner creates a feature branch, stages reviewed
files, commits, pushes and opens the PR. No publication has been performed here.

A separate next candidate is module-level rebinding: remove stale resolved-call
evidence in `module_rebinding`, then measure any remaining conservative fallback.
That evidence correction need not remove the recorded false positive, so do not
promise improved precision or weaken its unaffected label in advance.

## Pre-commit verification of function-local imports

A follow-up review found one additional defect in the new binding scan: a nested
definition's default value, decorator or class base can rebind the enclosing
function's import alias with an assignment expression. Skipping those headers
incorrectly retained a resolved call to the original imported function.

Added five regression cases for positional defaults, keyword-only defaults,
decorators, class bases and lambda defaults. All **five failed before the fix**
with `pytest -k nested_definition_headers`. The scan now examines definition
headers in the enclosing scope while preserving separate nested body bindings.
All **64 local-import tests** then passed. No regression was skipped or marked
as an expected failure.

Added one browser scenario, run on both desktop and mobile, which uploads the
unchanged `local_import` corpus input through the real API. It verifies the sole
selected test, the resolved three-node evidence path, the function-scoped import
edge, before/after changed-code previews, shared revision evidence and an exported
report identical to the API response. Snapshot Python remains JSON string data.
The dashboard's application code and report schemas are unchanged.

| Command / check | Observed result |
| --- | --- |
| `.venv/bin/pytest tests/test_local_imports.py --no-cov --tb=short` | 64 passed |
| `make check` | Passed: **272 application tests**, Ruff lint/format, strict mypy, TypeScript and Vite production build |
| `.venv/bin/python -m unittest discover -s scripts -p 'test_*.py' -v` | **8 maintenance tests passed** |
| `cd web && npm run format:check` | Passed |
| `cd web && npm run test:e2e` | **26 passed**, including the new upload/evidence/preview/export scenario on desktop and mobile |
| `.venv/bin/python -m pip check` | No broken requirements found |
| `make evaluate` | Exit 0; all 25 explicit baselines match |
| `.venv/bin/python -m codeimpact.evaluate --output reports/local-import-prepush-repeat.json > reports/local-import-prepush-repeat.txt` | Exit 0 |
| `cmp reports/corpus-evaluation.json reports/local-import-prepush-repeat.json` | Exit 0; byte-identical JSON |
| Comparison against `reports/local-import-milestone-before.json` | All 25 snapshots and authored label maps unchanged; the other 24 complete case reports remain identical |
| `git diff --check` | Passed |
| Git index and publication | No staged changes; no commits, pushes or PR created by the agent |
| Hosted CI for these edits | Pending the owner's commit and push |

The first browser attempt failed to launch Chromium under the local sandbox
(`EPERM` / `SIGABRT`), before browser assertions could execute. The existing
24-test suite passed with the required browser-launch permission; after adding
the new scenario, the full 26-test suite passed with the same permission. This
was an execution-environment restriction, not a failing application assertion.

The existing Starlette/httpx deprecation warning and browser environment warnings
were non-failing. Current application coverage is **92%** (1,069 statements,
86 missed); analyzer coverage is **99%** (311 statements, 4 missed). Coverage does
not establish correctness or production accuracy.

The corpus results and digests above remain unchanged after the header fix:
**23 TP, 2 FN, 6 FP, 26 TN**, plus two unclassified recommendations. All 31
recommendations pass the evaluator's evidence-path checks. Fixture injection and
runtime imports remain the two measured misses; the recorded conservative false
positives also remain outside this milestone. These are explicit analyzer limits,
not failing regression tests. The complete test suite remains the merge gate.

The milestone is ready for owner review and commit based on these local checks.
Review the added browser test along with the analyzer, regressions and documentation.
All requested changes remain unstaged and uncommitted.

