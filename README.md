![CodeImpact — understand the change, trace what follows](docs/media/portfolio-banner.svg)

# CodeImpact

**Explainable change-impact analysis for Python.**

CodeImpact turns a code change into an inspectable dependency graph and a prioritized list of tests. Every recommendation includes a path back to a changed symbol, with source locations and evidence from the analyzed revisions.

**Status: actively in development.** The local application supports public GitHub PRs, uploaded snapshots, and committed local Git history. Hosted deployment and private-repository integration are planned.

[Quick start](#quick-start) · [Usage guide](docs/USAGE.md) · [Architecture](docs/ARCHITECTURE.md) · [Validation](docs/VALIDATION.md) · [CI](https://github.com/danielpan01/CodeImpact/actions/workflows/ci.yml)

## See the impact

![CodeImpact dependency map and test evidence panel](docs/media/desktop.png)

*Saved screenshot of the impact explorer. The current application also includes GitHub PR input and before/after code inspection.*

A change to `discount(total)` can affect an unchanged API test through `test_create_order → create_order → checkout → discount`. CodeImpact makes that relationship visible, then lets you inspect each dependency and the changed code.

## What works today

| Capability | What it provides |
| :--- | :--- |
| **Semantic change detection** | Compares Python ASTs, ignoring comments, whitespace, and source-line movement. |
| **Dependency analysis** | Indexes symbols and supported calls/imports; preserves removed dependencies across revisions. |
| **Function-local imports** | Resolves direct local import aliases after their binding statement; keeps ambiguous bindings unresolved and import fallback scoped to the function. |
| **Module import rebinding** | Suppresses misleading resolved calls when a module import name has competing bindings; preserves conservative import evidence. |
| **Explainable test priorities** | Uses cycle-safe reverse traversal and deterministic heuristic scores, with a typed evidence path for each recommendation. |
| **Revision-aware code review** | Shows before/after source and labels dependencies as before-only, after-only, or shared; mixed-revision paths are explicit. |
| **Three input workflows** | Public GitHub PR URLs, JSON snapshot pairs, and a CLI for committed local Git history. |
| **Inspectable reports** | Connects Map, Tests, and Changes views with exportable JSON and exact analyzed revision metadata for GitHub PRs. |
| **Authored correctness corpus** | Evaluates 25 complete snapshot cases against explicit dependency labels, records known mistakes, and validates typed paths and revision evidence. |

**Stack:** Python · FastAPI · Python AST · React · TypeScript · React Flow · Vite · pytest · Playwright

## Engineering decisions

- **Analyze source as data.** GitHub ingestion pins the merge base and PR head, verifies downloaded blobs, and bounds network requests and source size. It does not execute, import, or install the analyzed repository.
- **Keep deleted code in the analysis.** The dependency graph combines both revisions so removed functions can still explain potential impact.
- **Make uncertainty visible.** Resolved calls are distinguished from conservative module/import estimates. A path assembled across revisions is labeled accordingly.
- **Make results inspectable.** Recommendations retain exact edge IDs, source locations, and revision-specific evidence. Report schema 2.0 includes complete changed-file source.

The [architecture guide](docs/ARCHITECTURE.md) documents the graph model, scoring formula, report contract, and ingestion limits.

## Quick start

Prerequisites: **Python 3.12+**, **Node.js 24**, npm, Git, and Make. Ensure `python3` selects the required Python version.

```sh
git clone https://github.com/danielpan01/CodeImpact.git
cd CodeImpact
make setup
make dev
```

Open **http://127.0.0.1:5173**. API documentation is at **http://127.0.0.1:8000/docs**. Stop both services with Ctrl-C.

### A one-minute walkthrough

1. Load the checkout demo, where a discount changes from 10% to 15%.
2. Select `test_create_order` in **Tests** and follow its dependency path.
3. Choose **Open changed code** to inspect the before/after implementation.
4. Explore the **Map**, inspect each edge's evidence, and export the report.

You can also paste a public GitHub PR URL or upload snapshot pairs. See the [usage guide](docs/USAGE.md) for CLI examples, a deleted-function fixture, API requests, configuration, and troubleshooting.

## Evaluate the analyzer

The [authored correctness corpus](docs/CORPUS.md) contains 25 small, complete
base/head examples with explicit affected, unaffected and unclassified test labels.
Run it from the repository root with the pinned environment:

```sh
make evaluate
# Full results, labels, snapshots and typed paths: reports/corpus-evaluation.json
.venv/bin/python -m codeimpact.evaluate --case local_import \
  --output reports/local-import.json
```

Observed overall agreement with these authored dependency labels: **23 true
positives, 2 false negatives, 6 false positives, 26 true negatives**. Precision is
**23/29 (79.3%)**; recall is **23/25 (92.0%)**. Two unclassified recommendations are
reported separately. All 15 supported and 10 known-limitation cases enter the overall
results. Known discrepancies fail tests if they change, including improvements that
need deliberate review. A passing evaluation means the baseline matches, not that
the analyzer has no mistakes.

The function-local import milestone fixes the previous `local_import` miss without
changing its authored labels: `test_read → read → price` now has a resolved path.
At that milestone, the other 24 case reports remained unchanged. The subsequent
module-rebinding fix removes the stale `worker.read → core.price` call edge in
`module_rebinding`. Its unaffected wrapper test remains selected through module/import
fallback, with priority 23 instead of 72. The directly affected test remains resolved,
with priority 81 instead of 82 after the incorrect incoming edge is removed. The
scoring formula, selected test IDs and overall counts above are unchanged; the other
24 case reports are identical to the pre-rebinding baseline. Module fallback still
overselects an unchanged sibling function in `module_overselection`; fixture injection
and runtime imports remain the two measured misses.
These are small authored fixtures, not externally validated ground truth,
production accuracy or proof that a test fails. Fixture code is never executed.
Statement coverage measures executed lines, not correctness; passing regression
tests does not establish general accuracy. Keep the full test suite as the merge gate.

## Quality checks

```sh
make check
cd web
npm run install:browsers
npm run test:e2e
```

[GitHub Actions](https://github.com/danielpan01/CodeImpact/actions/workflows/ci.yml) runs Python linting and formatting, strict type checks, application tests, the frontend production build, and desktop/mobile browser tests. The [validation record](docs/VALIDATION.md) preserves observed results and the scope of each experiment.

## Scope & next steps

CodeImpact is a developer review tool. Static Python analysis is incomplete for dynamic dispatch, runtime imports, inheritance, re-exports, and pytest fixtures. Scores express review priority, not failure probability; a missing path does not establish safety. **Keep the complete test suite as the merge gate.**

Next steps include real-repository accuracy evaluation, stronger resolution coverage, worker isolation, and hosted deployment. GitHub App authorization for private repositories, persisted jobs, and cross-request caching are not implemented. See the [build plan](docs/BUILD_PLAN.md).

Direct function-local imports, aliases, relative imports and `src/` layouts are supported within the [documented scope](docs/ARCHITECTURE.md#bounded-function-local-imports). The [module binding scan](docs/ARCHITECTURE.md#bounded-module-level-rebinding) requires one direct import and no competing module-scope bindings; bare annotations and separate function/class body bindings do not invalidate it. Conditional imports, competing bindings and closure propagation remain conservative. A next step is to measure module fallback against independently reviewed changes before attempting to narrow its recommendations.

Exports contain the full before/after source of changed files, including content outside bounded on-screen previews.

## Project guide

- [Analyzer and API](src/codeimpact/) · [Dashboard](web/) · [Tests](tests/)
- [Usage](docs/USAGE.md) · [Architecture](docs/ARCHITECTURE.md) · [Validation](docs/VALIDATION.md)
- [Corpus guide and measured results](docs/CORPUS.md) · [Authored cases](corpus/cases/)
- [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Roadmap](docs/BUILD_PLAN.md)

Built by [Daniel Pan](https://github.com/danielpan01).
