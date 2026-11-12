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

## Bounded module-level rebinding — November 11, 2026

Started in `/Users/danny/Documents/ChatGPT/CodeImpact` on clean branch
`codex/module-level-rebinding` at `68ae852fdc47a76da960c59caba03afb90252907`,
the owner's merged function-local import milestone. Origin remained
`https://github.com/danielpan01/codeimpact.git`. Read AGENTS.md, README,
ARCHITECTURE, CORPUS, this validation history, the analyzer/models/evaluator,
existing regressions and `module_rebinding.json` before editing. No pre-existing
uncommitted work was present. No Git branch, index, commit, remote or identity
mutation was performed by the agent.

### Defect, failing tests and correction

The previous module alias table remembered imports but never invalidated a name
when module code reassigned, deleted or shadowed it. In the corpus example,
`from core import price` followed by `price = lambda: 42` still produced a precise
`worker.read → core.price` edge, despite the replacement binding.

Saved the original 25-case evaluation to `reports/module-rebinding-before.json`
and its console output to `reports/module-rebinding-before.txt`, before edits to
analyzer or corpus annotations. Then added `tests/test_module_rebinding.py` and ran:

```sh
.venv/bin/pytest tests/test_module_rebinding.py --no-cov --tb=short
```

**Before the analyzer change: 59 failed, 28 passed (87 tests).** Failures exposed
stale imported function/module call targets, competing imports/definitions,
module-scope compound bindings, relative/src variants, and incorrect revision
presence for invalidated calls. Passing controls included ordinary imports,
separate scopes, bare annotations and deterministic source-as-data handling.
The original 64 function-local import regressions were not edited.

The correction adds a module-scope binding audit requiring one direct import per
name and no competing binding in that scope. It traverses compound statements but
does not enter separate function/class/lambda bodies. Definition headers and lambda
defaults can bind in the enclosing scope; comprehension iteration targets do not.
Plain/chained/unpacked/annotated/augmented assignments, assignment expressions,
deletions, definition names, loop/with targets, exception names and pattern captures
are accounted for. An annotation without a value does not assign a module name.
Attribute/subscript stores do not rebind their root object name.

Ambiguous imported roots cannot resolve via the stale alias or fall through to a
guessed replacement definition. Their directly relevant diagnostics are visible.
The prior direct import edges remain conservative dependencies. Supported local
imports retain precedence within their own function. No scoring, traversal, model,
schema, stable-ID, source-safety or resource-limit changes were made.

The first corrected run passed **151 tests** (87 new plus 64 function-local).
The broader regression run then reported **271 passed, 1 failed**: the existing
evidence-specific `module_rebinding` assertion deliberately still expected
`Resolved call path`. Inspection confirmed the intended switch to fallback, after
which that expected reason was updated. The case-specific new regression also
asserts the exact fallback path, edge kinds, revision and both resulting scores.
No assertions were skipped or weakened to hide the remaining FP.

### Selection versus evidence measurements

All 25 original snapshots and authored affected/unaffected/unclassified maps and
rationales are unchanged. Every case keeps the same selected test IDs and order,
classifications and metrics. Overall counts remain **TP 23, FN 2, FP 6, TN 26**,
with two selected unclassified pairs. Precision remains **23/29 (79.3%)** and recall
**23/25 (92.0%)**. Categories remain 15 supported and 10 known limitations.

For `module_rebinding`, before and after selection is exactly:

- `tests/test_price.py::test_price` — TP.
- `tests/test_worker.py::test_read` — FP.

The independent `tests/test_control.py::test_control` remains unselected (TN).
Thus the case remains TP 1, FN 0, FP 1, TN 1.

| Evidence | Before | After |
| --- | --- | --- |
| `worker.py::read → core.py::price` call | Present in both revisions | Removed in both revisions |
| Wrapper recommendation | `test_read → worker.read → core.price` | `test_read → tests/test_worker.<module> → worker.<module> → core.<module>` |
| Wrapper reason / distance / priority | Resolved call path / 2 / 72 | Conservative module/import dependency / 3 / 23 |
| Direct affected test | Resolved `test_price → core.price`, priority 82 | Same path, priority 81 |
| Both recommendation path revisions | Both | Both |

No edge is added. Every retained edge, stable ID and per-revision evidence item
is identical to the original case report. The direct test loses one priority point
because the changed target has one fewer incoming dependent. The wrapper's changed
path uses the existing fallback starting score and distance term. These are effects
of graph correction under the **unchanged formula**, not recalibration or failure
probabilities. Warnings now identify the ambiguous module name and unresolved call.

The other **24 complete case reports are identical**, including their scores,
warnings and evidence. All **31** returned recommendations pass validation of
head-test membership, non-removed status, start/end, consecutive typed edges,
direction, revision intersection, deterministic order and resolved/fallback reason.
Separate regressions preserve a valid before-only/after-only call when only the
other revision rebinds, and retain deleted-symbol handling and stable edge IDs.

The existing FP ID and `known_limitation` category are retained. Only its FP
explanation, limitation text and feature tag change to describe the remaining
module/import fallback. No discrepancy membership or category is changed because
selection did not improve. `make evaluate` therefore passed even before those
annotation edits; the separate evidence assertion caught the explanation drift.

### Validation and reproducibility

| Command / check | Observed result |
| --- | --- |
| `.venv/bin/pytest tests/test_module_rebinding.py tests/test_local_imports.py tests/test_analyzer.py tests/test_revision_evidence.py tests/test_corpus.py tests/test_evaluation.py --no-cov --tb=short` | **272 passed**, including all 87 rebinding and 64 local-import tests |
| `make check` | **359 passed**; Ruff lint/format, strict mypy, TypeScript and Vite production build passed |
| `.venv/bin/python -m unittest discover -s scripts -p 'test_*.py' -v` | **8 maintenance tests passed** |
| `.venv/bin/python -m pip check` | No broken requirements found |
| `make evaluate` | Exit 0; all 25 explicit baselines match |
| `cd web && npm run format:check` | Passed |
| `cd web && npm run test:e2e` | **28 passed**, desktop and mobile |
| Repeated evaluation JSON and console output | Byte-identical across repeated runs using the same output path; JSON also identical to `make evaluate` output |
| Snapshot file-order and repeated analyzer-report regression | Identical after excluding only `stats.elapsed_ms` |
| Before/after comparison | All 25 snapshot/label/classification/selected-ID sets unchanged; other 24 complete case reports identical |
| `git diff --check` | Passed |
| Hosted CI for this milestone | Not run; edits remain local and uncommitted |

The added browser scenario uploads the existing rebinding case through the real
local API and checks two selected tests, the wrapper's conservative explanation,
priority 23, four-node module path, absent stale call edge, shared revision evidence,
changed-code preview and an exported report equal to the API response. The dashboard
application code is unchanged. Browser execution used the Chromium launch permission
already established as necessary in this environment; all 28 tests passed. These
browser checks exercise stored snapshot strings, not execution of their Python.

