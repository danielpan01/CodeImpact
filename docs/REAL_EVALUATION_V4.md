# Fresh-repository evaluation v4

The first frozen run selected **92 of 105 discovered definitions**, with
**19 true positives, 57 false positives, zero false negatives and 13 true
negatives** against the source draft. All 16 uncertain definitions were selected.
The source inventory contains another **64 definitions outside discovery**.
Independent human label review is pending.

The engine is the clean PR #22 merge, `ed728a0851e87308c0ed454071ded12adb37eda8`.
The dataset is a purposive six-change sample across previously unused
Humanize, IceCream and oyaml. Full supported Python trees, exact heads and
first parents, root MIT license notices and provenance were captured without
checking out or running upstream code. The recorded selection windows were
expanded before measurement when the original windows lacked two eligible
changes per repository. No selected case was replaced after measurement.
[Selection protocol](../corpus/real-v4/PROTOCOL.md) ·
[Candidate decisions and exact revisions](../corpus/real-v4/CANDIDATES.md)

## First measurement

| Case | Selected / discovered | TP | FP | FN | TN | Uncertain selected / total | Outside discovery |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Humanize locale grouping | 34 / 34 | 2 | 32 | 0 | 0 | 0 / 0 | 0 |
| Humanize small precise delta | 20 / 33 | 5 | 15 | 0 | 13 | 0 / 0 | 0 |
| IceCream local timestamps | 0 / 0 | 0 | 0 | 0 | 0 | 0 / 0 | 32 |
| IceCream source error message | 0 / 0 | 0 | 0 | 0 | 0 | 0 / 0 | 32 |
| oyaml contextual error | 18 / 18 | 3 | 8 | 0 | 0 | 7 / 7 | 0 |
| oyaml loader/dumper registration | 20 / 20 | 9 | 2 | 0 | 0 | 9 / 9 | 0 |
| **Overall** | **92 / 105** | **19** | **57** | **0** | **13** | **16 / 16** | **64** |

| Repository | Selected / discovered | TP / FP / FN / TN | Resolved / conservative / changed test | Outside discovery |
| --- | ---: | ---: | ---: | ---: |
| Humanize | 54 / 67 | 7 / 47 / 0 / 13 | 0 / 52 / 2 | 0 |
| IceCream | 0 / 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 | 64 |
| oyaml | 38 / 38 | 12 / 10 / 0 / 0 | 0 / 35 / 3 | 0 |
| **Overall** | **92 / 105** | **19 / 57 / 0 / 13** | **0 / 87 / 5** | **64** |

Discovery coverage is 105/169 source-shaped definitions across the six heads.
Draft-label precision is 19/76 (25%). Recall is 19/19 among known affected
discovered definitions. The two IceCream cases have undefined precision and
recall. Definitions repeated across changes contribute once per case. This
sample describes static dependency agreement for these changes and has no
observed runtime outcomes.

## What the paths showed

- **Humanize locale grouping.** All 32 draft false positives end at
  `src/humanize/__init__.py::<module>` via the importing test module.
  The changed package re-export includes the new separator helper, but
  `tests/test_filesize.py::test_naturalsize` exercises an unchanged formatting
  route. The existing `tests/test_number.py::test_intcomma` is correctly
  selected against the draft, but its evidence is also a package fallback.
  The new locale-specific test has its own changed-test path.
- **Humanize small delta.** The 15 draft false positives end at
  `tests/test_time.py::<module>`. A new parameter row gives
  `test_precisedelta_one_unit_enough` a changed-test path, while unrelated
  `test_naturaldelta` variants share the test module. Its parameter data is a
  decorator literal, distinct from the existing module-table proof.
  `test_precisedelta_bogus_call` has calls that return or raise before the
  edited loop and a separate `naturaldelta` error check.
- **oyaml contextual error.** The eight draft false positives use
  `test_oyaml.py::<module>`. For example, `test_dump` exercises a representer,
  while the edited code is the mapping constructor. The two std-dict tests
  run only under a guard that skips the custom loader registration. The new
  unhashable-key test has changed-test evidence.
- **oyaml registration.** Both draft false positives also end at the test
  module. The std-dict tests remain behind the guard that skips custom
  loader registration. Nine selected uncertainties involve external
  loader/dumper dispatch or runtime implementation checks. In the contextual
  error case, seven selected uncertainties have similar loader ambiguity.
- **IceCream coverage.** Both revisions contain conventional unittest
  `testCamelCase` method names. For example,
  `tests/test_icecream.py::TestIceCream.testNoSourceAvailable` asserts the
  changed error message, and `TestIceCream.testWithoutArgs` checks output
  containing the timestamp from the changed formatting path. Neither is
  discovered. These are concrete scope gaps. They are outside the
  confusion matrix and have no frozen metric label.

The typed validator checked the exact edges and revision intersections for
every recommendation. Selected IDs, classified IDs, original per-case evidence,
uncertain selections and the outside inventory are in the JSON report. Baseline
annotations enumerate every recorded discrepancy.

## Replay and review

```sh
make evaluate-real-v4
# reports/real-v4-evaluation.json
```

The input freeze records 33 files and 16 source hashes from the reference
commit. Before offline analysis, the gate validates the complete Git trees,
source hashes, label partition, first parents, license notices, discovery
inventory, engine and historical corpus bytes. The original stable report
replays from the frozen inputs and is pinned by `first-run.json`, SHA-256
`a30130280f6a0f6e65e60cec4a400834a610a8a094e98911e74a725dceda1712`.
The separate baseline expects the observed discrepancy and uncertainty IDs.
It does not alter the source draft or original result. Execution output
uses v4 wrapper schema 1.0 and preserves the application report schema 2.0.

Read the source-only pack before the results when reviewing labels. A reviewer
can record agreements and disagreements with pinned source spans. Review
records do not update the frozen draft, baseline or review status.
[Source-only pack](../corpus/real-v4/REVIEW.md) ·
[Human review instructions](../corpus/real-v4/REVIEW_WORKFLOW.md)

The next bounded analyzer milestone should audit `unittest.TestCase` mixed-case
method discovery, starting with the two IceCream cases. Draft labels for any
newly covered definitions before enabling the rule, protect the original
169/105/64 inventory, and add a separately versioned measurement. The Humanize
package and decorator fallback findings provide separate precision work.
[Verification results](VALIDATION.md#milestone-10--fresh-repository-evaluation-v4)
