# Fresh-repository evaluation v5

V5 measures four changes from two repositories absent from the v1–v4
measurements. Selection prioritized dependency paths visible in the captured
source and Python standard library. The rules preceded candidate inspection.
The analyzer, source and draft labels were frozen before analysis at CodeImpact
`06f8a31b2435f95d5f3b0bbc6b4b70efd1c108b7`. All four selected cases were
retained. Human label review was skipped at the owner's direction.
[Protocol](../datasets/real-v5/PROTOCOL.md) ·
[Candidate decisions and exact revisions](../datasets/real-v5/CANDIDATES.md) ·
[Dataset and attribution](../datasets/real-v5/README.md)

Run `make evaluate-real-v5` from the project root. The offline gate checks the
source and license bytes against the complete captured Git trees, audits
discovery and label coverage, validates typed recommendation evidence, and
compares the stable report with the first-run digest. It checks discrepancy
IDs against a separate baseline. Output goes to
`reports/real-v5-evaluation.json`. A passing replay reproduces the recorded
misses and over-selection. Existing v1–v4 targets replay their own baselines.
[Freeze](../datasets/real-v5/frozen-inputs.json) ·
[First measurement and exact IDs](../datasets/real-v5/first-run.json) ·
[Baseline discrepancy IDs](../datasets/real-v5/baseline.json)

## First measurement

| Case or group | Selected / discovered | TP | FP | FN | TN | Uncertain selected / unselected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Cached Property async wrapper | 13 / 13 | 11 | 1 | 0 | 0 | 1 / 0 |
| Cached Property coroutine metadata | 15 / 15 | 6 | 9 | 0 | 0 | 0 / 0 |
| Cached Property subtotal | 28 / 28 | 17 | 10 | 0 | 0 | 1 / 0 |
| Python SemVer subclass comparison | 3 / 106 | 1 | 2 | 29 | 74 | 0 / 0 |
| Python SemVer prerelease comparison | 71 / 105 | 31 | 40 | 4 | 30 | 0 / 0 |
| Python SemVer subtotal | 74 / 211 | 32 | 42 | 33 | 104 | 0 / 0 |
| Overall | 102 / 239 | 49 | 52 | 33 | 104 | 1 / 0 |

The source audit counted 240 test-shaped base definitions and 239 head
definitions across the four cases. All were discovered in their respective
revisions. The async-wrapper revision removes two definitions and the
subclass-comparison revision adds one. Uncertain definitions are tracked
separately from the confusion matrix. The unit is a source definition.
Parameterized rows, inherited executions and doctest examples do not add to
these counts. The language of the table reflects agreement with draft
dependency labels. The upstream suites were never run.
[Both-revision discovery audit](../datasets/real-v5/discovery.json)

Both SemVer captures record the unsupported symlinks `tests/coerce.py` and
`tests/semverwithvprefix.py` in their Git trees. Their target examples are
already present as ordinary Python blobs under `docs/advanced/`. The
snapshots include all supported Python blobs in both revisions.

| Case | Changed-test evidence | Resolved call paths | Conservative paths |
| --- | ---: | ---: | ---: |
| Cached Property async wrapper | 8 | 5 | 0 |
| Cached Property coroutine metadata | 0 | 0 | 15 |
| Python SemVer subclass comparison | 1 | 0 | 2 |
| Python SemVer prerelease comparison | 0 | 0 | 71 |
| Overall | 9 | 5 | 88 |

The new subclass test has after-only changed-test evidence. The other 101
recommendations have both-revisions evidence. A resolved path can end at a
changed helper whose changed branch the test never exercises.

## What the discrepancies show