Coverage was **92% overall** (1,123 statements, 88 missed) and **98% analyzer**
(365 statements, 6 missed). The existing Starlette/httpx deprecation and browser
environment warnings were non-failing. Coverage measures executed lines, not
accuracy. No runtime accuracy, performance or hosted-CI claim is made for these edits.

Ignored local artifacts:

- `reports/module-rebinding-before.json` / `.txt`: original evaluation.
- `reports/module-rebinding-red.txt`: 59 failing / 28 passing checks before the fix.
- `reports/module-rebinding-after-code.json` / `.txt`: corrected analysis before
  metadata and evidence-expectation updates.
- `reports/module-rebinding-comparison.json`: before/after evidence and unchanged
  selection counts, with full copies of the changed case result.
- `reports/module-rebinding-focused-final.txt`, `module-rebinding-check.txt` and
  `module-rebinding-browser.txt`: final check output under `reports/`.
- `reports/corpus-evaluation.json`: final `make evaluate` result.
- `reports/module-rebinding-repeat-first.json` and `module-rebinding-repeat.json`:
  repeat reports, with identical `module-rebinding-repeat-first.txt` and
  `module-rebinding-repeat-second.txt` console output.

Final corpus SHA-256:
`41f8992ec96f473cb9bd1d0f8bd89614a42f5c49833c264f9e9f8713f09e0c94`.
Final JSON report SHA-256:
`cb04cff672f0f8cce1f80ca1ad84c3226242de8409ee7d767389a69d755d8a9c`.
The corpus hash changes because annotations changed, not because labels or sources
changed. Reproduction also needs the analyzer code and pinned environment.

### Boundaries and owner handoff

The audit is deliberately flow-insensitive: even unreachable, earlier or identical
repeated bindings can suppress a precise import. Conditional imports remain
unsupported for precise resolution. Global writes inside separate bodies,
attribute/shared-object mutations, reflective changes, runtime imports, dispatch,
re-export/closure propagation and full Python control flow remain outside this
milestone. Conservative module fallback still produces the six recorded FPs;
fixture injection and runtime imports remain the two measured misses.

For an interview: “The analyzer remembered an import even after the code replaced
it. I added a scope-aware binding check, proved the old call edge was wrong with
failing tests, and removed it. The test still appears through conservative module
fallback, so I reported better evidence without claiming better selection accuracy.”

Review analyzer.py, the new module-binding tests, the evidence assertion, the
metadata-only corpus diff and the new browser regression. README, ARCHITECTURE,
CORPUS, BUILD_PLAN, PROJECT_CONTEXT and this record describe the bounded correction.
All changes remain unstaged and uncommitted; the owner handles commit, push, PR and
merge. Reports are ignored reproducibility artifacts, not files to stage.


## Real-repository evaluation v1 — November 11, 2026

Implemented on `codex/real-repository-evaluation`, starting from
`aca764e9e3205a612898e29b065230695667fc85` (merged module-rebinding milestone).
This adds an evaluation workflow and dataset; analyzer behavior, scoring, stable
IDs, revision evidence, deleted-symbol handling, report 2.0, GitHub PR ingestion,
and dashboard design are unchanged. No commit, staging, push, PR or merge was made.

### Data and labeling procedure

Selected six actual functional source changes across MarkupSafe, ItsDangerous and
Schedule, with two changes each. Selection and eight considered/excluded changes
are recorded in `corpus/real/selection.json`; no analyzer output was used to choose
cases. This is a purposive historical pilot, not random or representative sampling.
All three repositories fit; no repository exclusion or size trimming was needed.
Two heads are merges, explicitly compared against pinned first parents. All twelve
complete recursive trees were untruncated. Each revision contains 4–18 supported
Python files and at most 77,705 source bytes, within unchanged ingestion limits.
No captured tree has excluded Python paths, symlinks or submodules. Non-Python
entries remain in tree receipts; non-Python contents other than licenses are not
part of supported snapshots.

The optional capture helper read GitHub REST commit/tree/blob objects, checked
public identity and existing network/source budgets, and retained exact source
strings, SHA-256 hashes, Git blob IDs/sizes and original licenses. Pallets licenses
are BSD-3-Clause; Schedule is MIT. All twelve license receipts match the accessible
attribution copies. No analyzed repository was cloned, checked out, installed,
imported or executed. Source, including setup/test code, remains JSON string data.

Source inspection and AST-only test discovery produced 45 affected, 123 unaffected
and 33 uncertain labels **before the first analyzer run on any of the six cases**.
All six review records remain `draft`, author Codex, reviewer/reference null.
Canonical hashes frozen at that point remain unchanged. This is an agent process
attestation, not independently verified chronology or label review. The review pack
contains all 201 definition IDs, rationales, pinned source links and complete Python
diffs; its generator does not run the analyzer. Inherited contexts and C-extension
variants remain uncertain where Python-only inspection is insufficient. The unit is
a test definition per change, not an expanded pytest item or runtime failure.

The first evaluation, with empty discrepancy maps, exited nonzero. After inspecting
recommendations, the observed FP IDs/explanations and selected-unclassified IDs were
recorded as deliberate baselines. The frozen labels, source snapshots and analysis
outputs were compared before/after this metadata update and are identical. There
was no analyzer tuning. All six cases remain `known_limitation`.

### Observed results

| Case | Selected / discovered | TP | FP | FN | TN | Unclassified total / selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| itsdangerous_fips | 33 / 37 | 29 | 4 | 0 | 4 | 0 / 0 |
| itsdangerous_future | 20 / 44 | 7 | 2 | 0 | 17 | 18 / 11 |
| markupsafe_format_map | 22 / 23 | 1 | 14 | 0 | 0 | 8 / 7 |
| markupsafe_striptags | 22 / 23 | 1 | 15 | 0 | 0 | 7 / 6 |
| schedule_repr | 38 / 38 | 3 | 35 | 0 | 0 | 0 / 0 |
| schedule_tags | 36 / 36 | 4 | 32 | 0 | 0 | 0 / 0 |
| **Overall** | **171 / 201** | **45** | **102** | **0** | **21** | **33 / 24** |

Draft-label precision is 45/147 (30.6%); recall is 45/45 (100%), conditional on the
classified drafts. Selected IDs and all classifications are present in the JSON;
[REAL_EVALUATION.md](REAL_EVALUATION.md) also lists every selected ID. Explanations:
48 resolved paths, 116 conservative module/import paths, 7 changed tests. Every
recommendation passed the existing typed path, caller-to-dependency direction,
changed endpoint, stable edge ID, source range and revision-evidence checks.

