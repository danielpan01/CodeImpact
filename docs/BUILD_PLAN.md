# Build plan and portfolio strategy

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

Add a labeled fixture corpus for imports/re-exports, fixture injection, conditional
definitions, nested scopes, class dispatch and module rebinding. Start by recording
unsupported cases explicitly. Improve one resolution rule at a time with regression
tests. Add source revision provenance to edges so the UI can distinguish base/head.
Add worker-level resource budgets for adversarial ASTs and performance measurements.

Acceptance: no recommendation lacks a valid edge-by-edge path. Publish supported
and unsupported case tables. Compare conservative module-only selection against
symbol-level selection instead of assuming finer graphs are always better.

## 3. Real GitHub PR input (2–3 days)

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

Evaluate a fixed, documented set of Python changes with human labels and, where
practical, mutation tests. Run trusted fixture code only in a separate controlled
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
