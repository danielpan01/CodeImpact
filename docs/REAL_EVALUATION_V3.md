# Fresh evaluation v3

Implemented locally November 14, 2026, against the unchanged analyzer from merged
[PR #10](https://github.com/danielpan01/CodeImpact/pull/10),
`25b58040ede56918755a6a83277de98408f3dcb9`. Six unused source changes from three
previously unused repositories were selected and labeled before the first analysis.
The complete supported Python trees, 90 source-derived draft labels, discovery
audit and review pack were frozen first. No analyzer tuning followed measurement.

```sh
make evaluate-real-v3
# reports/real-v3-parameter-tables-v1-evaluation.json (current)
# reports/real-v3-evaluation.json remains the preserved original
make pilot
# reports/developer-pilot/{inflection_title,ordered_set_pop}.json
```

## Current measurement — milestone 9C test parameter tables

The titleize case selects **2/22**, down from 22/22, with
**1 TP / 1 FP / 0 FN / 20 TN**. Its resolved titleize call path and the
conservative mutation/cleanup path retain their exact evidence. The 20
removed paths came from the changed test module.

Expanded v3 selects **47/120** with **42 TP / 5 FP / 0 FN / 61 TN**.
All 12 uncertain definitions stay unselected. Only the titleize case changes.
Holdout wrapper **8.0** verifies the `parameter-tables-v1` measurement and
the preserved `additive-exports-v1` and earlier receipts.
[Exact IDs, source proof and retained evidence](PARAMETER_TABLE_REVIEW.md)

## Preserved measurement — milestone 9C additive package exports

The validator addition selects **4/8**, down from 8/8. The two changed tests
retain their exact evidence. Four plain tests using existing explicit members
lose their package fallback. Two Hypothesis tests retain it because decorated
execution is outside the proof. The case is **2 TP / 2 FP / 0 FN / 4 TN**.

Expanded v3 selects **67/120** with **42 TP / 25 FP / 0 FN / 41 TN**.
All 12 uncertain definitions stay unselected. The other five analysis hashes
match the literal-table receipt. Holdout wrapper **7.0** verifies
`additive-exports-v1` and its predecessor chain.
[Exact IDs, evidence and source boundaries](VALIDATOR_EXPORT_REVIEW.md)

## Preserved measurement — milestone 9C literal rule tables

The Inflection rule case selects **8/22**, with **6 TP / 2 FP / 0 FN / 14 TN**.
Its six affected definitions remain selected. Fourteen unrelated tests lose
both production and test-table fallback contributions. Four retained paths now
use existing production evidence and receive the existing distance-based score.
[Exact IDs, source proof and path comparison](MODULE_DATA_REVIEW.md)

Expanded v3 selects **71/120**, with **42 TP / 29 FP / 0 FN / 37 TN** and all
12 uncertain definitions unselected. The other five v3 analyses match their
prior hashes, including titleize and both PyISO8601 cases. All six v2 analyses
also match their predecessors. Holdout wrapper **6.0** verifies the new
`literal-tables-v1` measurement and its `legacy-dispatch-v1` predecessor.

The original 90-definition result, excluded inventory and all labels remain
frozen. Every normal replay validates the history and fails on unexpected drift.

## Preserved engine replay — milestone 9B legacy dispatch

Holdout wrapper 5.0 links `descriptor-binding-v1` through the new
`legacy-dispatch-v1` receipt. The complete six-case expanded measurement,
discovery inventory and draft labels match. [Source and measurements](SLUGIFY_FALLBACK_REVIEW.md)

## Preserved engine replay — milestone 9B descriptor binding

The `descriptor-binding-v1` receipt reproduces all six expanded analyses
and their measurements, labels, annotations and discovery inventory. Holdout
wrapper 4.0 links `lfu-callback-v1` directly. The original 90-definition
denominator and outside-discovery inventory remain independently preserved.
[Descriptor measurement and receipts](DESCRIPTOR_REFINEMENT_REVIEW.md)

## Preserved engine replay — milestone 9A

The full expanded measurement below remains identical, including all six stable
analysis hashes. New `baselines/lfu-callback-v1.json` records the new mapping engine
hash, links the preserved discovery baseline and the new v2 receipt, and retains
the original labels, annotations and discovery audit. Holdout wrapper **3.0** adds
an explicit previous-baseline link; application report 2.0 is unchanged. Both
original and discovery-era report filenames are preserved. See
[the bounded LFU refinement](LFU_CALLBACK_REVIEW.md).

## Preserved discovery extension — milestone 7

Literal `test.py` is now supported. The separate `test-discovery-v1` label draft
was created before expanded analysis: 1 affected, 17 unaffected, 12 uncertain.
The expanded milestone 7 run selects **85/120** definitions: **42 TP / 43 FP / 0 FN / 23 TN**,
with **12 uncertain definitions, none selected**. Only `test_pop` is newly selected
via conservative module/import evidence. The other five analysis hashes are
unchanged. The old 90-definition denominator and 30 exclusions remain explicit
in the current holdout wrapper **2.0**; the original wrapper **1.0** and all frozen
inputs/labels/provenance/baselines stay untouched. No discovery gap is silently
reclassified as an unaffected test. See [policy, receipts, exact paths and review
status](TEST_DISCOVERY.md). The original milestone 5 findings below are historical.

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

## First-measurement findings and boundaries

- Changed module data retains broad fallback: Inflection contributes 37 false
  positives; adding/exporting the ISO validator contributes six. All 43 remain
  explicitly recorded. A resolved call is distinguished from module/import fallback.
- The syntax-repair case restores a module that cannot parse at the base revision.
  Its 30 labels concern import/loadability. Newly indexed head calls produce
  resolved paths; this is not 30 independently demonstrated runtime failures.
- The older Ordered Set tree stores tests in `test.py`. The original filename rule
  discovered none (milestone 7 now supports this exact filename). The dashboard now distinguishes **No tests discovered** from
  **No tests recommended**, explains the supported names and leads into changed code.
  At that milestone the analyzer’s discovery behavior was unchanged; see the
  separate milestone 7 expansion above.
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
