# CodeImpact fresh real-repository evaluation v6

Six source changes from three repositories unused in CodeImpact v1–v5.
The reference engine is the merged `060547c` revision. No upstream
code or tests were run.

- [Protocol](PROTOCOL.md) records the selection and label rules agreed before
  candidate inspection.
- [Candidate decisions](CANDIDATES.md) lists every inspected commit and why it
  was chosen or excluded. [Machine-readable decisions](candidates.json) and
  [selected revisions](selection.json) retain the full IDs and first parents.
- [Source-only review pack](REVIEW.md) links each label to the pinned test and
  shows the production and test diffs without recommendation output.
- [Analyzer hash inventory](analyzer.json) records the files read from the
  reference commit. [Frozen inputs](frozen-inputs.json) pins every source,
  provenance record, label, license, and source-only review artifact.
- [Observed results](../../docs/REAL_EVALUATION_V6.md) explains the separate
  first-run and replay receipts.

All 399 discovered head definitions have source-based draft labels. Independent
label review is pending. The reviewer and review-reference fields are empty.
To review, read the protocol, then check the source spans and rationale in
the review pack before looking at results. Record disagreements separately
from these frozen files.

The XML cases distinguish deliberately exercised declaration handling from
ordinary element parsing, explicit opt-in parsing, and serialization.
The dotenv cases separate a changed entry guard and interactive search from
explicit-file calls and utilities. Runtime environment, subprocess, or
external-shell behavior is uncertain where source does not pin the relevant
effects. The tokenizer cases distinguish the edited token-kind or brace
transformation from unrelated source and token utilities. Python-version
skips are recorded as source context. Counts use statically discovered
definition IDs, regardless of runtime collection. Outside-discovery IDs
remain separate from classified or uncertain discovered definitions.

Run `make evaluate-real-v6` from the project root for the offline replay.
