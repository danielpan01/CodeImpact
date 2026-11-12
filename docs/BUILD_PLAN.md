# Build plan and portfolio strategy

## Active roadmap — November 12, 2026

**Frontend milestone 1 is implemented locally; interaction refinement is next.** The redesign priority
comes from the owner's request after the evaluation v2 and bounded call-filtering
work merged in [PR #6](https://github.com/danielpan01/CodeImpact/pull/6), commit
`f06f72350a552722d91bd529a5ffd0b1d48cc2b5`. The detailed scope, visual direction,
delivery sequence and acceptance criteria are in [FRONTEND_ROADMAP.md](FRONTEND_ROADMAP.md).
The visual foundation and complete workspace are implemented and locally verified.
Milestones 2–3 remain planned; see VALIDATION.md for observed checks and review limits.

| Order | Milestone | What the user will notice | Completion evidence |
| --- | --- | --- | --- |
| 1 — implemented locally | Frontend foundation and complete analysis workspace | A distinct visual identity, readable typography, compact input controls, clear navigation and coordinated Map, Tests, Changes and evidence views | Real API data; inspected desktop/tablet/phone captures; 50 browser checks and 653 Python tests pass; all three evaluations unchanged |
| 2 | Graph, test list and code-review refinement | Focused dependency paths, searchable/filterable test recommendations, legible file navigation and synchronized evidence | Small and large pinned examples; selected IDs and evidence unchanged; keyboard interaction checks |
| 3 | Responsive polish and frontend release | Deliberate phone/tablet layouts, polished light/dark themes, loading/error/empty states and restrained motion | Responsive visual matrix, accessibility checks, all evaluations and CI passing; updated usage screenshots |
| 4 | Review labels and narrow Cachetools fallback | Fewer unrelated recommendations where source evidence supports exclusion | Human review status recorded; bounded LFU controls first; all three v2 baselines retained |
| 5 | Fresh evaluation and developer pilot | Evidence of behavior on unused changes and an easier workflow for another developer | Selection/labels frozen before analysis; results and usability feedback documented |
| 6 | Performance, isolation and hosted pilot | A dependable shareable service within explicit limits | Measured runtime/memory, bounded workers, access controls and deployment verification |

Milestones 1–3 form the frontend redesign program. Milestone 1 includes light tokens,
Tests-first navigation, collapsible inputs, reason-led evidence and deliberate
phone/tablet navigation. Dark theme, advanced filtering and larger-graph interaction
work remain. Deliver and validate each complete
slice before expanding it; the first slice includes a functioning workspace, not
only a visual concept or landing page. Preserve existing analyzer behavior, report
contracts, corpus bytes and all baselines throughout these frontend milestones.
Independent source-label review can proceed alongside frontend work. Known analysis
limitations remain visible; visual polish must not suggest stronger accuracy.

The following sections retain the original build strategy and historical milestone
records. Their time estimates and earlier “next” items are historical; the ordered
roadmap above is the current priority.

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
positives are removed; all 109 v2 affected labels remain selected. Current v2 is
109 TP, 284 FP, 0 FN, 166 TN, plus 13/22 uncertain selections. Both prior baselines
remain intact and `argument-guards-v1` separately records current behavior. Other
fallback evidence, graph IDs, revision paths and the scoring formula remain intact.

Next analyzer candidate, following the frontend redesign program above: bounded protocol-aware fallback narrowing for Cachetools,
starting with source-based LFU versus unrelated cache controls (136 recorded false
positives), with the descriptor/classmethod fallback (31) scoped separately. Do not
claim independent accuracy or remove uncertain IDs. Preserve all three recorded v2
measurements and obtain human label review before broader accuracy claims. Slugify's
remaining 117 fallback false positives, fixture injection and runtime imports also
remain open; the current call-path filter does not solve those mechanisms.
