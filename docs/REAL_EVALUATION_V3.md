# Fresh evaluation v3

Implemented locally November 14, 2026, against the unchanged analyzer from merged
[PR #10](https://github.com/danielpan01/CodeImpact/pull/10),
`25b58040ede56918755a6a83277de98408f3dcb9`. Six unused source changes from three
previously unused repositories were selected and labeled before the first analysis.
The complete supported Python trees, 90 source-derived draft labels, discovery
audit and review pack were frozen first. No analyzer tuning followed measurement.

```sh
make evaluate-real-v3
# reports/real-v3-evaluation.json
make pilot
# reports/developer-pilot/{inflection_title,ordered_set_pop}.json
```

## First measurement, preserved

| Case | Selected / discovered | TP | FP | FN | TN | Outside discovery |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Inflection rule tables | 22 / 22 | 6 | 16 | 0 | 0 | 0 |
| Inflection titleize | 22 / 22 | 1 | 21 | 0 | 0 | 0 |
| PyISO8601 validator errors | 2 / 8 | 2 | 0 | 0 | 6 | 0 |
| PyISO8601 validator addition | 8 / 8 | 2 | 6 | 0 | 0 | 0 |
| Ordered Set pop index | 0 / 0 | 0 | 0 | 0 | 0 | 30 |
| Ordered Set syntax repair | 30 / 30 | 30 | 0 | 0 | 0 | 0 |
| **Overall** | **84 / 90** | **41** | **43** | **0** | **6** | **30** |

Draft-label precision is **41/84 (48.81%)**; recall is **41/41 (100%)** among
discovered definitions. There are zero uncertain labels in this sample. The 30
outside-discovery definitions are separate, not negatives or uncertain labels.
Recall and precision for the pop case are **undefined (0/0)**. Zero labeled misses
does not establish safety: the filename discovery gap includes a direct `test_pop`
call. No tests, dependencies or upstream setup scripts were executed.

Repository totals: Inflection 7 TP / 37 FP / 0 FN / 0 TN, 44/44 selected;
PyISO8601 4 TP / 6 FP / 0 FN / 6 TN, 10/16 selected;
Ordered Set 30 TP / 0 FP / 0 FN / 0 TN, 30/30 discovered definitions selected,
with the other change's 30 definitions outside discovery.

## Findings and boundaries

- Changed module data retains broad fallback: Inflection contributes 37 false
  positives; adding/exporting the ISO validator contributes six. All 43 remain
  explicitly recorded. A resolved call is distinguished from module/import fallback.
- The syntax-repair case restores a module that cannot parse at the base revision.
  Its 30 labels concern import/loadability. Newly indexed head calls produce
  resolved paths; this is not 30 independently demonstrated runtime failures.
- The older Ordered Set tree stores tests in `test.py`. The existing filename rule
  discovers none. The dashboard now distinguishes **No tests discovered** from
  **No tests recommended**, explains the supported names and leads into changed code.
  The analyzer's discovery behavior is unchanged.
- Each repository contributes two historical changes; repeated tests,
  small-library selection and shared module effects limit generalization. The
  sample is purposive, not a random production benchmark or failure prediction.

[PROTOCOL.md](../corpus/real-v3/PROTOCOL.md) records the selection policy and the
pre-analysis exclusion of HTTMock for its unsupported corpus license. The replacement
Inflection cases, all considered candidate exclusions, exact first-parent/head
revisions, Git tree/blob integrity receipts and per-revision MIT notices remain
in the [dataset](../corpus/real-v3/README.md). Both malformed original source and
test-discovery gaps were retained. No tree was trimmed to improve results.

## Receipts and regression behavior

The freeze pins 31 input files and nine engine files. `first-run.json` records
all first selected IDs, classifications, counts, analysis hashes, the first full
report hash and the three initial false-positive discrepancy failures. A separate
`baseline.json` explains those observed mistakes; original cases and labels are
unchanged. Replay validates exact bytes, complete source/provenance, licenses,
discovery inventory and every typed evidence path. Changed measurements, labels,
engine code or historical corpus files fail; there is no automatic baseline rewrite.

The new wrapper uses `holdout_evaluation_schema_version: "1.0"`; analysis 2.0,
dataset/evaluation 1.0 and v2 wrapper 4.0 are unchanged. All 72 pre-existing corpus
files and all three prior stable evaluation reports remain byte-identical, including
v2's first-run, partial, argument-guard and mapping baselines. The only new online
capture capability is recognizing an ordinary root `MIT-LICENSE`; ambiguous and
symlink licenses still fail. Replay and CI do not access GitHub.

Hashes provide recorded integrity, not independent proof of labeling order or
correctness. These cases are now regression data. Source-label review is still
**pending**, with 90 unchecked label entries plus 30 outside-discovery entries in
the [review pack](../corpus/real-v3/REVIEW.md). Future label changes require a new
review record, not edits to the frozen originals.

## Developer pilot

The owner **deferred the human pilot on November 14, 2026**. The
[walkthrough and blank feedback record](DEVELOPER_PILOT.md) are prepared. Browser
checks cover the analyze → test → evidence → changed-code flow and discovery-limit
recovery; they do not substitute for participant observations. No human usability
result, execution benchmark, hosting or new infrastructure is claimed.

See [VALIDATION.md](VALIDATION.md) for observed checks. Milestone 6 has completed
performance measurement, bounded workers and local deployment verification. Live
hosting remains explicitly deferred; see the current [build plan](BUILD_PLAN.md).
