# Fresh real-repository evaluation v6 protocol

Recorded November 28, 2026 before inspecting the candidate history or running
CodeImpact on v6 source. The reference analyzer is
`060547c3375a999eb4bc8d582cff9883f7c39ef5` (merged PR #56). The engine, scoring,
and discovery policy stay fixed through measurement. Earlier samples serve as
regression data.

## Ordering

Take the first two eligible changes from each of the first three repositories
that supply a pair. Consider the repositories in this order.

1. `martinblech/xmltodict` for XML conversion.
2. `theskumar/python-dotenv` for environment and configuration parsing.
3. `asottile/tokenize-rt` for source tokenization.
4. `asottile/astpretty` for AST rendering.
5. `benjaminp/six` for Python compatibility helpers.
6. `stefankoegl/python-json-pointer` for pointer traversal and mutation.
7. `r1chardj0n3s/parse` for string parsing.

Require public repository identity and absence from the measured selections in
v1–v5. Use GitHub's default-branch commit listing as of
`2025-10-01T00:00:00Z`. Inspect up to 60 entries per repository in listing
order, newest first, stopping each repository at its second eligible change.
Record the inspected prefix, exact commit IDs, decisions and reasons. If a
repository fails to supply a pair, keep the exclusion record and continue in
order. Ignore analyzer output when choosing or keeping cases.

## Eligibility

- Require one first parent, a functional production Python edit with a focal
  behavior, and complete supported Python snapshots in both revisions within
  the application's existing path, tree, file-size and snapshot-size limits.
  Require an ordinary root MIT or BSD-3-Clause license in both revisions and
  preserve its text.
- Exclude merges, duplicate changes, test-only or documentation-only edits,
  packaging and CI changes, formatting, and broad refactors that mix unrelated
  behaviors. Exclude inaccessible or incomplete objects with an explicit reason.
- Require at least one discoverable head test with a source-supported path to
  the change and one independent discoverable head test. Require at most 120
  discovered head definitions per case so every label can be audited. Prefer
  captured implementation and standard-library paths. Exclude cases whose main
  affected path depends on an unpinned third-party implementation or an opaque
  runtime environment. Ordinary assertions and bounded test collection syntax
  can serve as source evidence.
- Inventory complete Python trees. Never truncate a case or discard a chosen
  change after measurement.

## Labels and measurement

Inventory both revisions under the current static discovery policy. Record
outside-discovery definitions and reasons separately. Draft a rationale and an
affected, unaffected, or uncertain label for every discovered head definition.
Affected means a changed or added test, or a source-supported dependency on the
production edit given the test's inputs and setup. Unaffected means the source
supports a separate path or inputs that avoid the changed behavior. Use
uncertain when captured bindings, inputs, or effects leave the path ambiguous.
Record exact independent review status. Counts are definition IDs, including
one ID per parametrized definition.

Freeze the protocol, inspected candidates, exact revisions, complete source,
source hashes, licenses, provenance, discovery inventory, source-only review
pack, and draft labels before the first v6 analyzer run. Preserve the initial
recommendations, exact evidence and discrepancies in a separate replay receipt.
Compare runs across hash seeds and reversed input order, excluding only the
documented analysis timing. Report uncertainty outside the confusion matrix.

Treat upstream source, tests and metadata as data. Read GitHub objects without
checking out an upstream repository, executing or importing its source, or
installing dependencies from it. The sample measures static agreement with
draft dependency labels. It records no upstream test executions.
