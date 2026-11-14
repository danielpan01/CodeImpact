# Fresh evaluation v3: pre-analysis protocol

Established November 14, 2026, before selecting or analyzing any v3 case.
Reference engine: `25b58040ede56918755a6a83277de98408f3dcb9` (merged PR #10).

Select two functional Python changes each from `micktwomey/pyiso8601`,
`patrys/httmock` and `rspeer/ordered-set`. These repositories are outside the
authored/v1/v2 evaluation inputs. They offer small, inspectable date parsing,
HTTP mocking and collection implementations. This is a purposive sample with
small-library and localized-change bias, not a random or production benchmark.

Inspect recent commit metadata and source diffs, moving backward to find two
bounded functional changes per repository. Exclude release/packaging, documentation,
CI-only and test-only commits, duplicate merge copies, broad unrelated refactors,
unsupported licenses and incomplete or oversized supported trees. Record actual
candidate exclusions. Use exact head/first-parent revisions and existing input
limits. Never trim a tree or replace a case because of analyzer results.

Capture complete supported Python trees as JSON strings with Git tree/blob receipts
and original license notices. Do not clone, check out, execute, import or install
upstream source. Inspect source and independently apply the existing static
test-definition discovery rule. Label every discovered head test before the first
analysis: affected, unaffected or uncertain, with a source rationale. Affected means
a dependency on an edited callable/default, not an observed failing assertion;
changed/new tests are affected themselves. Parameter variants share a definition ID.
Imports alone do not establish that every imported method is used. Retain unknown
fixture, decorator, inheritance, external-library and dynamic behavior as uncertain.

Before measurement, freeze the selection, cases, provenance, source-only review pack,
engine hashes and protocol. Labels remain agent drafts until a real reviewer
provides a dated review reference. Human review and developer-pilot status must be
reported honestly; an agent walkthrough does not constitute a human pilot.

Run the unchanged reference engine once after the freeze. Preserve the complete
first measurement and its empty-discrepancy drift before separately annotating the
observed mistakes. Never alter frozen labels to match output or tune the engine
within this milestone. Keep every uncertain definition in the inventory, including
unselected ones. Report per-case/repository and overall counts and valid evidence,
without pooling historical datasets or treating repeated tests as independent samples.

Preserve every historical corpus file and stable authored/v1/v2 report byte. Add a
separate offline replay gate with explicit receipts and documented schema boundaries.
Receipt hashes attest to recorded integrity, not independent authorship or timing.

For the developer pilot, prepare reproducible snapshot inputs and a short
analyze → test → evidence → changed-code walkthrough. Record actual participant
feedback only when received. Keep independent source-label review separate from
usability feedback, and retain pending/deferred status when participation is absent.

## Eligibility update before capture/analysis

Source inspection found that HTTMock's pinned LICENSE declares Apache-2.0, outside
the existing corpus's MIT/BSD-3-Clause allowlist. Exclude both considered HTTMock
changes on that basis; do not expand the license contract in this milestone.
Its `tests.py` naming also lies outside the current discovery rule and is recorded
as an inspection finding, not an analyzed result. Use `jpvanhal/inflection` as the
replacement third candidate repository, subject to the same pre-analysis checks.
No candidate has been analyzed and no measured result informed this substitution.

The owner explicitly deferred the human developer pilot on November 14, 2026.
Prepare the walkthrough and record that status; do not invent participant feedback.
Independent source-label review remains pending separately.

## Source-inspection clarification before measurement

The final sample includes module initialization and table-data dependencies in
addition to edited callables/defaults. A syntax repair can affect all tests whose
module import depends on the repaired file. Table readers are affected even when
a specific input does not match the new rule; statically evident early returns
before the table are unaffected. Preserve these distinctions in each rationale.

Retain the older Ordered Set `test.py` case with zero discovered definitions and
list its 30 test-shaped functions separately. This selection was not replaced.
Only discovered definitions receive the three-way metric labels; outside-discovery
functions are not counted as negatives, misses or uncertain definitions. Report
that denominator limitation alongside the metrics. Record no inferred runtime
collection, output failures, timings or developer feedback.
