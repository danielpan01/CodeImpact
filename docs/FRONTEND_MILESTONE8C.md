# Milestone 8C — visual and rendered-accessibility gates

Implemented locally from clean `main` at
`c967862fd7152c6d2883d5289b762ea24b67857d` (merged
[PR #14](https://github.com/danielpan01/CodeImpact/pull/14)). Its
[PR check](https://github.com/danielpan01/CodeImpact/actions/runs/43794211878),
[branch check](https://github.com/danielpan01/CodeImpact/actions/runs/43794161848)
and [post-merge check](https://github.com/danielpan01/CodeImpact/actions/runs/43795661155)
passed. The owner subsequently authorized committing and pushing this milestone
on `codex/frontend-milestone-8c`. It subsequently merged in
[PR #15](https://github.com/danielpan01/CodeImpact/pull/15) as
`7084ab04dd60881a6dde6e91986911f1d9f6ece2`, with
[post-merge CI passing](https://github.com/danielpan01/CodeImpact/actions/runs/43808633061). The results below record the local implementation
handoff. Live hosting and the human pilot remain deferred.

## Canonical environment

Screenshot comparisons use **Linux ARM64, Ubuntu 24.04.5, Playwright 1.65.0,
Chromium 158.0.8127.18 / revision 1254**, headless full Chromium with GPU disabled.
The exact environment is recorded in
[`quality-environment.json`](../web/quality-environment.json) and
[`quality.Dockerfile`](../web/quality.Dockerfile).

The immutable ARM64 base is
`mcr.microsoft.com/playwright:v1.64.1-noble@sha256:f609973e8fd93f38a5ddfd706a65805294247dae8d81b2541c0afe2787746197`.
The 1.65.0 image was not available when inspected. The Dockerfile therefore uses
that older image **only for its pinned OS, libraries, fonts and Node 26.13.0**,
then installs the exact **1.65.0** browser from the npm lockfile. Tests assert the
actual Chromium version. The old bundled browser is not used. No apt upgrades,
host fonts or remotely loaded fonts enter the environment. The Chromium binary's
observed SHA-256 is
`40c121f803bd7f2c3dc394a12f064d14af1faea4baf7938dd2a8edd5175086f6`.

Font files and fontconfig configuration are pinned by the image digest. Installed
font packages include Liberation 2.1.5-3, FreeFont 20211204, IPA Gothic 00303,
Noto Color Emoji 2.047, Loma 0.7.3, Unifont 15.1.01 and WenQuanYi Zen Hei 0.9.45.
There is no application font substitution or new font dependency. The captured
environment receipt is `reports/milestone8c-canonical-environment.txt`.

The host was macOS 26.6.2 ARM64 with no container runtime. With explicit owner
approval, Colima and the Docker CLI were installed and a separate `codeimpact`
VM started (4 CPUs, 6 GiB RAM, 24 GiB disk). The default Docker context was not
changed. This is a local test environment, not a hosted deployment. The VM was
stopped after verification to release memory; tools and the cached image remain.

## Run and inspect

On this Mac, from the repository root:

```sh
colima start --profile codeimpact --vm-type vz --cpu 4 --memory 6 --disk 24 --activate=false
cd web
CODEIMPACT_DOCKER_CONTEXT=colima-codeimpact npm run quality:container -- visual
CODEIMPACT_DOCKER_CONTEXT=colima-codeimpact npm run quality:container -- a11y
```

With an already running ARM64 Docker daemon, omit the context variable. The same
wrapper runs in the `ui-quality` GitHub Actions job on `ubuntu-24.04-arm`. It builds
the dependency image from the lockfile, then runs with **network disabled**, a
read-only repository and an isolated Node dependency volume. Only test output is
writable during comparisons. No daemon port or application port is published.
Images/packages need network access for initial preparation, not for tests.
The wrapper creates an empty `web/node_modules` mountpoint when absent, before
binding the repository read-only. Linux dependencies still come exclusively from
the image-backed volume; a fresh checkout does not require a host `npm ci`.

Inside that canonical container the commands are `npm run test:visual` and
`npm run test:a11y`. A direct `npm run test:visual` on macOS refuses to compare
incompatible images. Optional noncanonical checks on the host:

```sh
npm ci
npm run install:browsers
npm run test:visual:preview
npm run test:a11y
```

Preview captures never read, write or approve expected images. Native accessibility
scans are useful supplemental results; they do not replace canonical screenshots.
The quality suites start their own Vite server on loopback port 5176, refuse to
reuse an existing server and use no Python/API service. The existing behavioral
suite still exercises real API/analyzer/pilot integration on its own ports.

Artifacts are under `web/test-results/quality/{canonical,local}/{visual,a11y,preview}/`:

- `html/index.html`: Playwright report with assertions, screenshots and attachments.
- `results/`: failed-test screenshots, expected/actual/diff PNGs for visual
  differences, and retained traces. A missing baseline has an actual image but
  naturally cannot have an expected/diff image.
- `results.json`: machine-readable outcomes and complete axe result attachments,
  including rule IDs, WCAG tags, affected selectors/HTML, help links and incomplete
  findings that need manual review.

For example, from `web`:

```sh
npx playwright show-report test-results/quality/canonical/visual/html
npx playwright show-report test-results/quality/canonical/a11y/html
npx playwright show-trace test-results/quality/canonical/visual/results/TEST/trace.zip
```

CI uploads `ui-quality-results` even when a gate fails. Accessibility still runs
if visual comparisons fail. The existing lint/types/build, Python tests, four
evaluations, pilot verification and five-project browser suite are retained;
frontend format checking is also included. Behavioral outputs now live in
`web/test-results/e2e/` so a behavioral run cannot clear another suite's artifacts.

## Determinism and update policy

Four complete reports are generated from the existing demo, mixed/deleted fixture,
pinned Cachetools LFU case and pinned Ordered Set zero-discovery case. They retain
all names, counts, sources, warning occurrences, paths, scores and evidence. Only
`stats.elapsed_ms` is fixed to **12.5** in these UI fixtures. That is a display
constant, not a benchmark result. There are **no screenshot masks**.

`scripts/prepare_ui_fixtures.py` parses source as data with the existing analyzer;
it never imports/executes upstream files. Committed fixture and input hashes are
checked before tests. Original source licenses/provenance remain under the
corresponding corpus directories. Fixtures are not historical analyzer baselines.
Refresh them deliberately with `.venv/bin/python scripts/prepare_ui_fixtures.py`,
then review their diff separately from screenshots. Normal tests never generate
reports or expected images.

Tests wait for the relevant UI state, `document.fonts.ready`, and measured layout
agreement across animation frames, including graph positions. Screenshots also
use Playwright's consecutive-image stabilization. Locale is en-US, timezone UTC,
device scale 1, reduced motion on, screenshot animation disabled and caret hidden.
Hover/focus are the actual result of specified interactions. Loading uses a held
local response, not invented progress or a fixed sleep. Unexpected API or external
requests fail. Snapshot cases use the actual local upload request as JSON data.

Comparison tolerance: **0 differing pixels** above a **0.1 per-pixel YIQ color
threshold** (stricter than Playwright's 0.2 default). This permits tiny color
quantization differences, not a percentage of missing controls or displaced text.
There are no retries. Missing baselines fail and are not created by a comparison.

For an intentional visual change, first inspect the failed expected/actual/diff
images, then explicitly update only the affected cases:

```sh
CODEIMPACT_DOCKER_CONTEXT=colima-codeimpact npm run quality:container -- update --grep 'map-desktop-dark'
CODEIMPACT_DOCKER_CONTEXT=colima-codeimpact npm run quality:container -- visual
```

Inside the environment the explicit update command is `npm run test:visual:update`.
Updates are refused in CI and with a defect probe enabled; comparison commands
reject update/ignore-snapshot flags. Review every changed image and fixture before
committing. A browser/base-image upgrade requires deliberate new baseline review.
The original screenshots in `docs/media/milestone8a/` and `milestone8b/` remain
historical evidence and are never overwritten by this workflow.

## Reviewed visual coverage

Sixteen baseline images were individually inspected. Desktop is 1440×900; phone
is 390×844. Component captures retain complete bounded panels where a viewport
would miss source, evidence or diagnostic text. The mixed case captures the full
phone page so its sticky navigation does not obscure the evidence heading.

| State | Baselines | What is protected |
| --- | --- | --- |
| Entry | [Desktop light](../web/tests/quality/baselines/entry-desktop-light.png), [phone dark](../web/tests/quality/baselines/entry-phone-dark.png) | Identity, analysis task, demo/upload actions, typography and disabled actions |
| Tests | [Desktop light](../web/tests/quality/baselines/tests-desktop-light.png), [desktop dark](../web/tests/quality/baselines/tests-desktop-dark.png), [phone light](../web/tests/quality/baselines/tests-phone-light.png) | Selected recommendation, report context, filters/counts, first complete phone result |
| Evidence | [Phone dark](../web/tests/quality/baselines/evidence-phone-dark.png) | Complete four-step trail, expanded exact evidence, actions and Back |
| Focused Map | [Desktop dark](../web/tests/quality/baselines/map-desktop-dark.png) | Four nodes, caller→dependency arrows, selected path, controls and legend |
| Changes | [Desktop light](../web/tests/quality/baselines/changes-desktop-light.png) | File/symbol navigation, line numbers and both source revisions |
| Mixed / deleted | [Mixed phone dark](../web/tests/quality/baselines/mixed-phone-dark.png), [deleted phone light](../web/tests/quality/baselines/deleted-phone-light.png) | Mixed warning, after-only/before-only evidence, removed symbol and empty after file |
| Large diagnostics | [Desktop light](../web/tests/quality/baselines/diagnostics-desktop-light.png), [phone dark](../web/tests/quality/baselines/diagnostics-phone-dark.png) | 3 matching imports of 3,128 notes, complete expanded file groups and filter controls |
| Empty | [Phone light](../web/tests/quality/baselines/empty-phone-light.png), [zero discovery desktop dark](../web/tests/quality/baselines/zero-discovery-desktop-dark.png) | No matches/reset, retained selection, explicit discovery limitation and empty inspector |
| Recovery / loading | [Error phone dark](../web/tests/quality/baselines/error-phone-dark.png), [loading desktop light](../web/tests/quality/baselines/loading-desktop-light.png) | Visible retry/edit controls, actual loading message and disabled inputs; retry must load the report |

This is deliberately not every state × every size × every theme × every browser.
Existing tablet, 360-pixel phone, long-name/path, Map zoom, reflow, reduced-motion,
keyboard/focus/Back/Escape, touch-target and first-result behavioral coverage remains.
Firefox/WebKit retain behavioral gates; only pinned Chromium supplies pixel baselines.
The full API/export/discovery contracts remain covered by the existing tests and
evaluations, not by mocked visual inputs alone.

## Accessibility scope and corrections

`@axe-core/playwright` and axe-core are locked to **4.14.0**. Forty-eight full-page
scans cover 12 states × desktop/phone × light/dark: entry, Tests, evidence, Map,
Changes, mixed evidence, deleted source, diagnostics, no matches, zero discovery,
error and the pilot access form. The pilot scan exercises the rendered form;
the existing built-server tests verify real access enforcement and retry.

Enabled tags are `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa`: axe's
implemented WCAG 2.0/2.1/2.2 A/AA checks. Any violation in that scope fails. There
are no disabled rules, excluded regions or accepted violation counts. Full axe
results retain incomplete findings, which are not automatically established
violations or proof of compliance. Best-practice/AAA rules are outside this scope.

Observed corrections are deliberately small:

- Tests/Changes accessible names now include their visible result counts. Existing
  browser selectors assert the new complete names; no interaction coverage was removed.
- Focusable source panes have a named region role, so their labels are supported.
- Original diagnostic note numbers use visually hidden explanatory text instead
  of an unsupported label on an otherwise generic span. Raw notes remain untouched.
- Map zoom controls have a named group; the library's unsupported generic-div label
  is suppressed in favor of that group. Buttons and behavior are unchanged.
- React Flow attribution uses the existing opaque panel/muted-text tokens, making
  the link readable above the dotted canvas in both themes.

The final canonical scan still reports incomplete `color-contrast` assessments in
six cases: transformed graph labels in the four Map size/theme cases, and one
partly clipped inspector trail label in each desktop deleted-source case. These
remain in the complete axe artifacts; no rule is excluded. Agent inspection found
the full phone trails readable; the live desktop Map's rendered text/background
pairs measured at least **4.96:1 light / 7.14:1 dark**. This does not automatically
resolve contrast for every transform, overlap or scroll position. Broader manual
contrast/assistive-technology assessment remains a coverage limitation.

The final local-preview review exercised keyboard entry/demo, visible focus,
named source focus, Map zoom and phone Escape/focus restoration in both themes.
720×450 reflow was inspected as the layout-viewport equivalent of a 1440×900
window at 200%; this was not an OS browser-zoom or screen-reader study. The existing
44 px target and reduced-motion regressions remain green.

These scans and agent image review are partial coverage, not accessibility
certification or independent usability review. No screen-reader study was performed.

## Observed verification

Final checks and remaining axe review details are recorded in
[VALIDATION.md](VALIDATION.md). The intentional visual probe changed only the test
DOM's primary button to square/magenta: **1 failed, 5,825 differing pixels**. The
intentional accessibility probe removed only its accessible name: **1 failed,
`button-name`**. All 16 expected-image hashes remained unchanged during the visual
probe. The normal missing-baseline run also failed, creating zero expected files.
Native noncanonical comparison and CI baseline-update guards were also exercised
and rejected those commands as intended.
The final full visual suite passed **16/16 twice consecutively** after all UI
corrections, with **0 retries**. Final canonical and native accessibility runs
each passed **48/48**. All **248** existing browser checks passed; `make check`
passed **810 tests with one expected platform skip**. All four evaluations and
local pilot verification passed. All **186** protected files/artifacts retained
their original hashes.

Probe commands (expected failures), followed by recovery commands:

```sh
QUALITY_PROBE=visual CODEIMPACT_DOCKER_CONTEXT=colima-codeimpact npm run quality:container -- visual --grep 'entry-desktop-light'
QUALITY_PROBE=a11y CODEIMPACT_DOCKER_CONTEXT=colima-codeimpact npm run quality:container -- a11y --grep 'desktop-light.*entry'
CODEIMPACT_DOCKER_CONTEXT=colima-codeimpact npm run quality:container -- visual
CODEIMPACT_DOCKER_CONTEXT=colima-codeimpact npm run quality:container -- a11y
```

Probe flags affect isolated test DOM only and are absent in ordinary checks. Saved
failure artifacts are in `reports/milestone8c-proofs/`; run logs use
`reports/milestone8c-*.log`. The initial local scan found the label mismatch; a
concurrent early test run exposed shared-output cleanup, now fixed with separate
directories. Neither failure was hidden by retries or looser assertions.

The first publication [Actions run](https://github.com/danielpan01/CodeImpact/actions/runs/43800264793)
caught a fresh-checkout setup defect: Docker could not create the dependency
mountpoint inside the read-only repository, so both quality commands exited 125
before running tests. A tracked-files-only local copy reproduced that exact error.
Creating the empty mountpoint before the bind fixed it. From that same clean copy,
all **16 visual comparisons (11.0 s)** and **48 accessibility scans (40.4 s)** passed,
without host dependencies, baseline updates or tolerance changes. Logs are
`reports/milestone8c-clean-checkout-{reproduction,visual,a11y}.log`.
Remote results for the follow-up commit are recorded separately in Actions.

After this bounded frontend gate work, the next analyzer task is **milestone 7:
explicit, bounded test discovery**, with new versioned measurements and all original
baselines preserved. Broader fallback changes, hosting and human review are separate.

Local application preview: from the root, run
`CODEIMPACT_WEB_PORT=5185 CODEIMPACT_API_PORT=8015 make dev`, then open
http://127.0.0.1:5185. The API health and real demo were verified there. This local
preview is separate from the quality test server/container.

Implementation references: [Playwright comparisons](https://playwright.dev/docs/test-snapshots),
[container guidance](https://playwright.dev/docs/docker),
[axe integration and limitations](https://playwright.dev/docs/accessibility-testing),
and [GitHub's ARM64 runner availability](https://github.blog/changelog/2026-01-29-arm64-standard-runners-are-now-available-in-private-repositories/).

## Milestone 7 continuation

The preceding counts and images remain the historical 8C receipt. Milestone 7
adds literal `test.py` discovery, so Ordered Set is now a positive browser case.
The active zero-discovery fixture is separately authored unsupported source; the
original fixture/manifest entry remain archived unchanged. Only two active images
change, under new `milestone7-` filenames. All 16 original baseline PNGs remain
unchanged, with 16 active comparisons and 18 retained images. The 48 axe scans
include the expanded new scope disclosure. No tolerance, rule, retries or region
exclusions changed. See [the reviewed differences](TEST_DISCOVERY.md#frontend-and-visual-review)
and the separate milestone 7 validation record.