- **Cached Property async wrapper.**
  `TestCachedPropertyWithTTL.test_ttl_expiry` reaches the changed
  `CheckFactory` by a resolved call. It supplies the synchronous TTL
  descriptor and does not call the revised thread helper.
  `TestCachedProperty.test_cached_property` also reaches `CheckFactory`.
  The draft marks it uncertain because the getter is synchronous and later
  accesses run inside an uncaptured `freeze_time` context. Three legacy
  coroutine tests were directly edited. Their head bodies use `yield` in
  `async def`, so the source-based labels make no claim about how those
  bodies execute under a particular runner.
  [Pinned change](https://github.com/pydanny/cached-property/commit/6e0394999fe7d114b89c3b54c8db0cb0eab8c67e)
- **Cached Property coroutine metadata.** The six async or generator-style
  tests read an instance coroutine descriptor. That route constructs the
  wrapper decorated with the added `functools.wraps`. Nine synchronous
  definitions bypass that route yet receive the same kind of test-module
  to production-module import path.
  [Pinned change](https://github.com/pydanny/cached-property/commit/c97cf414254e2aed83417785b3890a4f2602ba81)
- **Python SemVer subclass comparison.**
  `test_compare_with_subclass` is newly added. The two existing tests in
  its file get fallback to `tests/test_subclass.py::<module>` even though
  their checks parse, replace or render versions. The 29 misses include
  `test_should_versioninfo_bump_major_and_minor`, which compares two
  `Version` objects with `==`. The operator invokes `Version.__eq__`
  through the edited `_comparator.wrapper`. Other misses include builtin
  `min` and `max` comparing parsed keys and tests using reflected
  comparisons. The selected paths do not cover those operator or wrapper
  routes.
  [Pinned change](https://github.com/python-semver/python-semver/commit/bc41390f388d88114e8529b17fe145c5af390cbb)
- **Python SemVer prerelease comparison.** `Version.compare` returns on
  different core triplets. Equal triplets enter `_nat_cmp` even when
  neither version has a prerelease. Three misses use rich comparison on
  equal triplets, including `test_should_compare_prerelease_and_build_with_numbers`.
  The fourth, `test_should_process_parsed_cli_arguments`, includes a
  `cmd_compare` row with two `1.2.3` versions supplied via a callback
  parameter. Of the 40 false positives, 39 end at the changed production
  module via the test module and package import. The remaining one,
  `tests/test_typeerror-274.py::test_should_not_work_with_invalid_args`,
  calls `Version.parse(8)` before the conservative module edge. Parsing
  rejects the argument without comparing versions.
  [Pinned change](https://github.com/python-semver/python-semver/commit/0f30183605ebb1cb43de1a6b8baad5dcd754f685)

Start the next analyzer slice with direct rich comparison between two
statically known local `Version` instances. One test such as
`test_should_versioninfo_bump_major_and_minor` can anchor the two-revision
trace through `__eq__` and its locally defined decorator. Check the
receiver, operator and wrapper binding before considering broader reflected
dispatch, builtin `min`/`max`, or the CLI callback. Record any change in a
successor measurement.

## Exact-class equality successor

Run `make evaluate-real-v5-equality` for the `exact-equality-v1` successor.
`make evaluate-real-v5` still reproduces the original report with the
equality proof disabled. Both gates use the original source, discovery and
draft labels. The successor validates the prior report before measuring the
new behavior. Its receipt pins the complete stable report, exact
recommendation differences and remaining discrepancy IDs.
[Successor receipt](../datasets/real-v5-successors/exact-equality-v1.json) ·
[Source transition](../benchmarks/exact-equality-v1-preservation.json)

| Measurement | Selected / discovered | TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Subclass comparison, original | 3 / 106 | 1 | 2 | 29 | 74 | 0 |
| Subclass comparison, successor | 5 / 106 | 3 | 2 | 27 | 74 | 0 |
| V5 overall, original | 102 / 239 | 49 | 52 | 33 | 104 | 1 |
| V5 overall, successor | 104 / 239 | 51 | 52 | 31 | 104 | 1 |

### Pinned trace and evidence

Both subclass-comparison snapshots expose `parse_version_info` through
`src/semver/__init__.py`. The named function in `_deprecated.py` applies a
source-defined decorator factory. Its returned wrapper uses
`functools.wraps`, performs the warning path, then forwards its arguments and
return value through `return func(*args, **kwargs)`. The forwarded
`parse_version_info` calls the explicitly imported `Version.parse`.
`Version.parse` binds the exact class through `@classmethod`, parses the
string and returns `cls(**matched_version_parts)` on success.

In `test_should_versioninfo_bump_major_and_minor`, the left operand starts
at `parse_version_info("3.4.5")` and runs `bump_major().bump_minor()`. Both
methods construct through `cls = type(self)`. The right operand directly
parses `"4.1.0"`. The other newly selected test takes the same route through
`bump_minor().bump_patch()`. On both paths the operands have the same
source-owned class. `Version.__eq__` holds the function returned by
`_comparator`. Before, its tuple includes `Version`. After, the tuple
uses `type(self)`. The evidence targets the returned wrapper whose body
changed. It uses the existing call edge type and cites the comparison
expression and the wrapper definition in each revision.
[Before tree](https://github.com/python-semver/python-semver/tree/bd97cfcd595c882d92b73430d4bf5c880d6062dc) ·
[After change](https://github.com/python-semver/python-semver/commit/bc41390f388d88114e8529b17fe145c5af390cbb) ·
[Python comparison dispatch](https://docs.python.org/3/reference/datamodel.html#object.__eq__) ·
[`functools.wraps`](https://docs.python.org/3/library/functools.html#functools.wraps)

| Newly selected ID | Comparison line | Target range in both revisions |
| --- | ---: | --- |
| `tests/test_bump.py::test_should_versioninfo_bump_major_and_minor` | 28 | `src/semver/version.py` 41–52 |
| `tests/test_bump.py::test_should_versioninfo_bump_minor_and_patch` | 34 | `src/semver/version.py` 41–52 |

Both recommendations have distance 1, score 82 and `both` revision evidence.
All existing recommendations keep their evidence and scores. The prerelease
case receives the same two graph edges, where the wrapper is unchanged. Its
71 recommendations, evidence paths and classifications are identical.
Both Cached Property analyses remain byte-identical with timing excluded.
There are no added or removed false positives.

### Remaining draft misses

The subclass case retains these 27 misses. Reasons include unsupported
prerelease/build factories, parameterized operands, earlier assertions or
other effects before the target comparison, reflected/mixed-type
operations, and comparison performed inside builtins or callbacks.

| File | Remaining test definitions |
| --- | --- |
| `tests/test_bump.py` | `test_should_versioninfo_bump_build_with_empty_str`, `test_should_versioninfo_bump_build_with_none`, `test_should_versioninfo_bump_multiple`, `test_should_versioninfo_bump_patch_and_prerelease`, `test_should_versioninfo_bump_patch_and_prerelease_with_token`, `test_should_versioninfo_bump_prerelease_and_build`, `test_should_versioninfo_bump_prerelease_and_build_with_token`, `test_should_versioninfo_bump_prerelease_with_empty_str`, `test_should_versioninfo_bump_prerelease_with_none` |
| `tests/test_compare.py` | `test_should_compare_prerelease_and_build_with_numbers`, `test_should_compare_prerelease_with_numbers_and_letters`, `test_should_compare_version_dictionaries`, `test_should_compare_version_info_objects`, `test_should_compare_version_list`, `test_should_compare_version_string`, `test_should_compare_version_tuples`, `test_should_not_allow_to_compare_invalid_versionstring`, `test_should_not_allow_to_compare_version_with_int` |
| `tests/test_deprecated_functions.py` | `test_should_raise_deprecation_warnings` |
| `tests/test_max-min.py` | `test_prerelease_order`, `test_should_get_max`, `test_should_get_max_same`, `test_should_get_min`, `test_should_get_min_same` |
| `tests/test_parsing.py` | `test_equal_versions_have_equal_hashes`, `test_should_parse_version_with_optional_minor_and_patch` |
| `tests/test_replace.py` | `test_should_return_versioninfo_with_replaced_parts` |

The prerelease case retains four misses.
`tests/test_compare.py` contains
`test_should_compare_prerelease_and_build_with_numbers`,
`test_should_compare_version_dictionaries` and
`test_should_compare_version_info_objects`.
`tests/test_pysemver-cli.py::test_should_process_parsed_cli_arguments` uses
a parameterized command callback. Their unchanged outcomes remain in the
successor receipt.

The proof covers a terminal single `==` assertion in a plain top-level
test. It audits captured imports, eager bindings, ordinary construction,
and class-preserving returns. The static analysis describes the binding
when the source operation runs under ordinary Python and supported
standard-library behavior. It does not reproduce pytest collection,
runner hooks, warning handlers, or arbitrary outside code. The labels
remain drafts and no upstream tests were run.

## Class-preserving prerelease factories

`make evaluate-real-v5-factories` replays the frozen v5 and exact-equality
measurements first. It then pins the full current report, all recommendation
differences and every remaining discrepancy in `prerelease-factories-v1`.
The same four captures and draft labels are used throughout.
[Successor receipt](../datasets/real-v5-successors/prerelease-factories-v1.json) ·
[Engine hashes](../benchmarks/prerelease-factories-v1-preservation.json)

| Measurement | Selected / discovered | TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Subclass comparison, exact equality | 5 / 106 | 3 | 2 | 27 | 74 | 0 |
| Subclass comparison, factories | 13 / 106 | 11 | 2 | 19 | 74 | 0 |
| V5 overall, exact equality | 104 / 239 | 51 | 52 | 31 | 104 | 1 |
| V5 overall, factories | 112 / 239 | 59 | 52 | 23 | 104 | 1 |

In both revisions, the test on line 78 parses `"3.4.5"` and
`"3.4.5-rc.1"` through `parse_version_info` and `Version.parse`. The first
instance has no prerelease. Passing `None` to `bump_prerelease` picks
`"rc.0"`. The frozen equality proof already binds `cls = type(self)` to
`Version` and follows the token branches. It first declines at line 335,
where the call on that class resolves to a static method.

The source binds `_increment_string` with the builtin `staticmethod`.
It searches the string with the class's compiled standard-library pattern,
increments the last captured number, and uses the capture span to rebuild
the string. A search with no match returns the original input. For
`"rc.0"` the captured digit is `0` and the result is `"rc.1"`.
Line 336 constructs through the same `cls` with the original numeric
fields and the rewritten data. Both operands therefore have the same
exact class on normal return. Looking up `__eq__` on that class yields the
edited `_comparator.wrapper`. Its accepted-type tuple uses `Version` before and
`type(self)` after. The evidence records the comparison and wrapper.
[Base source](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/src/semver/version.py#L308-L336) ·
[Head source](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/src/semver/version.py#L308-L336)

The new rule inspects a one-argument static helper with a class-owned regex
search, a guarded match branch, and one final return of the input binding.
It checks every assignment in the branch, including scalar additions,
subtractions, slices, capture reads, span unpacking and unshadowed builtin
calls. It needs only the kind of the returned data. Captured regexes and
Python code are never run. Opaque calls, competing helper bindings, dynamic
receivers, inheritance and alternative operand classes decline. Each
revision supplies its own proof.

All eight added IDs are in `tests/test_bump.py`. Each has a single resolved
call edge from the listed comparison to
`src/semver/version.py::_comparator.wrapper` at lines 41–52. The distance
is 1 and the score is 90. The ranges below are identical in base and head.

| New test definition | Before comparison line | After comparison line |
| --- | ---: | ---: |
| `test_should_versioninfo_bump_patch_and_prerelease` | 40 | 40 |
| `test_should_versioninfo_bump_patch_and_prerelease_with_token` | 46 | 46 |
| `test_should_versioninfo_bump_prerelease_and_build` | 52 | 52 |
| `test_should_versioninfo_bump_prerelease_and_build_with_token` | 58 | 58 |
| `test_should_versioninfo_bump_prerelease_with_empty_str` | 72 | 72 |
| `test_should_versioninfo_bump_prerelease_with_none` | 78 | 78 |
| `test_should_versioninfo_bump_build_with_empty_str` | 84 | 84 |
| `test_should_versioninfo_bump_build_with_none` | 90 | 90 |

The build method uses the same class and static helper. Its captured body
repeats the token assignment and helper call before returning the new
instance. Both occurrences pass the same proof. No recommendations were
removed. The two previously resolved major/minor and minor/patch tests
retain their exact evidence. Their scores rise from 82 to 90 because the
existing formula counts more callers of the changed wrapper.

The separate SemVer prerelease-comparison case gains the same eight graph
edges. Its wrapper is unchanged and all 71 recommendations retain their
scores and evidence. Both Cached Property analyses remain byte-identical
with timing excluded. V5 now has 15 resolved, 88 conservative and nine
changed-test recommendations.

The subclass case retains one bump-file miss,
`test_should_versioninfo_bump_multiple`. Its first equality appears before
more assignments and a second assertion. The factory proof admits one
terminal equality with a supported prefix. The other 18 misses are the
previously listed comparison, deprecation, min/max, parsing and replacement
definitions. Its two draft false positives remain
`tests/test_subclass.py::test_replace_from_subclass` and
`tests/test_subclass.py::test_subclass_from_versioninfo`. The other SemVer
case still has four misses and 40 draft false positives. Cached Property
retains ten draft false positives and the single selected uncertain definition.
The receipt lists all remaining IDs per case. Human label review was skipped.

## First equality assertion

The `first-assertion-v1` successor recovers two draft-affected tests in the
SemVer subclass case. Run `make evaluate-real-v5-first-assertion` to
reproduce the factory predecessor and compare the complete current report
against its receipt. All four measurements use the same pinned sources and
draft labels. [Selection and discrepancy receipt](../datasets/real-v5-successors/first-assertion-v1.json) · [Engine hashes](../benchmarks/first-assertion-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Subclass comparison, factories | 13 / 106 | 11 | 2 | 19 | 74 | 0 |
| Subclass comparison, first assertion | 15 / 106 | 13 | 2 | 17 | 74 | 0 |
| V5 overall, factories | 112 / 239 | 59 | 52 | 23 | 104 | 1 |
| V5 overall, first assertion | 114 / 239 | 61 | 52 | 21 | 104 | 1 |

| New recommendation | Before comparison | After comparison | Bound target in both revisions |
| --- | ---: | ---: | --- |
| `tests/test_bump.py::test_should_versioninfo_bump_multiple` | 64 | 64 | `src/semver/version.py::_comparator.wrapper`, lines 41–52 |
| `tests/test_parsing.py::test_equal_versions_have_equal_hashes` | 155 | 155 | `src/semver/version.py::_comparator.wrapper`, lines 41–52 |

**Line 64.** In both snapshots, lines 62–63 parse the receiver and expected
value into exact `Version` instances. The left operand calls
`bump_prerelease().bump_build().bump_build()`. Each call constructs
through `type(self)` after the source-defined scalar helper. The right
operand reads the original `expected` binding. Comparing them invokes
the wrapper bound to `Version.__eq__`. The edit replaces `Version` with
`type(self)` in that wrapper's accepted-type tuple. The factory predecessor
looked only at the final assertion on line 66 and stopped when its prefix
encountered the assertion on line 64. Line 65 reassigns `expected` after
the first comparison. The new edge cites line 64 and the wrapper in each revision.
[Base test](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/tests/test_bump.py#L61-L66) · [Head test](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/tests/test_bump.py#L61-L66)

**Line 155.** Two calls to `parse_version_info` establish the exact operands
of `assert v1 == v2`. This comparison reaches the same edited wrapper.
The subsequent hash comparison and dictionary and set operations supply
no evidence in this path. [Pinned test](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/tests/test_parsing.py#L152-L162)

Both additions have one resolved call edge, distance 1 and score 90. The
wrapper already had enough callers to reach the scoring formula's fan-in
cap. No recommendation was removed, and every previous recommendation
retained its score and evidence. The separate prerelease-comparison case
gains the same two graph edges to an unchanged wrapper. Its 71
recommendations retain their scores and paths. Both Cached Property
analyses are unchanged. V5 now records 17 resolved, 88 conservative and
nine changed-test recommendations.

The subclass case retains 17 draft misses across comparison, deprecation,
min/max, parsing and replacement tests. Its two draft false positives remain
`test_replace_from_subclass` and `test_subclass_from_versioninfo`. The
prerelease-comparison case retains four misses and 40 false positives.
Cached Property retains ten false positives and the single selected
uncertain label. The receipt lists each ID. Independent review was skipped.
