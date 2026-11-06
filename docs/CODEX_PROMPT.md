# Copyable Codex prompt: the next vertical slice

Use this in the CodeImpact project after you review and push the starter. Select
GPT-6 Astra and Extra high in the UI if those settings are available. Model/effort
selection is a UI setting, not something this prompt can guarantee.

The prompt deliberately asks for one complete feature. Read the result and make
your own commit before moving to durable jobs, private-repo authorization or deployment.

---

Continue my CodeImpact SWE portfolio project. Work in the existing repository
`danielpan01/codeimpact`; do not create a replacement project. If this is a cloud
chat, verify that you can access the repository and its latest files before editing.
A path on my Mac is not proof that the files exist in your cloud environment.

Read AGENTS.md, README.md, docs/ARCHITECTURE.md, docs/BUILD_PLAN.md,
docs/PROJECT_CONTEXT.md and docs/VALIDATION.md. Inspect the implementation and tests.
Preserve my uncommitted work. Briefly state what is already implemented and what
this milestone will add. Then implement it, run meaningful checks, fix failures,
and provide a reviewable result.

**Milestone: paste a public GitHub PR URL and get a real explainable impact report.**

Existing architecture: Python 3.12 AST analyzer, FastAPI, Git snapshot CLI,
React/TypeScript/Vite/React Flow dashboard. It compares AST fingerprints, unions
base/head dependencies, uses reverse BFS, and ranks tests with evidence paths.
Sources are data and are never executed. Preserve the deterministic local engine
and demo while adding a separate read-only ingestion layer.

Requirements:

1. Accept an exact `https://github.com/owner/repo/pull/number` URL. Reject other
   hosts, credentials in URLs, unsupported schemes, malformed paths and arbitrary
   download URLs. Keep requests constrained to the necessary GitHub API hosts.
2. Fetch PR metadata, pin immutable head/base revisions, obtain the appropriate
   merge-base SHA, and read complete bounded Python snapshots from merge base and
   head. Support forks. Do not use only changed-file patches as the dependency graph;
   unchanged callers and tests are needed. Do not silently use a truncated tree or
   comparison response. Never check out, install or execute the analyzed repository.
3. Reuse validated Snapshot and AnalysisRequest contracts. Preserve the current
   per-file, per-snapshot and HTTP bounds, adding explicit network timeouts, bounded
   concurrency, total byte budgets and clear unsupported/too-large errors. Detect
   symlinks/submodules and explain skipped input. Preserve deletions and remove+add
   rename behavior. Handle non-UTF-8 files explicitly.
4. Keep tokens on the server. Start with public repositories and anonymous API
   access; if an optional environment token is supported, never include it in client
   code, reports, logs, screenshots or committed files. Handle rate limits with an
   actionable retry message. Do not ask me to paste a token into chat.
5. Add a typed API route and request/response schemas. Include repository identity,
   PR number, exact analyzed SHAs, merge base and analyzer version in report metadata.
   Preserve compatibility with the existing demo and snapshot upload or explicitly
   version the contract and migrate both clients.
6. Extend the dashboard with a clearly labeled PR URL form, loading/error/retry
   states, revision metadata, the existing graph and ranked tests. Keep keyboard
   access and phone layout usable. Use actual backend results; never invent graph
   nodes, completion progress or accuracy numbers.
7. Every recommendation must show a valid test-to-change dependency path. Keep
   resolved-call paths distinct from module fallbacks. Scores remain prioritization
   heuristics, not probabilities. Missing paths do not prove safety. Retain the
   warning that the full test suite remains the merge gate.
8. Add HTTP contract tests for a normal PR, fork head, deletion, pagination or tree
   truncation, rate limiting, timeout, private/404 result, invalid URL, oversized
   source and branch movement after metadata retrieval. Ensure no test runs code
   from a fetched repository. Mock network behavior deterministically; add one
   documented manual smoke test against a public PR when network access permits.
9. Add browser coverage for successful PR input and recoverable failure. Run
   `make check`, frontend formatting checks, and desktop/mobile Playwright tests.
   Add regression fixtures for any analyzer behavior you change. Do not hide
   failing checks or weaken assertions to make them pass.
10. Update architecture, setup, limitations, validation and demo instructions. Give
    me a short explanation of the new module boundaries and a reproducible example.
    Clearly distinguish completed functionality from future work.

Do not add authentication UI, payments, LLM analysis, Redis, Postgres, a GitHub App
installation flow or deployment in this milestone. Stateless ingestion is sufficient
for this bounded slice. Identify where durable background jobs will eventually fit.

I personally own all commits and pushes. Do not stage, commit, push, change Git
identity, create remote commits, open a pull request or deploy. Leave the finished
changes locally for my review, and give me the commands to commit and push myself.

Finish with: what works, what changed, checks and observed results, known limitations,
the files I should read to understand the implementation, and my next concrete step.
Do not claim an active model or reasoning setting you cannot verify.

---

For later milestones, replace the objective and acceptance tests rather than asking
Codex to rebuild the whole product. Keep the ownership and evidence requirements.

