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