The main measured mistakes are broad module/test-module fallback and class-level
fingerprints. `Markup` construction reaches a changed class even when the called
method is unrelated; Schedule selects every discovered test in both cases.
“Resolved call path” does not guarantee feature-level relevance. The 33 uncertain
labels, seven changed-test selections, correlated case-test pairs and nonrandom
sample prevent general accuracy claims. No upstream assertion failures, FIPS runtime
behavior, production performance, hosted CI or deployed integration is asserted.

### Verification

Commands were run from the project root, except the browser suite:

```sh
.venv/bin/pytest tests/test_real_evaluate.py --no-cov
make check
make evaluate
make evaluate-real
.venv/bin/python -m codeimpact.real_evaluate --output reports/real-repeat.json
cd web && npm run test:e2e
```

The focused suite covers offline operation, source-as-data imports/process guards,
exact-repeat determinism, complete denominator accounting, deliberate baseline drift,
output containment and atomic replacement (including hard links and failed writes),
source/tree/license/pin/label tampering, duplicate keys/paths, missing or symlinked
metadata, per-file/aggregate bounds, fabricated review status, invalid evidence
paths, source-only review generation, and mocked recapture of three stored upstream
object sets. The initial test collection failed before the new module existed;
all final workflow/failure-mode regressions pass.

Final results: **34 focused tests passed; 393 Python tests passed** in `make check`,
with Ruff lint/format, strict mypy and TypeScript/Vite production build also passing.
**28 Playwright tests passed**, covering desktop and Pixel 7 layouts against isolated
local servers. Chromium used the required local launch permission. Browser tests
exercise existing dashboard behavior; no dashboard code was changed. Existing
Starlette/httpx deprecation and React Flow/environment warnings were non-failing.

Both final real reports are byte-identical, excluding only embedded analyzer
`stats.elapsed_ms` via the unchanged evaluator. No timestamps or other volatile
fields are removed. The source-only review pack was regenerated and matched exactly.

- Real dataset digest: `9fd07dda75c07067d2f19a9a5202281748d68791832ffe3a0e8d71f40ed64e57`.
- Real corpus digest: `94776d2b16538e5bc837773f4dc4259e84dd804329f4e7be61092ba9fd4ad836`.
- Real report SHA-256: `802054f1bf9b460653ca5da211e19b0c6da841618922de05432fcd0e2beaf32c`.

The original 25 authored case files have **no diff from starting HEAD**. Their
complete before/after evaluation JSON is byte-identical: TP 23, FN 2, FP 6, TN 26,
plus two unclassified selections. Corpus digest remains
`41f8992ec96f473cb9bd1d0f8bd89614a42f5c49833c264f9e9f8713f09e0c94`;
report digest remains
`cb04cff672f0f8cce1f80ca1ad84c3226242de8409ee7d767389a69d755d8a9c`.

Ignored local artifacts: `reports/real-capture/*.json`, `real-first-evaluation.json`,
`real-first-evaluation.txt`, `real-authored-before.json`, `real-authored-before.txt`,
`real-authored-after.txt`, `real-focused.txt`, `real-check.txt`, `real-browser.txt`,
`real-evaluation.json`, `real-evaluation.txt`, `real-repeat.json`, `real-repeat.txt`.
The checked-in dataset, review pack and result document reproduce the workflow
without those artifacts or network access.

Offline provenance checks establish consistency with recorded trees and hashes;
they do not reconstruct raw commit objects, verify commit signatures or authenticate
GitHub afresh. See [the full protocol](../corpus/real/README.md) for this trust
boundary, limits and the human review procedure. Independent label review remains
outstanding by design. All milestone changes are left unstaged and uncommitted.

## Scoped class/module selection refinement — November 11, 2026

This is a user-requested follow-up to real-repository evaluation v1, in the same
unstaged working tree starting at `aca764e9e3205a612898e29b065230695667fc85`.
The earlier section records the initial unchanged-analyzer measurement; the
results below supersede it for the current implementation. No commit, staging,
push, PR or merge was performed.

### Change and regression evidence

