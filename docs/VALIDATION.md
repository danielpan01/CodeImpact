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

