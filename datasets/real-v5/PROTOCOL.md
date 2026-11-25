# Fresh real-repository evaluation v5 protocol

Recorded November 24, 2026 before candidate inspection and analysis. The
reference analyzer is CodeImpact `06f8a31b2435f95d5f3b0bbc6b4b70efd1c108b7`
(merged PR #36). The owner chose to skip human label review. Labels are
source-based drafts.

## Ordering

Take the first two eligible changes from each of the first two repositories
that supply a pair. Consider repositories in this order.

1. `stefankoegl/python-json-pointer` for pointer traversal and parsing.
2. `pydanny/cached-property` for descriptor and cache behavior.
3. `python-semver/python-semver` for version parsing and comparison.
4. `mahmoud/boltons` for general-purpose Python helpers.

Each repository must be public and absent from the measured v1–v4 selections.
Use the default-branch GitHub listing at or before `2025-01-01T00:00:00Z`.
Inspect the first 60 entries newest first, in the returned order. Stop a
repository at its second eligible change. If it has fewer than two, record
the exclusions and move to the next repository. Record the inspected prefix,
exact heads, first parents for selected cases, and source eligibility reasons.
Do not use analyzer output to choose cases.

## Eligibility

- Require a single-parent functional production Python change, complete trees
  of supported Python files within the application snapshot limits, and an
  ordinary supported root MIT or BSD-3-Clause license in both revisions.
- Omit merges, duplicate changes, packaging or CI changes, documentation or
  test-only changes, formatting, and broad unrelated refactors.
- Require a source-traceable affected head test and at least one independent
  discovered head test. Prefer relevant dependency paths contained in the
  captured source and Python standard library. Exclude a change when establishing
  its main affected path requires an unpinned external implementation, plugin,
  or opaque execution environment. Ordinary test assertion and parametrization
  syntax can serve as source evidence. Record any remaining uncertainty
  explicitly rather than inferring runtime behavior from a test name.

## Freeze and replay

Inventory both revisions under the current static discovery policy. Record
outside-discovery definitions separately. Draft an affected, unaffected or
uncertain label and a source rationale for every discovered head definition.
Use the captured call, binding, setup and input when deciding dependency
relevance. A changed or new test is affected. An unchanged test may reach an
edit even if its particular assertion still passes. Definition counts do not
include individual parameters or inherited test executions.

Freeze the case order, selection decisions, full source snapshots, first
parents, license bytes, capture receipts, definitions, draft labels, and
reference analyzer hashes before the first recommendation run. Retain every
selected case and label after measurement. Publish a separate gate for the
exact first-run report, recommendation evidence, and observed discrepancies.

Treat upstream source and metadata as data. Never check out an upstream
repository, execute or import its files, or install its dependencies. This
purposive sample measures static agreement with draft dependency labels.