`selection.py` separates full AST display fingerprints from propagation seeds.
Body-only aggregate classes no longer imply constructor impact. Aggregate-only
module fallback is filtered through bounded possible source references. Actual
initialization changes, parse failures and constructor changes retain conservative
propagation. The helper uses AST data only and never creates a precise call edge
from an uncertain method spelling. Scoring, stable IDs, edge direction, deletion
handling, schemas and dashboard design are unchanged. See
[Architecture](ARCHITECTURE.md#scoped-aggregate-fallback) for the exact boundaries.

The first regression run failed **15 tests** before implementing the filter
(`reports/selection-red.txt`). Additional safety checks exposed four more protocol
gaps before correction: `str` falling back to `__repr__`, container element
representation, shadowed builtins and unmodeled operator protocols
(`reports/selection-protocol-red.txt`). All **41 selection regressions** now pass.
Coverage includes sibling/test-body edits, method additions/deletions, constructor
changes, direct/local receivers, properties, fluent factories, field/property
name collisions, callbacks, callable aliases, conditional and inherited members,
initialization/default/decorator effects, parse failures, parameter rebinding,
foreign field writes, external bases/custom allocation, local imports, protocol
fallbacks and reference-budget exhaustion. Unsupported special-method changes and
exhausted symbol budgets retain broad fallback with visible warnings.

The first full application run exposed expected stale discrepancy and evidence
assertions. Those were updated only after inspecting actual recommendations; no
source or affected/unaffected/uncertain label was changed. The final check also
caught a mypy variable-type conflict in the new protocol guard; it was corrected
before rerunning the complete check successfully.

### Actual measured results

| Dataset | Before selection | Current selection | Current TP | FP | FN | TN | Unclassified total / selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Authored 25 cases | 31 | 25 | 23 | 0 | 2 | 32 | 2 / 2 |
| Real 6 cases | 171 | 60 | 45 | 4 | 0 | 119 | 33 / 11 |

The authored refinement removes six FPs across `module_overselection`,
`module_rebinding`, `shadowed_names`, `conditional_definitions` and
`inherited_dispatch`. The first three become supported demonstrations: 18 supported
and 7 limitation cases overall. Conditional and inherited references remain
conservative. Fixture injection and runtime imports remain the same two misses.

The real refinement removes **98 of 102 FPs**: all 29 MarkupSafe, all 67 Schedule,
and both timestamp-case FPs. Four FIPS default-initialization FPs remain:
`TestSerializer.test_fallback_signers`, `TestSigner.test_digest_method`,
`TestSigner.test_invalid_separator`, and `test_abstract_algorithm`. These need
argument-sensitive constructor/factory and early-exit analysis; the current filter
does not claim it. No label editing or case-specific suppressions hide them.
All 45 affected drafts remain selected. Current reasons: 6 resolved call paths,
47 conservative module/import paths and 7 changed tests.

Real draft-label precision is 45/49 (91.8%), recall 45/45 (100%). Authored precision
is 23/23 (100%), recall 23/25 (92.0%). The 33 uncertain real labels remain in the
report; none was moved to improve a denominator. The real cases informed this fix
and are now development/regression data, not an unseen accuracy benchmark. All six
review statuses remain draft; no upstream runtime failures or independent label
review are claimed. Full application tests remain the merge gate.

### Commands and verification

Run from the project root, except the browser command:

```sh
.venv/bin/pytest tests/test_selection_precision.py tests/test_module_rebinding.py \
  tests/test_evaluation.py tests/test_real_evaluate.py --no-cov -q
make check
make evaluate
make evaluate-real
.venv/bin/python -m codeimpact.evaluate --output reports/selection-authored-repeat.json
.venv/bin/python -m codeimpact.real_evaluate --output reports/selection-real-repeat.json
.venv/bin/python scripts/review_real.py > reports/selection-label-review.md
cd web && npm run test:e2e
```

- **220 focused regressions passed.**
- **`make check` passed:** Ruff lint/format, strict mypy, **434 Python tests**,
  and TypeScript/Vite production build. Observed statement coverage: 94%; coverage
  is not a correctness or accuracy claim. One existing Starlette/httpx deprecation
  warning was non-failing.
- **`make evaluate` and `make evaluate-real` passed**, with no baseline drift and
  every recommendation's typed paths and revision/source evidence validated.
- **30 Playwright tests passed**, across desktop and Pixel 7 layouts against
  isolated local servers. The rebinding browser regression now checks that the
  unrelated wrapper is absent while import graph evidence remains. A new class
  method regression checks one conservative recommendation, visible full changes,
  source preview and exact JSON export on both layouts. Chromium used its required
  local launch permission; no dashboard production code changed.
- Both evaluation reports are **byte-identical on repeat**. Only embedded analysis
  `stats.elapsed_ms` is excluded. Reversing base/head snapshot file insertion order
  also produces identical complete stable analyses for all 31 cases.
- All 31 source snapshots and affected/unaffected/unclassified maps match their
  pre-refinement records. All graph nodes/edges, `changed`, `removed`, `changes`
  and `source_files` also match exactly. Scores may change when selected paths
  change, but the formula and graph dependent counts do not.
- The regenerated 201-label review pack is byte-identical. Real provenance, exact
  pins, complete tree/source hashes, licenses and frozen label hashes still pass
  the offline loader. No upstream code was executed/imported/installed/checked out.

[The historical baseline](../corpus/selection-baseline-v1.json) retains original
annotations, selected IDs, classification counts and source/label hashes for both
datasets. Active baselines deliberately remove fixed FP annotations and update
uncertain-selection lists and limitation explanations; none was accepted silently.
The corpus/dataset digests change because those annotations are part of the digest.

| Artifact | SHA-256 |
| --- | --- |
| Authored corpus | `33ff141b4817c94c7bb2dccf01ae4aa7cd7722ef6ce2de8e44ddf7afe540629d` |
| Authored report | `4b877c9b23cc8b44bf9a679ba799b2fdb63e702b4b5d3466800e06ea0547d77b` |
| Real corpus | `ed5d8ae64a1d372792408baab537bc347bb7e80ede86766974400f4e7bcb1f72` |
| Real dataset | `fafaf7e886d99f2fc0c47378314c86865b8b8843f9138af032c8fe2daa89882a` |
| Real report | `3bfac5389b252016355396cda5a03e73353b6201744173e572e6247c03b707fa` |

Ignored local artifacts: `reports/selection-before-*.json`, `selection-red.txt`,
`selection-protocol-red.txt`, `selection-focused.txt`, `selection-focused-all.txt`,
`selection-check.txt`, `selection-browser.txt`, `selection-evaluate*.txt`,
`selection-*-repeat.json`, `selection-preservation.json`, `selection-label-review.md`.
The final preservation record contains exact hashes and comparisons. Final
`git diff --check` passed; the index is empty and HEAD remains the starting commit.
All edits, including the earlier real-evaluation workflow, are unstaged/uncommitted.

## Bounded constructor/factory argument tracking — November 12, 2026

Implemented at the user's request to remove the four remaining ItsDangerous
recommendations after the class/module selection refinement. Starting HEAD remains
`aca764e9e3205a612898e29b065230695667fc85`; all preceding work and this follow-up are
unstaged/uncommitted. The previous section is the intermediate 60-selection record.

### Implementation and boundaries

The new `arguments.py` performs bounded AST data-flow queries for changes confined
to supported class-default bindings. It tracks supplied positional/keyword values,
known argument expansions, partial factories, wrapper calls, stored option mappings,
known collection iteration, and source-level early exceptions. Both revisions must
support exclusion. The graph and evidence remain unchanged; separate per-module
traversals preserve recommendations justified by other changed sources.

Pure local pytest factory providers (including known `request.param` alternatives)
and direct literal data providers can supply values. This is narrower than general
fixture injection. The original authored injection miss remains unchanged.
Explicit standard-library digest references can be recognized as non-None callable
values without importing or calling them; arbitrary external settings cannot.
An added passive helper import from an already-imported module no longer creates
an independent all-tests fallback. Other initialization effects stay conservative.

Unknown arguments, imported values, callables, iteration counts, source/unknown
implicit protocols, escaping objects, unsupported mutation/flow and exceeded
budgets retain recommendations. The applicability check declines descriptor
construction, custom `staticmethod`, class creation hooks, unsupported bases and
other module changes. Limits are documented in
[Architecture](ARCHITECTURE.md#bounded-constructor-and-factory-arguments). No
analyzed source, dependency, fixture or upstream test was executed/imported/installed
or checked out. No repository/test names are used for suppression.

### Regression development and observed outcomes

The initial regression run, before changing the analyzer, had **9 failures and
12 passes** (`reports/arguments-red.txt`). It covered explicit/positional/expanded
arguments, default/None/unknown controls, wrappers and partials, local parameterized
factory providers, stored factory options, fallback dictionaries, early exceptions,
rebinding, before/head preservation, other initialization effects, and the exact
four real false positives. Additional failing controls were added for passive-helper
imports, unknown imported values, implicit protocols, branch mutation, descriptor
and custom decorator effects, local-import timing, unknown iterations and comparisons. A further failing control verifies that a helper
import cannot hide a change in module initialization order.

All **47 argument regressions** now pass, also covering query budgets, source-as-data,
repeatability, keyword-only arguments and deep alias chains. Later failing controls
cover captured constructor defaults, shared mutable function defaults and unchanged
module/class initialization effects. These cases retain conservative fallback;
nonliteral defaults are not recreated or guessed. Effectful definition headers
and arbitrary surrounding initialization decline the exclusion filter. A full run before the
baseline update failed only the three stale real-evaluation expectations. The
updated drift test deliberately restores an obsolete FP annotation and still
requires a nonzero evaluator exit; improvements are not silently accepted.

| Dataset | Selected before | Selected now | TP | FP | FN | TN | Unclassified total / selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Authored 25 cases | 25 | 25 | 23 | 0 | 2 | 32 | 2 / 2 |
| Real 6 cases | 60 | 56 | 45 | 0 | 0 | 123 | 33 / 11 |

All four former `itsdangerous_fips` FPs are excluded:

- `TestSigner.test_digest_method`: explicit MD5 survives the partial factory,
  constructor and nested algorithm construction; no changed default is read.
- `TestSerializer.test_fallback_signers`: visible serializer factory variants,
  signer options and fallback dictionaries all supply explicit digests.
- `TestSigner.test_invalid_separator`: known byte membership establishes an early
  source-level exception before default lookup.
- `test_abstract_algorithm`: the unrelated abstract class/method does not consume
  the edited defaults.

The FIPS case now selects **29/37**, TP 29 / FP 0 / FN 0 / TN 8. The other five
real cases retain identical analysis reports. Overall reasons are 6 resolved call
paths, 43 conservative module/import paths and 7 changed tests. All 45 affected
labels remain selected; all 33 uncertain labels and their 11 selections are unchanged.
Classified draft-label precision and recall are both 45/45. These are regression
results on cases used to develop the fix, not independently reviewed labels,
production accuracy, runtime failures or an unseen benchmark. Existing fixture
injection and runtime-import misses remain in the authored totals.

### Final verification

Commands from the project root, except the browser suite:

```sh
.venv/bin/pytest tests/test_arguments.py tests/test_selection_precision.py \
  tests/test_module_rebinding.py tests/test_evaluation.py tests/test_real_evaluate.py --no-cov
make check
make evaluate
make evaluate-real
PYTHONHASHSEED=17 .venv/bin/python -m codeimpact.real_evaluate \
  --output reports/arguments-real-repeat.json
PYTHONHASHSEED=31 .venv/bin/python -m codeimpact.evaluate \
  --output reports/arguments-authored-repeat.json
.venv/bin/python scripts/review_real.py > reports/arguments-label-review.md
cd web && npm run test:e2e
```

- **267 focused regressions passed**; the new argument file contributes 47.
- **`make check` passed:** Ruff lint/format, strict mypy, **481 Python tests**, and
  TypeScript/Vite production build. Statement coverage was 93%; it is not an
  accuracy claim. One existing Starlette/httpx deprecation warning was non-failing.
- **Both evaluations passed** with zero baseline drift. All typed evidence paths,
  source ranges, revision provenance, pins, complete source/tree hashes, licenses
  and frozen label hashes pass their existing validations.
- **32 Playwright tests passed**, desktop and Pixel 7. The additional regression
  checks that an explicit constructor override is excluded, the default user retains
  its existing resolved class path in both revisions, changed-source preview works,
  and exported JSON equals the API response. No dashboard production code changed.
- Repeat reports are **byte-identical**, including different hash seeds. Reversing
  snapshot file order also yields identical stable analyses for all 31 cases.
  Only the already-documented `stats.elapsed_ms` field is omitted.
- All 31 source/label maps, graph nodes/edges, changed and removed IDs, change ranges
  and full source-evidence records match the preceding milestone exactly.
  The entire authored evaluation JSON is byte-identical. The other five complete
  real case analyses are identical; only FIPS recommendation/impact propagation
  changes. Scoring formulas, report schemas and stable IDs are preserved.
- The regenerated 201-label review pack is byte-identical. Review statuses remain
  draft. Only the FIPS discrepancy map and limitation explanation were deliberately
  updated. The historical archive now also retains the intermediate four-FP baseline.

| Artifact | SHA-256 |
| --- | --- |
| Authored corpus | `33ff141b4817c94c7bb2dccf01ae4aa7cd7722ef6ce2de8e44ddf7afe540629d` |
| Authored report | `4b877c9b23cc8b44bf9a679ba799b2fdb63e702b4b5d3466800e06ea0547d77b` |
| Real corpus | `cc295683bb432a32bc554cfc2dd3b31dd1ac6dbc83ea4e1e2eb417c5060c67f3` |
| Real dataset | `bcc3c986a75f83baacfd7348e4ed2d7394cfb03a299b147138010a0ea0c69bec` |
| Real report | `258ab743f6af677e714d238e9e1f3fd099f090a7e65ec3bd0c61b1e144992cae` |

Ignored local evidence includes `reports/arguments-before-*.json`, `arguments-red.txt`,
`arguments-*-red.txt`, `arguments-focused.txt`, `arguments-focused-all.txt`,
`arguments-check.txt`, `arguments-browser.txt`, `arguments-evaluate*.txt`,
`arguments-*-repeat.json`, `arguments-preservation.json`, and `arguments-label-review.md`.
Final `git diff --check` passed, the index is empty, and HEAD is unchanged. No commit,
push, PR, branch creation or merge was performed.

## Original fresh-repository evaluation v2 and regression gates — November 12, 2026

Implemented on `codex/fresh-repository-validation` from merged reference
`bef99db1bbc144ac399ecb3f537269293fe3f22e`. The work adds evaluation data and gates;
**analyzer behavior, scoring, app report contracts and dashboard are unchanged**.
No commits, staging, pushes, PRs or merges were performed for this milestone.

### Source selection, labels and first measurement

The pre-analysis protocol selected two localized source changes each from
Atomicwrites, Python Slugify and Cachetools, all previously absent from v1.
Ten considered changes were excluded for documented documentation/release/test-only,
duplicate-merge or broad-refactor reasons. This is purposive small-project sampling,
not random or newest-two sampling. All six changes fit the original limits.
The existing bounded capture script read exact commit/tree/blob objects over HTTPS,
including full supported before/after Python trees and MIT license bytes. No
repository was checked out, imported, installed or executed. No snapshot was trimmed.

Source inspection produced **581 definition labels: 109 affected, 450 unaffected,
22 uncertain**. All six review statuses remain draft, author Codex, with no human
reviewer claimed. Complete sources, label/selection hashes, six frozen engine/source
hashes and the source-only review pack were recorded before the first analysis.
The pre-analysis `frozen-inputs.json` file SHA-256 is
`3cf5b6d90e1d04e2b1b0632b3fd68ce6f3f34e4958a69344ef0669a20e4c210c`.
Hashes attest to integrity and recorded procedure, not independent certification.

The first evaluator run exited 1 against deliberately empty discrepancy annotations.
`corpus/real-v2/first-run.json` preserves first measured IDs, counts, classifications,
reason counts, stable analysis hashes, original drift messages and raw-report hash.
Only discrepancy maps, expected uncertain selections and limitation explanations
were then deliberately annotated. Source/label/provenance/review-pack hashes remain
unchanged. No analyzer tuning or replacement of difficult cases occurred.

| Dataset | Selected | TP | FP | FN | TN | Uncertain total / selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Authored 25 | 25 | 23 | 0 | 2 | 32 | 2 / 2 |
| Real v1 six | 56 / 201 | 45 | 0 | 0 | 123 | 33 / 11 |
| Fresh v2 six | 362 / 581 | 65 | 284 | 44 | 166 | 22 / 13 |

V2 explanation totals: 6 resolved paths, 349 conservative module/import paths,
7 changed tests. Precision is 65/349 (18.6%); recall 65/109 (59.6%) against classified
draft labels. Per-case/repository IDs, metrics, pins, coverage, concrete mistakes and
interpretation are in REAL_EVALUATION_V2.md and generated reports. V2 is kept separate
from both existing datasets; passing a recorded baseline does not remove mistakes.

### Workflow and failure-mode verification

The new `fresh_evaluate.py` reuses `evaluate_real` and its typed evidence validation.
The existing CLI accepts an evaluator/default paths so both workflows share output
protection and atomic writes. It adds an explicitly versioned fresh extension 1.0;
existing dataset wrapper 1.0, evaluation 1.0 and analysis 2.0 remain unchanged.
The v2 gate checks frozen source/label/engine receipts, complete provenance, all
recommendation evidence, recorded discrepancy annotations and the first measured
selections/classifications/analysis hashes. Metadata limits include added receipts
and the source-only review pack. Original data/report hashes have a preservation test.

28 new workflow tests cover incomplete or altered snapshots, missing/overlapping
labels, coordinated label-hash rewrites, truncated provenance, parent/license
mismatch, invalid review claims, frozen-source inventory/path tampering, changed
engine/review bytes, metadata limits, symlink/missing first-run receipts, malformed
evidence, baseline drift, protected output, offline/source-as-data execution,
reordered inputs, original data/report preservation, and CI gate presence.
The first workflow test invocation failed collection because the new module did not
yet exist (`reports/v2-workflow-red.txt`); the implemented failure-mode suite passes.

Observed commands:

```sh
.venv/bin/pytest tests/test_fresh_evaluate.py tests/test_real_evaluate.py \
  tests/test_corpus.py tests/test_evaluation.py --no-cov
make check
make evaluate
make evaluate-real
make evaluate-real-v2
PYTHONHASHSEED=17 .venv/bin/python -m codeimpact.evaluate \
  --output reports/v2-repeat-authored.json
PYTHONHASHSEED=31 .venv/bin/python -m codeimpact.real_evaluate \
  --output reports/v2-repeat-v1.json
PYTHONHASHSEED=47 .venv/bin/python -m codeimpact.fresh_evaluate \
  --output reports/v2-repeat-fresh.json
.venv/bin/python scripts/review_real.py --corpus corpus/real-v2 \
  > reports/v2-review-repeat.md
cd web && npm run test:e2e
```

- **509 Python tests passed**, including **28 new v2 workflow tests**; the combined
  focused evaluator/corpus suites passed **143 tests**.
- `make check` passed Ruff lint/format, strict mypy, pytest and the TypeScript/Vite
  production build. One existing Starlette/httpx deprecation warning was non-failing.
- **32 Playwright tests passed** on desktop and Pixel 7 using isolated local servers.
  No dashboard behavior or upstream runtime tests were changed/executed.
- **All three evaluations passed** with matching recorded mistakes. Offline tests
  forbid socket connections, subprocesses and imports of the three analyzed packages.
- All three report JSON files are **byte-identical** across repeat runs/different
  hash seeds. Reversing snapshot file order yields identical stable analyses for
  **all 37 cases**. Only the existing `stats.elapsed_ms` field is omitted.
- All original authored/v1 dataset files, historical baselines and stable reports
  remain byte-identical. Frozen analyzer/selection/argument/model/ingestion source
  hashes match the reference commit. The 581-label review pack regenerates identically.
- CI is configured with all three offline commands, using pinned local data and no
  capture step. These uncommitted workflow changes have not run on GitHub; the checks
  above were executed locally. Remote CI must pass after the user's eventual push.

| Stable artifact | SHA-256 |
| --- | --- |
| Authored report (unchanged) | `4b877c9b23cc8b44bf9a679ba799b2fdb63e702b4b5d3466800e06ea0547d77b` |
| V1 report (unchanged) | `258ab743f6af677e714d238e9e1f3fd099f090a7e65ec3bd0c61b1e144992cae` |
| Fresh v2 report | `ec86ffd62cedcdd19c97e1287f6902355e250ecb1b0e7dc0321d3afe555749ed` |

Ignored local evidence: `reports/v2-capture/`, `v2-first-report.json`,
`v2-first-run.txt`, `v2-check.txt`, `v2-browser.txt`, `v2-focused.txt`,
`v2-evaluate*.txt`, `v2-repeat-*.json`, `v2-review-repeat.md`, and
`v2-verification.json`. Initial results and all pinned source/provenance inputs needed
for offline reproduction are retained in the versioned dataset, not only reports/.

### Remaining work

The 44 v2 misses are partial-bound modern Slugify calls; recommended next work is
bounded module-level `functools.partial` call binding with ambiguity/rebinding guards.
The 284 false positives expose separate dispatcher-argument and protocol-fallback
limitations. Independent human label review remains outstanding, as do the authored
fixture-injection/runtime-import misses. No omitted test is certified safe to skip.
Future analyzer or reviewed-label work must preserve the initial v2 measurement and
explicitly version its new reference/baseline instead of silently updating this gate.

Final diff validation passed; the index is empty and HEAD remains the reference.
All milestone changes are unstaged and uncommitted.

## Bounded module-level partial binding — November 12, 2026

Implemented after the original v2 measurement above, at the user's request to
repair the Slugify misses. This changes bounded call resolution, so v2 is now
**development/regression data**. It is not fresh validation of this fix. All labels
remain agent drafted; no upstream code or tests were executed and no human review
or runtime failure evidence is claimed.

### Implementation and regression development

`partial_bindings.py` recognizes single direct module assignments to imported
`functools.partial`, including aliases and annotated assignments. Targets are plain,
undecorated functions reached through direct/relative imports, module aliases,
`src/` layouts, same-module definitions and bounded package re-exports. Slugify's
wildcard package exports require a complete static export inventory and a unique
target; dynamic or competing exports are declined. Ordinary call resolution is
otherwise unchanged. No synthetic nodes or invocation edges at construction are added.

The new call edge retains the actual call-site range, underlying function range
and a textual partial-binding location. Source order, module and lexical shadowing,
rebinding/deletion, conditional imports/bindings, wildcard uncertainty, dynamic
arguments/targets, import cycles and local stdlib shadowing have regression controls.
Unsupported/rebound/conditional/chained candidates cannot fall through to a same-named
function. Before-only and deleted-target evidence remains valid. Stable IDs, edge
direction, report 2.0, scoring formula and selection/argument code are unchanged.
The new graph can change scores; heuristic scores remain non-probabilistic.

Initial tests ran before implementation: **15 failed, 33 passed**, including both
real Slugify misses (`reports/partial-red.txt`). A final ambiguity review added five
controls; four reproduced the same-name fallthrough before the guard was tightened
(`reports/partial-ambiguity-red.txt`). Final focused suite: **72 passed**. No labels
were modified to make these regressions or evaluations pass.

### Preserved and current measurements

| Dataset / baseline | Selected | TP | FP | FN | TN | Uncertain total / selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Authored 25 (unchanged) | 25 | 23 | 0 | 2 | 32 | 2 / 2 |
| Real v1 six (unchanged) | 56 / 201 | 45 | 0 | 0 | 123 | 33 / 11 |
| Original v2 `bef99db` (preserved) | 362 / 581 | 65 | 284 | 44 | 166 | 22 / 13 |
| Current v2 `module-partial-v1` | 413 / 581 | 109 | 291 | 0 | 159 | 22 / 13 |

All **44 Slugify false negatives** are now selected. The fix also exposes **seven
additional false positives**, explicitly recorded: four case/test pairs reject
invalid arguments before the changed helper, and three ASCII-case calls use
`allow_unicode=True` to bypass transliteration. Existing 284 false positives remain.
See REAL_EVALUATION_V2.md for their exact IDs, per-case/repository counts and examples.
Current precision is 109/400 (27.25%) and recall 109/109 (100%) against classified
draft labels. Explanation totals are 58 resolved paths, 348 conservative paths and
7 changed tests. All 22 uncertain IDs remain counted: 13 selected, 9 unselected.

Every original authored/v1/v2 file remains byte-identical, including v2's 24 original
files, source/labels/provenance, discrepancy annotations, review pack, frozen engine
receipt and first measurement. Current results and current engine hashes are stored
separately in `corpus/real-v2/baselines/module-partial-v1.json`; no automatic baseline
update command was added. The final ambiguity guard changed only the current source
hash: a direct measurement comparison confirmed unchanged selections and evidence
before that hash was deliberately updated.

The current gate validates original input/annotation/first-run hashes and the current
seven-file engine inventory. Only discrepancy category/maps/limitations may be
applied as in-memory overlays; labels and snapshots cannot be overlaid. The active
measurement and discrepancy maps must both match. Fresh extension **2.0** reports
current and original summaries separately, with `first_measurement_matches: false`
and `current_measurement_matches: true`. The original analyzer is retained as a
recorded first measurement, not claimed to be rerun by the current command. Analysis
2.0, evaluation 1.0 and dataset-wrapper 1.0 remain unchanged.

### Final verification of the completed change

Observed on the final source:

```sh
.venv/bin/pytest tests/test_partial_bindings.py --no-cov
make check
make evaluate
make evaluate-real
make evaluate-real-v2
PYTHONHASHSEED=17 .venv/bin/python -m codeimpact.evaluate \
  --output reports/partial-repeat-authored.json
PYTHONHASHSEED=31 .venv/bin/python -m codeimpact.real_evaluate \
  --output reports/partial-repeat-v1.json
PYTHONHASHSEED=47 .venv/bin/python -m codeimpact.fresh_evaluate \
  --output reports/partial-repeat-v2.json
cd web && npm run test:e2e
```

- **587 Python tests passed**, including **72 partial-binding regressions** and
  **34 v2 workflow tests**. One existing Starlette/httpx deprecation warning remains
  non-failing. Ruff lint/format, strict mypy and TypeScript/Vite production build passed.
- **32 Playwright tests passed** on desktop and Pixel 7. No dashboard changes were made.
- **All three evaluation commands exited 0** against their deliberate baselines.
  Passing preserves the recorded mistakes; it does not establish safe test skipping.
- All three stable report files match byte-for-byte on repeated runs with different
  hash seeds. A separate seed-73 run reversed snapshot file order and reproduced
  stable analysis for **all 37 cases**. Only existing `analysis.stats.elapsed_ms` is
  excluded. Authored/v1 reports still match their original hashes exactly.
- Source/provenance/evidence validation, original-v2 preservation, baseline-drift
  rejection, offline/source-as-data guards and source-only review regeneration pass.
  Selection, argument tracking, models and GitHub ingestion source bytes are unchanged.
- Local checks passed; remote GitHub CI has not run on these uncommitted changes.
  The existing CI configuration includes all three offline evaluations and browser tests.

| Final stable artifact | SHA-256 |
| --- | --- |
| Authored report (unchanged) | `4b877c9b23cc8b44bf9a679ba799b2fdb63e702b4b5d3466800e06ea0547d77b` |
| V1 report (unchanged) | `258ab743f6af677e714d238e9e1f3fd099f090a7e65ec3bd0c61b1e144992cae` |
| Current v2 report | `efe5413cdb4c73b554f5d526d0947f597ea71b5588768969a8198a84985885ed` |

Ignored local verification artifacts include `reports/partial-{red,ambiguity-red,
focused,check,browser,determinism}.txt`, `partial-evaluate-*.txt`,
`partial-repeat-*.json`, `partial-verification.json`, `partial-before-files.json`
and before-report copies. Versioned baseline receipts contain the results needed
by offline CI. Final Git checks confirm an empty index and unchanged HEAD `bef99db`;
all work remains unstaged and uncommitted.

### Remaining boundaries and next work

This milestone binds the underlying callable; it does not evaluate arbitrary factories,
imports, execution order, monkeypatches, dynamic dispatch or argument-dependent paths.
Function-local/imported/nested partial bindings, constructors and bound methods remain
outside this resolver. The two authored misses (fixture injection and runtime imports)
and Cachetools fallback over-selection remain. Recommended next work is bounded
argument-sensitive reachability for ordinary/partial calls, starting with the seven
newly exposed early-validation/unicode-bypass controls. Preserve both v2 baselines and
all labels; independent human review remains outstanding.

## Bounded argument-sensitive call filtering — November 12, 2026

Implemented at the user's request to remove the seven false positives introduced by
partial binding. All seven case/test pairs are now excluded, while all 109 affected
v2 selections remain. The original and partial-binding v2 baselines are preserved;
this section records a third measurement. V2 remains development/regression data,
with agent-drafted labels and no independent review or upstream runtime evidence.
Analyzed source was read as data; no upstream code or tests were executed.

### Implementation and regression development

`call_arguments.py` follows existing resolved call sites using bounded literal and
parameter bindings, partial captures, keyword overrides, forwarded options,
supported branch guards and early returns/raises. Filtering requires the complete
changed module difference to consist of existing undecorated function bodies. Both
revisions and every relevant call site must support exclusion. Reaching an edited
function retains its dependency; this does not infer whether an edited line runs.

Only test-to-function call contributions to selection are filtered. Serialized
graph nodes, edges, IDs, direction, change records, source evidence and the scoring
formula remain unchanged. Module/import fallback remains conservative. Twenty
retained ASCII-case recommendations now use the modern branch instead of the
legacy branch, with unchanged scores, distances and revision classifications.

Unknown bindings, mutable defaults, modified/escaping options, mutable partial
captures, unsupported control flow, callbacks, recursion, customized functions and
exhausted budgets retain the existing path. Limits are 2,000 query steps, 16 nested
callable levels and 64 carried arguments/collection items. General dynamic dispatch,
implicit protocols and external monkeypatching remain outside this bounded query.
Internal call metadata does not change analysis report schema 2.0.

The first regression run preceded implementation: **9 failed, 20 passed**
(`reports/dispatch-red.txt`). Additional failure-mode regressions caught mutable
options/defaults, callable escape/customization, invalid bindings and conservative
fallback boundaries during development. Final coverage includes **61 call-argument
tests** and **five additional v2 gate tests**, including previous-baseline tampering,
a missing previous receipt and the required new source hash. No labels were changed.

### Preserved and current measurements

| Dataset / baseline | Selected | TP | FP | FN | TN | Uncertain total / selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Authored 25 (unchanged) | 25 | 23 | 0 | 2 | 32 | 2 / 2 |
| Real v1 six (unchanged) | 56 / 201 | 45 | 0 | 0 | 123 | 33 / 11 |
| Original v2 `bef99db` (preserved) | 362 / 581 | 65 | 284 | 44 | 166 | 22 / 13 |
| V2 `module-partial-v1` (preserved) | 413 / 581 | 109 | 291 | 0 | 159 | 22 / 13 |
| Current v2 `argument-guards-v1` | 406 / 581 | 109 | 284 | 0 | 166 | 22 / 13 |

The seven removed recommendations comprise four case/test pairs that reject invalid
arguments before the changed helper and three ASCII-case unicode bypasses. Exact
IDs and per-case/repository counts are in [REAL_EVALUATION_V2.md](REAL_EVALUATION_V2.md).
Current explanation totals are **51 resolved paths, 348 conservative paths and
7 changed tests**. Precision is 109/393 (**27.74%**) and recall 109/109 (**100%**) against
classified draft labels. All 22 uncertain IDs remain counted: 13 selected, 9 unselected.
No new false positives or false negatives appeared relative to the partial baseline.

Every pre-existing corpus file remains byte-identical, including all 25 prior v2
files, both measurement receipts, snapshots, labels, provenance, discrepancy
annotations and the review pack. The new baseline is separately recorded at
`corpus/real-v2/baselines/argument-guards-v1.json`, with eight current engine source
hashes and the previous baseline's byte hash. The gate checks both historical
receipts and current measurements; it never automatically accepts drift. Fresh
wrapper **3.0** exposes original, previous and current summaries separately, with
`first_measurement_matches: false` and `current_measurement_matches: true`. Analysis
2.0, evaluation 1.0 and dataset-wrapper 1.0 remain unchanged.

### Final verification of the completed change

Observed on the final source:

```sh
.venv/bin/pytest tests/test_call_arguments.py tests/test_partial_bindings.py \
  tests/test_arguments.py --no-cov
.venv/bin/pytest tests/test_fresh_evaluate.py --no-cov
make check
make evaluate
make evaluate-real
make evaluate-real-v2
PYTHONHASHSEED=17 .venv/bin/python -m codeimpact.evaluate \
  --output reports/dispatch-repeat-authored.json
PYTHONHASHSEED=31 .venv/bin/python -m codeimpact.real_evaluate \
  --output reports/dispatch-repeat-v1.json
PYTHONHASHSEED=47 .venv/bin/python -m codeimpact.fresh_evaluate \
  --output reports/dispatch-repeat-v2.json
cd web && npm run test:e2e
```

- **653 Python tests passed**, including the **180 focused argument/partial tests**
  and **39 v2 workflow tests**. One existing Starlette/httpx deprecation warning is
  non-failing. Ruff lint/format, strict mypy and TypeScript/Vite production build passed.
- **32 Playwright tests passed** on desktop and Pixel 7. No dashboard files changed.
- **All three evaluation commands exited 0** against their deliberate baselines.
  Passing means recorded results match, not that no mistakes remain.
- All three stable reports are byte-identical across repeated runs with different
  hash seeds (17, 31 and 47). A seed-73 run reversed snapshot file order for **all
  37 cases** and reproduced their stable analysis. Only the already documented
  `analysis.stats.elapsed_ms` field is excluded from stable analysis comparisons.
- Authored/v1 stable reports are byte-identical to the pre-change copies. All
  original dataset bytes and both prior v2 baselines match their pre-change hashes.
  Selection, constructor argument tracking, partial binding, models and GitHub
  ingestion source bytes are unchanged. V2 graphs and retained scores are unchanged;
  exactly seven recommendations disappeared and 20 retained evidence paths improved.
- Local checks passed. Remote GitHub CI has not run on these uncommitted changes;
  the existing workflow includes all three offline evaluations and browser tests.

| Final stable artifact | SHA-256 |
| --- | --- |
| Authored report (unchanged) | `4b877c9b23cc8b44bf9a679ba799b2fdb63e702b4b5d3466800e06ea0547d77b` |
| V1 report (unchanged) | `258ab743f6af677e714d238e9e1f3fd099f090a7e65ec3bd0c61b1e144992cae` |
| Current v2 report | `fc33aede311104cd63bdef021484f8be81471a588c9d9cd486230937be491fb9` |

Ignored local evidence includes `reports/dispatch-{red,focused,workflow,check,browser,
determinism}.txt`, `dispatch-evaluate-*.txt`, `dispatch-repeat-*.json`,
`dispatch-before-files.json`, before-report copies and `dispatch-verification.json`.
The versioned baseline contains the current results and receipts needed by offline CI.
Final diff checks passed; the index is empty and HEAD remains `bef99db`. All changes
remain unstaged and uncommitted.

### Remaining boundaries and next work

The older **284 false positives** remain: 117 Slugify and 167 Cachetools selections.
The two authored misses involving fixture injection and runtime imports also remain.
These are recorded analyzer limitations, not failing regression checks. Recommended
next work is a separate bounded Cachetools protocol-fallback milestone, beginning
with the 136 LFU case false positives and treating the 31 descriptor-case false
positives as a distinct control. Preserve all three measurements and obtain human
label review before broader accuracy claims. No omitted test is certified safe to skip.
