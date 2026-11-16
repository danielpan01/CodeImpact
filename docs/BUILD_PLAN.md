# Build plan and portfolio strategy

## Active roadmap — updated November 16, 2026

**Milestones 1–6 match their implemented technical scope. The product still has
explicit coverage, accuracy and release-readiness work.** Live hosting and the human
pilot remain owner-deferred; independent source-label review remains pending.
Do not interpret completion of local deployment preparation as a hosted release.

Reviewed reference: `8d9661f1640619741ed25e570911bea838198666` on `main`, merged in
[PR #12](https://github.com/danielpan01/CodeImpact/pull/12). Its
[post-merge quality run](https://github.com/danielpan01/CodeImpact/actions/runs/43778102565)
passed. The [repository and UI review](REPOSITORY_REVIEW.md) distinguishes this
reference from the new local review changes and records actual verification.

Milestones 8A, 8B and 8C are merged. 8C landed in
[PR #15](https://github.com/danielpan01/CodeImpact/pull/15), commit
`7084ab04dd60881a6dde6e91986911f1d9f6ece2`, with
[post-merge CI passing](https://github.com/danielpan01/CodeImpact/actions/runs/43808633061).
Milestone 7 merged in [PR #16](https://github.com/danielpan01/CodeImpact/pull/16)
at `a4d29a7c7c462c32f0bb7978e45708166b0106b0`; its
[post-merge checks passed](https://github.com/danielpan01/CodeImpact/actions/runs/43930425754).
Milestone 9A is implemented; the owner authorized publication on November 16.
See [the discovery receipt](TEST_DISCOVERY.md) and VALIDATION.md.
The repository-review reference above remains historical.

### Completed foundation

| Milestone | Status against roadmap | Evidence / remaining boundary |
| --- | --- | --- |
| 1. Frontend foundation | Merged, PR #7 | Shared design tokens, real input workflows, Tests-first workspace and coordinated evidence |
| 2. Review interactions | Merged, PR #8 | Test search/filter/sort, exact-path graph focus, file/symbol navigation and source coloring |
| 3. Frontend release polish | Merged, PR #9 | Light/dark themes, responsive focus/recovery and cross-browser checks; separate human walkthrough waived |
| 4. Mapping fallback | Code merged, PR #10 | Eleven false positives removed; broader LFU/descriptor work and independent label review remain |
| 5. Fresh v3 evaluation | Merged, PR #11 | Frozen six-case evaluation, discovery audit and pilot materials; human pilot deferred |
| 6. Local deployment preparation | Merged, PR #12 | Disposable bounded workers, access/admission controls, performance receipt and built-server checks; live hosting deferred |

Current measured limits matter more than a milestone count: authored data retains
two misses; v2 retains 272 false positives; the original v3 result retains 43 false positives and **30 excluded definitions**.
Milestone 7 adds those 30 definitions to a separate current measurement: 85/120
selected, 42 TP / 43 FP / 0 FN / 23 TN, with 12 uncertain definitions unselected.
The original 90-definition denominator and its exclusions remain frozen. All labels still require independent
review. Preserve the historical datasets and measurements through subsequent work.

The November 15 review also makes a bounded phone-spacing improvement: the complete
first demo recommendation is visible without scrolling at 360×844 and 390×844 in
both themes, with all controls and report data retained. This is a local refinement,
not another replacement of the frontend. See FRONTEND_ROADMAP.md and VALIDATION.md.

### Milestone sequence and remaining work

| Order | Milestone | Why now | Done when |
| --- | --- | --- | --- |
| 7 — merged | Bounded test-discovery coverage and explicit scope | Original v3 excluded 30 definitions in `test.py`; current version covers them | Supported filename policy is explicit; discovered/outside-scope inventories are auditable; new evidence and baseline are versioned without rewriting the original v3 result |
| 8 — merged | Visual character, large-report diagnostics and UI quality gates | The owner wants rounder controls and a less bland, more distinctive interface; the LFU example exposes 3,128 raw notes and the interface needs durable regression protection | A visible refresh improves controls, typography, surfaces and identity; grouped diagnostics and visual/accessibility checks protect the result |
| 9A — implemented | Cachetools fallback refinement | Literal-raising local callback proof removes one LFU false positive; 124 remain | All six affected/eight uncertain LFU selections and retained evidence preserved; separate `lfu-callback-v1` receipts |
| 9B | Descriptor and Slugify fallback refinement | Separate mechanisms account for 31 descriptor and 117 Slugify false positives | Each mechanism has its own regression-first milestone and versioned measurement; no blanket suppression of module/import evidence |
| 9C | Module-data dependency refinement | V3 records 37 Inflection and six ISO validator false positives | Supported data/export changes are distinguished using source evidence; initialization side effects remain conservative |
| 10 | Fresh evaluation and reviewed-label release evidence | Existing cases will have informed the next fixes | Unused changes and labels are frozen before evaluation; discovery coverage is included; independent review status and remaining mistakes are recorded honestly |
| 11 | Developer pilot and usability iteration — owner-deferred | Other developers can expose workflow problems not visible to automated tests | Owner resumes the pilot; actual participants complete prepared tasks; feedback and resulting changes are documented |
| 12 | Controlled hosted pilot — owner-deferred | The service is verified locally, not on a real host | Owner chooses/authorizes a host; TLS, secrets, Linux isolation/resource behavior, rate limits, recovery and privacy are verified there |
| 13 | Integrations and persistence — conditional | Accounts, saved reports, CI annotations or private repositories need real usage requirements | A specific pilot need justifies one bounded feature and its access/data-retention model |

Milestones 8A–8C are merged; their visual, diagnostics and accessibility gates
remain active. **Milestone 7 is merged** with one filename extension,
a pre-analysis source-label draft, separately versioned measurements and preserved
history. **9B is next: one bounded descriptor instance/classmethod mechanism.**
The owner selected descriptor refinement first; Slugify remains a separate slice.
Do not start all of milestone 9 as one rewrite.

### Milestone 7: bounded test-discovery coverage — implemented

The acceptance list below is satisfied within the documented static-discovery
boundary. [TEST_DISCOVERY.md](TEST_DISCOVERY.md) records the policy, labels, exact
result changes, historical preservation and UI evidence; [VALIDATION.md](VALIDATION.md)
records actual checks and the publication recheck.

1. Inspect the existing filename/symbol rules and the frozen v3 discovery audit.
   Specify a small supported policy, starting with literal `test.py` as motivated
   by Ordered Set. Do not run pytest collection, import project configuration,
   install upstream dependencies or execute source.
2. Add failing tests for supported names, excluded utility files, nested/class
   definitions, duplicate names, before/head differences and deleted tests.
   Avoid interpreting every `test_` function in arbitrary production code as a test.
3. Draft source-based affected/unaffected/uncertain labels for newly included
   definitions before examining recommendations. Preserve the original 30-entry
   outside-discovery inventory and all original v3 labels/receipts.
4. Implement the smallest bounded change. Report the discovery policy and distinguish
   zero discovered tests, no recommended tests, and known unsupported definitions.
   Any report-contract extension must be explicit, versioned and exercised by the UI.
5. Preserve every old baseline and add a deliberately reviewed current baseline.
   Keep original versus expanded-denominator metrics separate. Do not call a newly
   discovered test affected solely because it was previously omitted.
6. Run focused regressions, all four evaluations, full checks, pilot verification
   and browser tests. Verify stable IDs, evidence, deleted-symbol behavior and
   determinism. Document what discovery still cannot see.

### Milestone 8: visual character, diagnostics and UI quality

The owner wants a less generic appearance with rounder buttons and more character.
Deliver the visual refresh first, then diagnostics and automated protection. Keep
the warm light/graphite dark foundation while improving surface contrast, typography,
action hierarchy and a recognizable CodeImpact identity. Apply the detailed direction in
[FRONTEND_ROADMAP.md](FRONTEND_ROADMAP.md#visual-direction) and the delivery slices in
[FRONTEND_ROADMAP.md](FRONTEND_ROADMAP.md#ongoing-professional-ui-quality).

- **8A — Visual refresh (merged in PR #13):** introduce consistent rounded controls (10–12 px starting
  target), softer outer panels, stronger headings and clear primary/secondary actions.
  Refine the wordmark and a small dependency-graph motif. Reduce repeated boxed
  sections, use purposeful surface tints, and coordinate Tests, Map, Changes and
  evidence. Improve empty/loading/error states and restrained interaction feedback.
  Verify before/after desktop, tablet and phone screens in both themes. A radius-only
  adjustment does not complete this slice.
- **8B — Diagnostics (merged in PR #14):** group the thousands of raw diagnostics by category/file with
  counts, search and expandable complete entries. Keep raw warnings in exports and preserve exact
  evidence; do not make unknowns disappear to improve presentation.
- **8C — Quality gates (merged in PR #15):** 16 reviewed image baselines and
  48 rendered WCAG A/AA scans, using pinned Linux ARM64/Ubuntu/Chromium/fonts and
  fixed local reports. Only fixture elapsed time is fixed; no content is masked.
  Explicit failure/recovery probes verify both gates. CI integration is included;
  the publication branch’s remote checks are recorded separately in Actions.
- Retain the phone first-result regression and 44-pixel interactive controls.
  Exercise long names, zero discovery, zero recommendations, mixed/deleted source,
  large maps, failure recovery and the built pilot access flow in both themes.
- Complete manual keyboard/zoom review alongside the rendered-accessibility scan.
  Existing token-contrast/focus checks remain useful but are not a full audit or
  certification. Record real screen-reader review only if performed.
- Keep new discovery-scope communication readable when milestone 7 introduces it.
  Explain measured coverage without implying that priority is failure probability.

Acceptance is a working UI and reviewed before/after evidence, not a collection of
screenshots or new design tokens alone. Keep the current production build and all
application/evaluation checks green. Do not add fictitious history, team activity,
completion percentages or unsupported backend actions.

Milestone 8A and the phone-spacing regression merged in PR #13. The
[visual receipt](FRONTEND_MILESTONE8A.md) preserves its design and verification
history. Milestone 8B now implements lossless category/file grouping, complete
literal search, filters, 50-note pages and report-scoped state without changing
the API or analyzer. The [diagnostics receipt](FRONTEND_MILESTONE8B.md) documents
supported formats, fallback behavior, screenshots and checks.
**8C is merged**. Its [verification and update protocol](FRONTEND_MILESTONE8C.md)
keep 8A/8B evidence intact. Milestone 7 retains these gates and is implemented.
**Milestone 9A is implemented**, with independent source-label review still pending.
See [the bounded callback proof and measurement](LFU_CALLBACK_REVIEW.md).
Next is a single 9B descriptor mechanism; its 31 draft-label false positives and
eight uncertain definitions are unchanged. Keep Slugify and module-data work separate.

### Later analyzer and evaluation work

For every 9-series milestone, choose one source pattern, add failing regressions,
retain unknown/rebound/side-effect controls, preserve original labels and baseline
files, and record changes in a new measurement. An improvement must not remove
valid affected paths merely to reduce selection size. Heuristic scores are not
probabilities. Fixture injection and runtime imports remain separate authored
limitations; prioritize them after new evidence establishes a bounded useful scope.

Milestone 10 must include test-discovery coverage in its denominators and retain
uncertain/outside-policy cases. Reserve its unused examples before tuning. Source-only
review packs support independent review; no reviewed ground truth or runtime failure
claim is valid without separate evidence. Human source-label review is pending and
can proceed whenever an actual reviewer is available; it is distinct from the
owner-deferred usability pilot.

### Deployment and product decision gates

Live hosting and human participation stay deferred until the owner explicitly
resumes them. Current work may prepare checklists and local tests without claiming
those gates are complete. Before a hosted pilot, validate the exact Linux deployment,
TLS and secrets, host memory limits, source/log retention, readiness, worker cleanup,
concurrent requests and service-wide rate limits. Measure latency and memory under
representative pilot load. Existing single-machine sequential timings are not an SLO
or a capacity claim; the workers are resource-isolated processes, not an OS sandbox.

Keep the public fixture demo and owner-controlled pilot access small. Add individual
identity/private GitHub authorization only with a defined permission and revocation
model. Add report storage only with ownership, retention/deletion and source privacy
requirements. Add queues/caching only after measured latency or usage requires them.
No database, queue or new framework is an automatic next step.

### Completion rule for future work

Run focused tests plus `make check`, `make evaluate`, `make evaluate-real`,
`make evaluate-real-v2`, `make evaluate-real-v3`, `make verify-pilot`, and
`cd web && npm run test:e2e` for application changes. Include frontend formatting
for UI work. Verify relevant determinism and unchanged historical receipts, update
actual results, and leave changes unstaged/uncommitted for the owner's publication.

Historical sections below are retained as historical records. Their old “next”
items and time estimates do not override the active sequence above.

## Original build strategy and milestone history

The local starter is the first vertical slice. A credible flagship project comes
from improving its correctness, evaluating it honestly, and making it useful to
someone besides its author. Treat the following time ranges as estimates.

## 1. Own the engine (1–2 focused days)

Run the demo. Read models.py, analyzer.py and the tests in that order. Draw the graph
for `test_create_order → create_order → checkout → discount` by hand, then explain
why reverse traversal is needed. Change the demo yourself and predict the result.
Inspect module fallback, a deleted function and an unrelated test.

Acceptance: explain stable IDs, AST fingerprints, edge direction, union semantics,
BFS cycle handling, risk scoring, false positives and false negatives without AI.
Review all generated files, then make your own first commit and push.

## 2. Harden analysis (2–4 days)

A 25-case authored dependency corpus is implemented locally in the November 10,
2026 corpus milestone. It covers imports/re-exports, fixture injection, conditional
definitions, nested scopes, class dispatch and module rebinding, retaining exact
known discrepancies and all difficult cases in overall metrics. See [CORPUS.md](CORPUS.md)
and VALIDATION.md. These small authored labels are not real-repository accuracy.

The bounded function-local import extension is now implemented locally: direct
local aliases resolve after their import, ambiguous bindings suppress precision,
and fallback imports belong to their function. The existing `local_import` case
moves from FN to TP with its authored labels unchanged; the other 24 case reports
are identical. See CORPUS.md and the separate VALIDATION.md entry for the boundary
and observed checks. At that milestone precision was 23/29 and recall 23/25 on these authored
labels, not production accuracy.

Bounded module-level rebinding removed a misleading call in `module_rebinding`.
At that milestone its FP remained through fallback, with priority 23 instead of 72.
The subsequent aggregate-selection refinement removes that FP and five others
without changing labels or graph evidence. Current authored counts are TP 23,
FP 0, FN 2, TN 32, with two uncertain selections. See CORPUS.md and the separate
validation records. Fixture injection, runtime imports and constructor/factory
flow need further bounded work, preceded by independent label review and fresh
evaluation cases.
Source revision provenance and changed-code inspection are already in
starting commit `546ee8e`: report 2.0 retains per-revision evidence and exact typed
paths, labels mixed paths, and shows bounded before/after code.
Worker-level budgets for adversarial ASTs and performance measurement remain future
work, separate from this corpus milestone.

Acceptance: no recommendation lacks a valid edge-by-edge path. Publish supported
and unsupported case tables. Compare conservative module-only selection against
symbol-level selection instead of assuming finer graphs are always better.

## 3. Real GitHub PR input (2–3 days)

Implemented locally November 8, 2026; present in starting commit `2604fd7` for the
November 10 milestone.
See VALIDATION.md for observed mocked/live results. Complete supported Python trees
are read from exact merge-base/head revisions; truncated listings fail explicitly.
This completes the public, stateless slice below, not private authorization or hosting.

Implement read-only public PR ingestion first. Validate an exact GitHub PR URL;
fetch metadata, pin base/head SHAs, compute/read the correct merge base, retrieve
bounded source blobs from both revisions, and feed the existing engine. Support
fork heads, pagination, deleted files, API rate limits, private/404 responses, timeouts
and branch movement. Never silently accept a truncated tree or patch.

Use mocked HTTP contract tests plus one manual real-PR smoke test. Keep all tokens
server-side. Do not execute a repository or use its installation scripts. Only after
this works add GitHub App authorization for private repos.

Acceptance: a pasted real PR produces the same stable report as equivalent local
snapshots; repeated runs use the pinned SHAs; errors are actionable and visible.

## 4. Durable jobs and deployment (2–4 days)

Add a worker and job state machine only when remote analyses need asynchronous
execution. Postgres can store jobs/reports; Redis can back a queue and cache if that
operational complexity is justified. Cache by repository, pinned revisions, analyzer
version and configuration. Include idempotency, cancellation, retries and quotas.

Deploy with authentication, isolated parsing workers, request/job limits, protected
secrets, structured logs and health checks. Avoid storing source longer than needed.
Connect the UI to job progress and a shareable report. Include a public fixture demo
that needs no credentials. A deployment is separate from a cloud ChatGPT chat.

Acceptance: an interrupted job recovers correctly, unauthorized report access fails,
and a fresh user can complete the workflow on desktop and phone.

## 5. Measure and present (2–3 days)

The local authored corpus supplies a reproducible first step (25 cases, no live
test execution). Real-repository evaluation v1 now adds six pinned source changes
across three public repositories, offline provenance validation and a label review
pack. Its labels are agent drafted; independent review remains outstanding. See
[REAL_EVALUATION.md](REAL_EVALUATION.md): the first run selected 171/201 definitions
with 102 false positives. Class/module selection removed 98 FPs; bounded constructor/factory argument tracking
now removes the remaining four. Current selection: 56/201, TP 45, FP 0, FN 0, TN 123,
with 33 uncertain tests (11 selected). Sources and draft labels are unchanged; archived baselines preserve the
original measurement. These cases informed the fix and are regression data, not
an unseen benchmark. Next: independently review the labels and reserve fresh
changes before further constructor/factory or fixture-flow work.
Evaluate a fixed, documented set of Python changes with independently reviewed
labels and, where practical, mutation tests. Run trusted fixture code only in a separate controlled
evaluation environment—not in the analyzer. Report repository counts, source sizes,
revisions, machine specs and repeat counts. Measure median/p95 runtime, selection
size, recall against known affected/failing tests, and false positives.

Do not use one tiny demo as an accuracy claim. Publish examples where static analysis
misses a dependency. Keep correctness and test reduction separate metrics.

The strongest 60-second demo:

1. Show a real diff changing a pricing function.
2. Show the graph lighting up through callers to an API test.
3. Click the recommended test and show the exact path and source evidence.
4. Delete or rename a function and show that old dependencies are retained.
5. Show an unaffected subsystem and a clearly labeled unresolved case.
6. Finish with measured evaluation results and the passing CI run.

Resume bullet template, only after measurement:

> Built CodeImpact, a Python change-impact analyzer using AST indexing and graph
> traversal; visualized PR blast radius and explained test recommendations across
> [N] evaluated changes, with [measured recall] and [measured p95 latency].

## Should you one-shot it with Codex?

One-shot a bounded vertical slice, then review. Do not one-shot the entire GitHub
integration, deployment and accuracy story as an opaque final product. The scaffold
already supplies the first slice. Use [CODEX_PROMPT.md](CODEX_PROMPT.md) to direct the
next implementation with explicit acceptance tests. Keep your own commits between
phases. The engineering signal is your ability to explain tradeoffs and evidence.

## Original fresh validation v2 — November 12, 2026

Fresh evaluation v2 is implemented against the frozen `bef99db` analyzer: six
previously unused changes across Atomicwrites, Python Slugify and Cachetools.
It adds pre-analysis receipts, a 581-label draft review pack, preserved first
measurements and all three offline evaluation gates in CI. The engine and both
existing datasets are unchanged. See REAL_EVALUATION_V2.md and VALIDATION.md.

Observed draft-label results are TP 65, FP 284, FN 44, TN 166, with 13 selected
of 22 uncertain definitions. The next target identified by that original measurement was bounded
module-level `functools.partial` call binding, motivated by all 44 Slugify misses.
Begin with source-derived regressions and rebinding/unknown-target controls;
preserve the frozen v2 first measurement and explicitly version any new baseline.
General dispatcher-argument filtering and protocol-specific fallback narrowing
need separate bounded milestones. Independent label review remains outstanding;
the fixture-injection/runtime-import authored misses are not fixed by evaluation.

## Completed bounded partial binding — November 12, 2026

Module-level `functools.partial` calls now bind to uniquely resolved plain functions,
including the bounded package re-exports needed by Slugify. Scope/rebinding/order
controls and revision evidence are covered by regression tests. All 44 v2 Slugify
misses are selected; seven additional false positives are openly recorded. The first
v2 baseline remained untouched and a separate `module-partial-v1` baseline gated
that intermediate behavior. See REAL_EVALUATION_V2.md and VALIDATION.md for measured results.

The next work identified by the partial milestone was bounded argument-sensitive reachability for ordinary function and partial
calls. Begin with the seven newly exposed unicode-bypass/early-validation controls,
then legacy dispatch controls; preserve unknown/overridden arguments and before/head
evidence. Do not mix that work with Cachetools protocol fallback changes. Keep the
original and partial baselines, labels and uncertain counts intact. Human review of
the drafted labels remains outstanding. Fixture injection and runtime imports also
remain separate limitations.

## Completed bounded call-argument guards — November 12, 2026

Existing resolved call paths now use bounded immutable argument checks for branch
bypasses and early type-validation exits. Exactly seven newly exposed Slugify false
positives are removed; all 109 v2 affected labels remain selected. At that milestone, v2 was
109 TP, 284 FP, 0 FN, 166 TN, plus 13/22 uncertain selections. Both prior baselines
remain intact and `argument-guards-v1` separately records current behavior. Other
fallback evidence, graph IDs, revision paths and the scoring formula remain intact.

The next analyzer candidate identified then was bounded protocol-aware fallback narrowing for Cachetools,
starting with source-based LFU versus unrelated cache controls (136 recorded false
positives), with the descriptor/classmethod fallback (31) scoped separately. Do not
claim independent accuracy or remove uncertain IDs. Preserve all three recorded v2
measurements and obtain human label review before broader accuracy claims. Slugify's
remaining 117 fallback false positives, fixture injection and runtime imports also
remain open; the current call-path filter does not solve those mechanisms.

## Bounded mapping fallback — merged in PR #10

Body-only mapping edits can exclude known unrelated receivers from aggregate module
fallback. Eleven FIFO/LRU/RR controls leave the LFU recommendation list; all six
affected and eight uncertain LFU definitions remain. Overall v2 is 395/581 selected:
109 TP, 273 FP, 0 FN, 177 TN, plus 13/22 uncertain selections. Authored/v1 reports and
the other five v2 case analyses are unchanged. No protocol call edges or stronger
reason labels are invented; retained scores are unchanged and all fallback paths remain valid.

The new `mapping-fallback-v1` receipt preserves the original, partial and argument
baselines. Human label review is **pending**, with no reviewer or approval invented;
see [MAPPING_FALLBACK_REVIEW.md](MAPPING_FALLBACK_REVIEW.md). Remaining LFU mistakes
(125), descriptor fallback (31) and Slugify fallback (117) stay recorded. The subsequent
fresh evaluation freezes unused changes/labels before analysis.
Human participation remains deferred; neither milestone supplies independent
accuracy or human usability evidence.

## Fresh evaluation and pilot preparation — November 14, 2026

Six unused changes across three repositories were labeled and frozen against the
merged PR #10 engine before measurement. Results: 41 TP, 43 FP, 0 FN, 6 TN;
84/90 discovered definitions selected. Ordered Set also has 30 test-shaped functions
outside discovery; that case has undefined recall, not a perfect score. All labels
remain drafts. The first result and its mistakes are preserved in a separate v3
gate; all 72 historical corpus files and the three previous reports are unchanged.
The dashboard explains zero discovery and the two-case walkthrough is prepared.
The owner deferred the human pilot; no participant feedback was collected.
See REAL_EVALUATION_V3.md and VALIDATION.md. This technical work merged in PR #11,
commit `02598a155bda061b56d03a0fcee161e13df10e89`, with post-merge CI passing.

## Performance, isolation and local deployment — November 14, 2026

Milestone 6 leaves the analyzer and all 106 historical corpus files unchanged.
The API now runs each analysis in a fresh process with wall/CPU/RSS/output bounds,
reaps failed or cancelled workers, and limits admission before buffering source.
The built same-origin pilot server requires a shared access key for submitted code,
keeps the demo public, and exposes readiness and source-free request logs.
Six fixed inputs have ten measured repetitions each; the largest measured case
has median wall time 1.12 seconds and maximum worker peak RSS 85.1 MiB on this Mac.
These figures are local observations, not multi-user capacity or accuracy claims.

Local HTTP and desktop/phone browser checks verify deployment preparation. Linux
hard address-space enforcement has a dedicated Linux CI test; this Mac verifies
the RSS watchdog and CPU/wall limits. The owner explicitly deferred live
hosting and reaffirmed that deferral when authorizing publication on November 15.
