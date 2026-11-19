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

## Mixed-case unittest successor

`unittest-discovery-v1` replays the same six snapshot pairs under
`test-files-v3`. In each IceCream case, both revisions have unchanged test
sources with one direct `import unittest` per relevant file, 30
`TestIceCream` methods and two `TestIceCreamInstall` methods. The newly
discovered and selected ID sets are identical for both cases. The 32 exact
IDs per case, head line spans and individual source rationales are in the
separate draft label receipt. Its pre-analysis SHA-256 is
`c4f3b20d9b148b6fb3f42c56d2ad9e55a868b8ea2ccc1df305e4c4784e31b691`.
[Frozen successor draft labels](../corpus/real-v4-successors/unittest-discovery-v1/labels.json)

The timestamp change replaces `datetime.utcnow()` with `datetime.now()`
in `_formatTime`. Seven tests exercise enabled zero-argument output.
Argument-only formatting tests bypass that branch. The source-error change
edits `NoSourceAvailableError.infoMessage`, which `testNoSourceAvailable` checks.
Other error or stack-sensitive cases can depend on external source inspection
or dynamic setup. Both installation methods in both cases remain uncertain
because the assertions involve shared runtime builtins state.

| Replay or case | Source-shaped | Discovered | Selected | Outside | TP | FP | FN | TN | Uncertain selected / unselected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Frozen v4 | 169 | 105 | 92 | 64 | 19 | 57 | 0 | 13 | 16 / 0 |
| Successor IceCream timestamp | 32 | 32 | 32 | 0 | 7 | 22 | 0 | 0 | 3 / 0 |
| Successor IceCream source error | 32 | 32 | 32 | 0 | 1 | 26 | 0 | 0 | 5 / 0 |
| Successor IceCream total | 64 | 64 | 64 | 0 | 8 | 48 | 0 | 0 | 8 / 0 |
| Successor v4 | 169 | 169 | 156 | 0 | 27 | 105 | 0 | 13 | 24 / 0 |

All 64 new recommendations have conservative module/import evidence present
in both revisions. In each case, 31 paths run from the method through its
test module, `icecream/__init__.py::<module>` and the changed
`icecream/icecream.py::<module>`. The remaining method, `testDifferentName`,
imports `ic` inside its body and starts its path directly at the package
module after the test. The successor has 151 conservative, five changed-test
and zero resolved-call recommendations. The four non-IceCream v4 cases
retain identical stable analyses, selections and outcomes.

```sh
make evaluate-real-v4            # reports/real-v4-evaluation.json
make evaluate-real-v4-unittest   # reports/real-v4-unittest-discovery-v1-evaluation.json
```

Both targets run offline in CI. The first preserves the original inventory,
labels, source-only review pack, first measurement and report. The successor
validates the exact label overlay, evidence and classification against its
own receipt. Its JSON report lists the selected IDs, revision paths,
uncertainties and all prior and current discovery counts. Independent label
review remains pending for both versions. Review the successor labels against
the same pinned source spans and record proposed revisions separately.
[Successor baseline](../corpus/real-v4-successors/unittest-discovery-v1/baseline.json)
· [Discovery boundaries](TEST_DISCOVERY.md#mixed-case-unittest-methods)
· [Verification](VALIDATION.md#mixed-case-unittest-discovery)

## IceCream timestamp successor

The reference replay before the refinement selects all 32 timestamp tests.
The pinned change has three displayed symbols. The body of
`IceCreamDebugger._formatTime` changes from `datetime.utcnow()` to
`datetime.now()`. The enclosing class fingerprint changes with the method,
but its initialization and method headers stay identical, so the class is
display-only. Swapping the adjacent `datetime` and `contextlib` imports
changes the module outline and gives it an independent propagation seed.
All 32 original recommendations use that seed. The edited method also has
its own seed.
[Pinned source pair](../corpus/real-v4/cases/icecream_local_time.json)

In both revisions, the package initializer re-exports `ic` from its
implementation module using a wildcard. The implementation binds a singleton
`ic = IceCreamDebugger()`. The test setup changes `ic._pairDelimiter` and
the output context managers can replace and restore callbacks and streams.
The instance's `__call__` and `format` forward positional arguments to
`_format`. That method calls `_formatTime` only from `if not args`, so an
ordinary bound call with an argument bypasses the timestamp on that route.

The proof can follow this pattern in closed source with a unique instance
binding, passive imports and modeled lifecycle. It excludes the nonempty-only
synthetic test and retains empty calls, mixed calls and an independent changed
dependency. It declines the pinned IceCream module contribution in both
revisions. The argument count alone does not settle these effects:

- The test module conditionally binds `StringIO`, and the package uses a
  wildcard import and dynamically reads a version file into its namespace.
- The implementation calls the external `executing.Source` through a frame
  object before the guard. The argument branch also reads source through that
  dependency. The frozen snapshots do not contain that implementation.
- Context-managed callback changes, formatting and output add further
  dependencies in some tests. In the installation tests the binding also
  depends on builtins state. The source-error branch and `testNoSourceAvailable`'s
  dynamic call retain their existing evidence.

| Timestamp replay | Selected | TP | FP | FN | TN | Uncertain selected / unselected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `unittest-discovery-v1` | 32/32 | 7 | 22 | 0 | 0 | 3 / 0 |
| `variadic-dispatch-v1` | 32/32 | 7 | 22 | 0 | 0 | 3 / 0 |

The successor records zero added or removed IDs and zero evidence replacements.
Every retained ID appears in the receipt. Each path remains conservative with
evidence in both revisions. The full report retains the original 31
test-module paths and the direct package path from the local import in
`testDifferentName`. The source-error, Humanize and oyaml reports are identical.
All labels remain draft pending independent review.
[Successor receipt and exact retained IDs](../corpus/real-v4-successors/variadic-dispatch-v1/baseline.json)

```sh
make evaluate-real-v4-unittest   # frozen discovery successor
make evaluate-real-v4-variadic   # reports/real-v4-variadic-dispatch-v1-evaluation.json
```

The latter gate checks the predecessor receipt and stable report, reuses its
labels, and verifies the current engine, full stable measurement, and exact
selection and evidence delta. [Verification](VALIDATION.md#guarded-variadic-timestamp-fallback)
