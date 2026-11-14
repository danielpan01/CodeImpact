# Fresh source evaluation v3

Six previously unused commit/first-parent pairs across PyISO8601, Inflection and
Ordered Set. The selection is purposive and historical (2019–2022), not a random
sample of recent changes. Each repository contributes two changes; repeated test
definitions and closely related changes are not independent samples.

Read [PROTOCOL.md](PROTOCOL.md) and [REVIEW.md](REVIEW.md) before results.
All 90 discovered head definitions have source-derived, agent-drafted labels:
41 affected, 49 unaffected, zero uncertain. Independent label review is pending.
No upstream code, test suite, installation script, or pickle payload was executed.
All Python source remains JSON string data. Complete supported source trees, Git
object receipts and both original license notices are retained; see
[ATTRIBUTION.md](ATTRIBUTION.md).

## Discovery is part of the result

The audit in `discovery.json` also inventories test-shaped functions outside the
existing filename/definition discovery rule. `ordered_set_pop` has 30 such
functions in `test.py`, including `test_pop`, but zero discovered definitions.
They are outside the metric denominator, not true negatives or uncertain labels.
Zero discovered tests cannot establish recall or safe test skipping. The case
stays in the six-case inventory. AST parsing failures likewise limit this audit;
this is not pytest collection or a runtime coverage claim.

`ordered_set_syntax` repairs an invalid f-string in the base module. Its 30 affected
labels refer to the module's ability to load, including direct test imports and
helpers using OrderedSet. They do not assert every test reaches `update` or fails
at runtime. Inflection rule-table labels distinguish table readers from unchanged
helpers and statically evident early returns. Function/table dependency does not
mean every parameter executes an edited branch. There are no source-ambiguous
labels in this small sample; that does not remove the discovery gap.

## Freeze and replay

Before the first analyzer invocation, `frozen-inputs.json` pins every case,
provenance record, selection, protocol, this document, review pack, discovery audit,
license copy and preservation receipt, plus the nine engine files from merged
PR #10 (`25b58040ede56918755a6a83277de98408f3dcb9`). Hashes record integrity;
they are not independent attestation of authorship or timing.

The subsequent `first-run.json` retains the first report hash, complete stable
measurement (IDs, counts and analysis hashes) and initial discrepancy failures.
`baseline.json` separately annotates the observed mistakes without editing any
frozen source or label. `make evaluate-real-v3` validates receipts before analysis,
checks every typed evidence path and compares the full stable measurement.
A passing replay preserves known mistakes; it does not mean perfect accuracy.
There is no automatic rebaseline option. Changes require explicit review and a
separate receipt, leaving the original files intact.

The wrapper adds `holdout_evaluation_schema_version: "1.0"`. Dataset/evaluation 1.0,
analysis 2.0 and the existing v2 wrapper remain unchanged. `elapsed_ms` is excluded
from stable analysis hashes. Historical corpus files and authored/v1/v2 report
hashes are pinned in `preservation.json`; regression tests replay the old reports.
No machine or latency benchmark is claimed by this milestone.

## Review and pilot status

Independent source-label review: **pending**. Review checkboxes remain unchecked.
Corrections need a separately versioned record; do not rewrite frozen labels.

Human developer pilot: **deferred by the owner on November 14, 2026**. Prepared
walkthrough materials do not constitute user feedback or a completed pilot.
See [the developer walkthrough](../../docs/DEVELOPER_PILOT.md). Evaluation findings
and any automated dashboard checks are distinct from human usability evidence.
