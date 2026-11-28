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

## Exact-class less-than evidence

`make evaluate-real-v5-less-than` checks the first-assertion predecessor and
replays the same four captures with `exact-less-than-v1`. The new receipt
pins the complete stable report, the recommendation delta and the remaining
draft-label discrepancy IDs. [Successor receipt](../datasets/real-v5-successors/exact-less-than-v1.json) · [Engine hashes](../benchmarks/exact-less-than-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Subclass comparison, first assertion | 15 / 106 | 13 | 2 | 17 | 74 | 0 |
| Subclass comparison, less-than | 17 / 106 | 15 | 2 | 15 | 74 | 0 |
| V5 overall, first assertion | 114 / 239 | 61 | 52 | 21 | 104 | 1 |
| V5 overall, less-than | 116 / 239 | 63 | 52 | 19 | 104 | 1 |

| Added recommendation | Before comparison | After comparison | Bound target in both revisions |
| --- | ---: | ---: | --- |
| `tests/test_compare.py::test_should_compare_prerelease_with_numbers_and_letters` | 129 | 129 | `src/semver/version.py::_comparator.wrapper`, lines 41–52 |
| `tests/test_compare.py::test_should_compare_prerelease_and_build_with_numbers` | 299–301 | 299–301 | `src/semver/version.py::_comparator.wrapper`, lines 41–52 |

In both snapshots, `from semver import Version` follows the package
initializer’s explicit import from `.version`. The assignments on
lines 127–128 construct two `Version` objects. The left has prerelease `"1unms"` and the right
has no prerelease. At line 129, Python attempts the left operand's
`__lt__` because both operands have the same exact class. In both
snapshots, `@_comparator` on lines 473–475 binds the returned wrapper
to `Version.__lt__`. The wrapper's type tuple contains `Version` in base
and `type(self)` in head. Both include the exact class of the right
operand. The wrapper forwards to the original method, whose body calls
`self.compare(other) < 0`. The evidence targets the edited wrapper.
The predecessor's assertion proof accepted only `==`.
[Base comparison](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/tests/test_compare.py#L126-L130) · [Head comparison](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/tests/test_compare.py#L126-L130)

The second test constructs both exact `Version` operands inline in its
first assertion. The constructor converts the numeric prerelease and
build inputs to strings. The comparison reaches the same bound wrapper.
The location covers the entire multiline expression. Each recommendation
uses one resolved call edge, with score 90 and evidence in both revisions.
[Head comparison](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/tests/test_compare.py#L298-L304)

The proof records the first call to a supported source-bound `__lt__`.
Same exact class rules out a right-hand subclass taking priority through
`__gt__`. If `__lt__` returns `NotImplemented`, Python can then attempt
`__gt__`. The analysis models only the first dispatch. It declines mixed
classes, unknown operands, absent or ambiguous methods, chained comparisons
and unsupported assertion prefixes. It analyzes before and after separately.

Both Cached Property analyses are identical. The separate SemVer
prerelease-comparison case gains the two graph edges to an unchanged
wrapper and keeps the same 71 recommendations. Every previous
recommendation retains its evidence and score. V5 now has 19 resolved,
88 conservative and nine changed-test recommendations.

The subclass case retains 15 draft misses and the same two draft false
positives, `test_replace_from_subclass` and
`test_subclass_from_versioninfo`. The prerelease-comparison case retains
four misses and 40 false positives. Cached Property retains ten false
positives and one selected uncertain definition. The receipt lists the
exact remaining IDs. Labels remain drafts.

## Exact-class inequality evidence

`make evaluate-real-v5-inequality` first checks the preserved less-than
replay, then measures `exact-inequality-v1` on the same four captures and
draft labels. The receipt pins the complete stable report, including the
before and after source ranges, exact recommendation changes and remaining
discrepancy IDs. [Successor receipt](../datasets/real-v5-successors/exact-inequality-v1.json) · [Engine hashes](../benchmarks/exact-inequality-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Subclass comparison, less-than | 17 / 106 | 15 | 2 | 15 | 74 | 0 |
| Subclass comparison, inequality | 18 / 106 | 16 | 2 | 14 | 74 | 0 |
| V5 overall, less-than | 116 / 239 | 63 | 52 | 19 | 104 | 1 |
| V5 overall, inequality | 117 / 239 | 64 | 52 | 18 | 104 | 1 |

| Added recommendation | Before comparison | After comparison | Bound target in both revisions |
| --- | ---: | ---: | --- |
| `tests/test_compare.py::test_should_compare_version_info_objects` | 138 | 138 | `src/semver/version.py::_comparator.wrapper`, lines 41–52 |

In both pinned revisions, the test imports `Version` through the package
initializer. Lines 134–135 construct two instances of the same exact class.
Both have version numbers `0.10.4`, and the right operand has prerelease
`"beta.1"`. Their first assertion, `assert v1 != v2`, calls the left
operand's explicit `Version.__ne__` binding. The decorator at line 469
binds the wrapper returned by `_comparator`. Its type check uses `Version`
in base and `type(self)` in head, so both accept the right operand. The
wrapper forwards to the method body on line 471, which returns
`self.compare(other) != 0`. CodeImpact records the initial call from line
138 to the edited wrapper. The later assertions supply no evidence for this
recommendation. [Base test](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/tests/test_compare.py#L133-L143) · [Head test](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/tests/test_compare.py#L133-L143)

The proof covers one direct `!=` assertion after a supported straight-line
prefix. It uses the function-wide local binding audit and requires a
supported source-defined `__ne__` on the exact class. A missing, rebound
or ambiguous method, unknown or mixed operand classes, and chained
comparisons stay outside this proof. The default `object.__ne__` delegation
to `__eq__` and dispatch after an explicit `NotImplemented` return are
outside the slice. Before and after are proved independently.

The new recommendation has distance 1 and score 90. Every existing
recommendation retains its score and evidence, and none were removed. The
separate SemVer prerelease-comparison case gains the same edge to its
unchanged wrapper and retains its 71 recommendations. Both Cached Property
analyses match the predecessor. V5 now has 20 resolved, 88 conservative
and nine changed-test recommendations.

The subclass case retains 14 draft misses and two draft false positives
(`test_replace_from_subclass` and `test_subclass_from_versioninfo`). The
prerelease-comparison case retains four misses and 40 false positives.
Cached Property retains ten false positives and one selected uncertain
definition. The successor receipt lists the exact remaining IDs. Labels
remain drafts.

## Inequality with a builtin dictionary

`make evaluate-real-v5-dictionary-inequality` checks the exact-class
inequality predecessor and measures `dictionary-inequality-v1` on the
same four captures and draft labels. The receipt pins the complete stable
report, including the revision-specific evidence ranges, recommendation
delta and all remaining discrepancy IDs. [Successor receipt](../datasets/real-v5-successors/dictionary-inequality-v1.json) · [Engine hashes](../benchmarks/dictionary-inequality-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Subclass comparison, exact-class inequality | 18 / 106 | 16 | 2 | 14 | 74 | 0 |
| Subclass comparison, dictionary inequality | 19 / 106 | 17 | 2 | 13 | 74 | 0 |
| V5 overall, exact-class inequality | 117 / 239 | 64 | 52 | 18 | 104 | 1 |
| V5 overall, dictionary inequality | 118 / 239 | 65 | 52 | 17 | 104 | 1 |

| Added recommendation | Before comparison | After comparison | Bound target in both revisions |
| --- | ---: | ---: | --- |
| `tests/test_compare.py::test_should_compare_version_dictionaries` | 167 | 167 | `src/semver/version.py::_comparator.wrapper`, lines 41–52 |

In both pinned revisions, line 164 constructs a source-defined
`Version` and line 165 calls unshadowed builtin `dict` with the
`major`, `minor`, `patch`, `prerelease` and `build` keyword arguments.
The right operand is an exact builtin dictionary. It has no subclass
relationship to the left operand's class, so Python tries the left
operand's explicit `__ne__` first. Line 469 in `src/semver/version.py`
decorates that method with `_comparator`, which binds the edited wrapper.
Both wrapper type tuples include builtin `dict`. Their first entries
use `Version` in base and `type(self)` in head. The wrapper
forwards to the original method on lines 470–471. The recorded edge
cites the first comparison, `assert v1 != v2`, and the wrapper itself.
[Base test](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/tests/test_compare.py#L163-L172) · [Head test](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/tests/test_compare.py#L163-L172)

The new proof tracks dictionaries constructed in the straight-line test
prefix or inline as the right operand. It recognizes dictionary literals
with constant keys and supported values, empty `dict()`, and unshadowed
`dict` calls with explicit keyword arguments whose values the existing
expression proof supports. Positional constructor inputs and unpacking
stay outside its scope. The test's whole function supplies local binding
information, so a local assignment later in the body can shadow the
constructor. The proof declines reversed operands, dictionary subclasses,
ambiguous bindings and other mixed types. It records the initial
invocation only, with later dispatch after `NotImplemented` outside the
proof.

The new recommendation has distance 1 and score 90. Every previous
recommendation retained its score and evidence. The separate SemVer
prerelease case gains the same graph edge to an unchanged wrapper and
retains its 71 recommendations. Both Cached Property analyses match the
predecessor. V5 now has 21 resolved, 88 conservative and nine changed-test
recommendations.

The subclass case retains 13 draft misses and two draft false positives
(`test_replace_from_subclass` and `test_subclass_from_versioninfo`). The
prerelease case retains four misses and 40 false positives. Cached Property
retains ten false positives and one selected uncertain definition. The
successor receipt lists the exact IDs. Labels remain drafts.

## Less-than with literal pytest parameters

`make evaluate-real-v5-parameterized-less-than` checks the dictionary
inequality predecessor and measures `parameterized-less-than-v1` on the
same four captures and draft labels. The full report hash pins the
comparison ranges and bound targets in each revision. The receipt also
records the exact recommendation delta and remaining discrepancies.
[Successor receipt](../datasets/real-v5-successors/parameterized-less-than-v1.json) · [Engine hashes](../benchmarks/parameterized-less-than-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Subclass comparison, dictionary inequality | 19 / 106 | 17 | 2 | 13 | 74 | 0 |
| Subclass comparison, parameterized less-than | 21 / 106 | 19 | 2 | 11 | 74 | 0 |
| V5 overall, dictionary inequality | 118 / 239 | 65 | 52 | 17 | 104 | 1 |
| V5 overall, parameterized less-than | 120 / 239 | 67 | 52 | 15 | 104 | 1 |

| Added recommendation | Before assertion | After assertion | Target in both revisions |
| --- | ---: | ---: | --- |
| `tests/test_compare.py::test_should_compare_version_tuples` | 206 | 206 | `src/semver/version.py::_comparator.wrapper`, lines 41–52 |
| `tests/test_compare.py::test_should_compare_version_list` | 235 | 235 | `src/semver/version.py::_comparator.wrapper`, lines 41–52 |

Both pinned revisions use direct `@pytest.mark.parametrize` calls. Lines
192–201 give `t` five builtin tuples. Lines 221–230 give `lst` five
builtin lists. Each table names a single parameter, so each row is the
value passed to that parameter under standard direct pytest
parametrization. Rows vary in length and values but agree on their exact
builtin type. Lines 203 and 232 construct the left operand `v0` from the
package's source-defined `Version` in the two tests.
[Base tests](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/tests/test_compare.py#L192-L235) · [Head tests](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/tests/test_compare.py#L192-L235)

The exact tuple and list types are unrelated to the left operand's class.
Python therefore tries the left `__lt__` before considering reflected
dispatch. The decorator at line 473 binds the wrapper returned by
`_comparator`. Its type tuple includes builtin `tuple` and `list` in
both revisions, while its first entry changes from `Version` to
`type(self)`. It forwards to `Version.__lt__`, whose body returns
`self.compare(other) < 0`. Each resolved edge cites the first assertion
and wrapper. The later comparisons supply no evidence in these paths.
[Head wrapper](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/src/semver/version.py#L38-L54)

The proof accepts one direct decorator backed by an unshadowed
`import pytest`, one required positional-or-keyword parameter, and a
literal list or tuple table. It requires 1–64 rows with at most 256
constant elements in total. All rows must be tuple literals or all
must be list literals. The first assertion must read that parameter
directly on its right, with a supported straight-line prefix and a
provable source-class instance on the left. Mixed or computed rows,
rebindings, stacked or indirect parametrization, reversed operands,
subclasses, and dispatch after `NotImplemented` stay outside this
proof. Evidence is attached to the test definition, once per proved
revision. Runner hooks and individual pytest cases are outside the
recorded source proof.

Each added recommendation has distance 1 and score 90. Every previous
recommendation retains its score and evidence. The separate SemVer
prerelease case gains the same two edges to an unchanged wrapper and
keeps its 71 recommendations. Both Cached Property analyses match the
predecessor. V5 now records 23 resolved, 88 conservative and nine
changed-test recommendations.

The subclass case retains 11 draft misses and two draft false positives
(`test_replace_from_subclass` and `test_subclass_from_versioninfo`).
The prerelease case retains four misses and 40 false positives.
Cached Property retains ten false positives and one selected uncertain
definition. The successor receipt lists the exact IDs. Labels remain
drafts.

## Less-than with literal pytest string parameters

`make evaluate-real-v5-string-parameter-less-than` checks the tuple and
list predecessor and measures `string-parameter-less-than-v1` on the
same captures and draft labels. The stable report hash pins the evidence
ranges by revision. The receipt also lists the exact recommendation delta
and remaining discrepancies.
[Successor receipt](../datasets/real-v5-successors/string-parameter-less-than-v1.json) · [Engine hashes](../benchmarks/string-parameter-less-than-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Subclass comparison, tuple and list parameters | 21 / 106 | 19 | 2 | 11 | 74 | 0 |
| Subclass comparison, string parameters | 22 / 106 | 20 | 2 | 10 | 74 | 0 |
| V5 overall, tuple and list parameters | 120 / 239 | 67 | 52 | 15 | 104 | 1 |
| V5 overall, string parameters | 121 / 239 | 68 | 52 | 14 | 104 | 1 |

In both pinned revisions, lines 250–259 of `tests/test_compare.py` give
`s` the three literal strings `"1.0.0"`, `"1.0.0-pre.2"` and
`"1.0.0-pre.2+build.4"`. The source-defined `Version` constructor at
line 261 establishes the exact class of the left operand. The right
operand is an exact builtin `str` in each row, so it has no subclass
priority over the left operand. Python first tries the callable
bound to `Version.__lt__`, installed by `@_comparator` at line 473 of
`src/semver/version.py`. Both wrappers include `str` through
`String.__args__`, with `String = Union[str, bytes]` in
`src/semver/_types.py`. The type tuple starts with `Version` in base
and `type(self)` in head. The wrapper forwards to the original
`__lt__`, whose body returns `self.compare(other) < 0`.
[Base test](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/tests/test_compare.py#L250-L264) · [Head test](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/tests/test_compare.py#L250-L264)

The only added recommendation is
`tests/test_compare.py::test_should_compare_version_string`. Its
resolved call edge runs from line 264 to
`src/semver/version.py::_comparator.wrapper` at lines 41–52 in both
revisions. It has distance 1 and score 90. Existing recommendation
scores and evidence are identical. The separate prerelease case gains
the same graph edge to its unchanged wrapper and retains its 71
recommendations. Both Cached Property cases match their predecessor.

The proof uses the existing single-parameter table and direct-assertion
rules. A string table must contain 1–64 rows, all exact string literals.
Mixed or empty tables, computed strings, reversed dispatch, guards such
as `pytest.raises`, and dispatch after `NotImplemented` stay outside the
proof. Evidence still describes the test definition. The nearby
`test_should_not_allow_to_compare_invalid_versionstring` remains a
draft miss because its comparison is inside `pytest.raises`.

The subclass case retains ten draft misses and two draft false positives.
The prerelease case retains four misses and 40 false positives. Cached
Property retains ten false positives and one selected uncertain
definition. The receipt lists the remaining IDs. Labels remain drafts.

## Less-than inside pytest.raises

`make evaluate-real-v5-raises-less-than` checks the direct string
assertion predecessor and measures `raises-less-than-v1` on the same
captures and draft labels. The receipt pins the complete stable report,
including exact source ranges, the recommendation delta and remaining
discrepancies.
[Successor receipt](../datasets/real-v5-successors/raises-less-than-v1.json) · [Engine hashes](../benchmarks/raises-less-than-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Subclass comparison, direct string parameters | 22 / 106 | 20 | 2 | 10 | 74 | 0 |
| Subclass comparison, raises less-than | 23 / 106 | 21 | 2 | 9 | 74 | 0 |
| V5 overall, direct string parameters | 121 / 239 | 68 | 52 | 14 | 104 | 1 |
| V5 overall, raises less-than | 122 / 239 | 69 | 52 | 13 | 104 | 1 |

In both revisions, line 279 of `tests/test_compare.py` supplies
`s` with the literal strings `"1"`, `"1.0"` and `"1.0.x"`. Line 281
constructs `v` as the source-defined `Version`. Line 282 enters
`pytest.raises(ValueError)` using the direct pytest import and the
unshadowed builtin exception class. The block contains one expression,
`v < s`, at line 283. Builtin `str` is unrelated to `Version`, so Python
tries the left `__lt__` first. At line 473 of `src/semver/version.py`,
`@_comparator` installs the wrapper returned by `_comparator`. Its
type tuple includes `str` through `String.__args__` in both revisions.
The changed first entry uses `Version` in base and `type(self)` in head.
The wrapper forwards to `__lt__`, whose body calls `self.compare(other)`.
[Base test](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/tests/test_compare.py#L279-L285) · [Head test](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/tests/test_compare.py#L279-L285)

The only added recommendation is
`tests/test_compare.py::test_should_not_allow_to_compare_invalid_versionstring`.
The resolved call edge cites line 283 and
`src/semver/version.py::_comparator.wrapper` at lines 41–52 in both
revisions. It has distance 1 and score 90. The later `s > v` expression
supplies no evidence. The record describes the initial call. The
exception outcome, reflected dispatch and later statements stay outside
the proof.

The rule accepts one top-level `with pytest.raises(ValueError):` after
the existing straight-line prefix. The block must hold one bare
`<` expression with a proved exact source instance and a direct
unrebound literal string parameter. The pytest import, `raises` member
and builtin exception binding must be stable. Bindings such as
`as info`, keyword options, multiple context managers, extra body
statements and other expected exceptions are outside the supported form.

Existing recommendation scores and evidence match the predecessor.
The separate prerelease case gains the same edge to its unchanged
wrapper and retains its 71 recommendations. Both Cached Property
cases match their predecessor. Across v5, there are 25 resolved,
88 conservative and nine changed-test recommendations.

The subclass case retains nine draft misses and two draft false
positives. The prerelease case retains four misses and 40 false
positives. Cached Property retains ten false positives and one selected
uncertain definition. The successor receipt lists the remaining IDs.
Labels remain drafts.

## Greater-than inside pytest.raises

`make evaluate-real-v5-raises-greater-than` checks the raises less-than
predecessor and measures `raises-greater-than-v1` on the same captures
and draft labels. The receipt pins the whole stable report, including
the exact comparison and target ranges, the recommendation delta and
remaining discrepancies.
[Successor receipt](../datasets/real-v5-successors/raises-greater-than-v1.json) · [Engine hashes](../benchmarks/raises-greater-than-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Subclass comparison, raises less-than | 23 / 106 | 21 | 2 | 9 | 74 | 0 |
| Subclass comparison, raises greater-than | 24 / 106 | 22 | 2 | 8 | 74 | 0 |
| V5 overall, raises less-than | 122 / 239 | 69 | 52 | 13 | 104 | 1 |
| V5 overall, raises greater-than | 123 / 239 | 70 | 52 | 12 | 104 | 1 |

In both revisions, `tests/test_compare.py` imports the source-owned
`Version` and constructs `v1` at line 289. Line 290 uses the direct
pytest binding and unshadowed builtin `TypeError` to enter the context.
Line 291 contains the single expression `v1 > 1`. The right operand is
exact builtin `int`, unrelated to `Version`, so its reflected `__lt__`
has no subclass priority and Python tries the left `__gt__` first.
In both revisions, `@_comparator` at line 481 of `src/semver/version.py`
binds the returned wrapper to that method. The wrapper's accepted-type
tuple changes its first entry from `Version` to `type(self)`. The edge
cites that wrapper, which is invoked before any decision about
`NotImplemented`, reflected dispatch or the eventual exception.
[Base test](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/tests/test_compare.py#L288-L294) · [Head test](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/tests/test_compare.py#L288-L294)

The only added recommendation is
`tests/test_compare.py::test_should_not_allow_to_compare_version_with_int`.
Its resolved edge cites line 291 and
`src/semver/version.py::_comparator.wrapper` at lines 41–52 in both
revisions. It has distance 1 and score 90. The following `1 > v1` and
subsequent blocks supply no evidence.

The new proof reuses the straight-line prefix and single-expression
`pytest.raises` shape. It requires an undecorated parameterless test,
an unshadowed direct pytest import and builtin `TypeError`, an exact
source-class instance on the left, and an exact builtin integer
constant on the right. Booleans, unary or other computed operands,
reversed operands, ambiguous comparison methods, and context options
stay outside the proof. Evidence records the initial call separately
for each revision.

Earlier recommendation scores and evidence match the predecessor.
The separate prerelease case gains the same edge to its unchanged
wrapper and retains its 71 recommendations. Both Cached Property
analyses match their predecessor. V5 now records 26 resolved,
88 conservative and nine changed-test recommendations.

The subclass case retains eight draft misses and two draft false
positives. The prerelease case retains four misses and 40 false
positives. Cached Property retains ten false positives and one
selected uncertain definition. The successor receipt lists all
remaining IDs. Labels remain drafts.

## Keyed min and max

`make evaluate-real-v5-keyed-extrema` checks the unchanged
`raises-greater-than-v1` predecessor and measures the keyed helper proof
on the same snapshots and draft labels.
[Successor receipt](../datasets/real-v5-successors/keyed-extrema-v1.json) · [Engine hashes](../benchmarks/keyed-extrema-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Subclass comparison, raises greater-than | 24 / 106 | 22 | 2 | 8 | 74 | 0 |
| Subclass comparison, keyed min and max | 28 / 106 | 26 | 2 | 4 | 74 | 0 |
| V5 overall, raises greater-than | 123 / 239 | 70 | 52 | 12 | 104 | 1 |
| V5 overall, keyed min and max | 127 / 239 | 74 | 52 | 8 | 104 | 1 |

Both revisions import `max_ver` and `min_ver` from `semver` at line
3 of `tests/test_max-min.py`. The initializer explicitly re-exports them
from `._deprecated` at lines 17–18. The source decorator wraps the
helper with `functools.wraps`, prepares a deprecation warning, and
forwards `*args` and `**kwargs` to the captured function at line 81
of `src/semver/_deprecated.py`. Both helpers pass their two operands
directly to the unshadowed builtin and convert the returned input with
`str`. Evidence follows the forwarded call to the helper itself.
[Base test](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/tests/test_max-min.py#L3-L19) · [Head test](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/tests/test_max-min.py#L3-L19) · [Base helpers](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/src/semver/_deprecated.py#L201-L236) · [Head helpers](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/src/semver/_deprecated.py#L201-L236)

Both key calls bind `Version.parse` to the exact source class
`Version`. In both revisions its successful return at line 652 of
`src/semver/version.py` constructs `cls(**matched_version_parts)`.
After both calls return, the builtin compares the second key result
with the first using `>` for `max` or `<` for `min`. The key
results have the same exact class, ruling out priority for a reflected
subclass method. Equal inputs still reach the initial ordering call.
The bound target is the wrapper returned by `_comparator`, whose line 44
changes from `Version` to `type(self)`.
[Base key](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/src/semver/version.py#L607-L652) · [Head key](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/src/semver/version.py#L607-L652) · [CPython min/max loop](https://github.com/python/cpython/blob/v3.12.12/Python/bltinmodule.c#L1689-L1768) · [CPython comparison dispatch](https://github.com/python/cpython/blob/v3.12.12/Objects/object.c#L750-L776)

The following are the only four added recommendations. Each has
distance 2, score 72 and both-revision evidence. The second hop points
to `src/semver/version.py::_comparator.wrapper` at lines 41–52.

| Test ID | First hop in `tests/test_max-min.py` | Second hop in `src/semver/_deprecated.py` | Initial binding |
| --- | ---: | --- | --- |
| `tests/test_max-min.py::test_should_get_max` | 7 | `max_ver` line 217 | `Version.__gt__` |
| `tests/test_max-min.py::test_should_get_max_same` | 11 | `max_ver` line 217 | `Version.__gt__` |
| `tests/test_max-min.py::test_should_get_min` | 15 | `min_ver` line 236 | `Version.__lt__` |
| `tests/test_max-min.py::test_should_get_min_same` | 19 | `min_ver` line 236 | `Version.__lt__` |

Existing recommendation evidence and scores match the predecessor.
Each SemVer graph gains four test-to-helper edges and two
helper-to-wrapper edges. The wrapper is unchanged in the prerelease
case, which retains all 71 recommendations. Both Cached Property
analyses match the predecessor.
The replay now has 30 resolved, 88 conservative and nine changed-test
recommendations. The parameterized `test_prerelease_order` remains a
draft miss, along with three other subclass case tests.

- `tests/test_deprecated_functions.py::test_should_raise_deprecation_warnings`
- `tests/test_parsing.py::test_should_parse_version_with_optional_minor_and_patch`
- `tests/test_replace.py::test_should_return_versioninfo_with_replaced_parts`

The subclass case also retains two draft false positives.
The prerelease case retains four draft misses and 40 false positives.
Cached Property retains ten false positives and one selected uncertain
definition. All discrepancy IDs are pinned in the successor receipt.
Winner selection, reflected dispatch and warning outcomes are outside
the proof. Labels remain drafts and upstream code was read as data.

## Keyed min and max from literal pytest tables

`make evaluate-real-v5-keyed-parameters` checks the unchanged
`keyed-extrema-v1` predecessor and measures the extension against the
same snapshots and frozen draft labels.
[Successor receipt](../datasets/real-v5-successors/keyed-parameters-v1.json) · [Engine hashes](../benchmarks/keyed-parameters-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Subclass comparison, keyed literal arguments | 28 / 106 | 26 | 2 | 4 | 74 | 0 |
| Subclass comparison, keyed literal table | 29 / 106 | 27 | 2 | 3 | 74 | 0 |
| V5 overall, keyed literal arguments | 127 / 239 | 74 | 52 | 8 | 104 | 1 |
| V5 overall, keyed literal table | 128 / 239 | 75 | 52 | 7 | 104 | 1 |

In both subclass-case revisions, lines 22–41 of `tests/test_max-min.py`
declare seven three-string rows for `left,right,expected`. For every row,
the first two named columns feed `min_ver(left, right)` at line 43. The
third column supplies the expected value on the right of the assertion.
The deprecation wrapper forwards the call to the helper, which invokes
`min(ver1, ver2, key=Version.parse)` at line 236. Both key invocations
use the same bound classmethod and each normal return constructs that
exact `Version` class. The builtin therefore tries the bound `Version.__lt__`
first. The changed target is `src/semver/version.py::_comparator.wrapper`
at lines 41–52 in each revision.
[Base test](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/tests/test_max-min.py#L22-L43) · [Head test](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/tests/test_max-min.py#L22-L43)

The sole new recommendation is
`tests/test_max-min.py::test_prerelease_order`. Its path goes through
`src/semver/_deprecated.py::min_ver` to the wrapper, with score 72,
distance 2 and both-revision evidence. It adds a test-to-helper edge
and reuses the existing helper-to-wrapper edge. The prerelease case
gains the same graph edge to its unchanged wrapper and keeps all 71
recommendations. Both Cached Property cases and all prior
recommendation scores and evidence match the predecessor. V5 now has
31 resolved, 88 conservative and nine changed-test recommendations.

The proof checks a direct, unshadowed pytest decorator, at least two
unique named columns, and a nonempty table of at most 64 rows and
256 literal string cells. It declines unsupported rows, decorator
options, rebinding and unproved keys. Each revision must establish
the full trail for that test. Winner selection and reflected dispatch
are outside the proof.

The remaining subclass draft misses are
`tests/test_deprecated_functions.py::test_should_raise_deprecation_warnings`,
`tests/test_parsing.py::test_should_parse_version_with_optional_minor_and_patch`
and `tests/test_replace.py::test_should_return_versioninfo_with_replaced_parts`.
The separate prerelease case retains its four draft misses. The receipt
records the unchanged false positives and uncertain selection.

## Factory equality with literal pytest dictionaries

`make evaluate-real-v5-parameter-dictionary-equality` checks the
`keyed-parameters-v1` predecessor and measures the new rule against the
same snapshots and frozen draft labels.
[Successor receipt](../datasets/real-v5-successors/parameter-dictionary-equality-v1.json) · [Engine hashes](../benchmarks/parameter-dictionary-equality-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Subclass comparison, keyed literal table | 29 / 106 | 27 | 2 | 3 | 74 | 0 |
| Subclass comparison, factory dictionary equality | 30 / 106 | 28 | 2 | 2 | 74 | 0 |
| V5 overall, keyed literal table | 128 / 239 | 75 | 52 | 7 | 104 | 1 |
| V5 overall, factory dictionary equality | 129 / 239 | 76 | 52 | 6 | 104 | 1 |

In both subclass revisions, `tests/test_parsing.py` lines 56–100 give
`test_should_parse_version_with_optional_minor_and_patch` five rows
with a string `version` and literal dictionary `expected`. Line 102
passes the string to `Version.parse` with
`optional_minor_and_patch=True`. The bound classmethod uses the optional
minor-and-patch pattern and returns `cls(**matched_version_parts)` on
normal completion at line 652 of `src/semver/version.py`.
Line 103 compares the exact source-class result with the exact builtin
dictionary. Python first tries the bound `Version.__eq__`, which uses
the wrapper returned by `_comparator`. The edit is inside that wrapper
at line 44.
[Base test](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/tests/test_parsing.py#L56-L103) · [Head test](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/tests/test_parsing.py#L56-L103)

The neighboring `test_should_parse_version` calls legacy `parse`.
The latter returns `Version.parse(version).to_dict()` at line 142 of
`src/semver/_deprecated.py`. The assertion uses two dictionaries and
the test stays unselected in the subclass case.

The sole added recommendation is
`tests/test_parsing.py::test_should_parse_version_with_optional_minor_and_patch`.
Its one call edge connects test line 103 to
`src/semver/version.py::_comparator.wrapper` at lines 41–52 in both
revisions. Distance is 1 and the score is 90. The five rows receive
one recommendation for the test definition.

Both SemVer graphs gain one edge. The prerelease case uses its
unchanged wrapper and keeps all 71 recommendations. Both Cached
Property analyses and all existing recommendation scores and evidence
match the predecessor. V5 now has 32 resolved, 88 conservative and
nine changed-test recommendations.

The rule shares the prior table limits of 64 rows and 256 cells.
It checks the two named columns, scalar dictionary keys and values, a
stable pytest binding, and the factory's callable and return class.
It declines row or argument unpacking, computed cells, rebound
parameters, and unsupported factory bindings. The evidence covers the
initial `__eq__` call. Its return value and subsequent dispatch are
outside the proof.

The subclass case retains two draft misses.
`tests/test_deprecated_functions.py::test_should_raise_deprecation_warnings`
and `tests/test_replace.py::test_should_return_versioninfo_with_replaced_parts`
remain unselected. The prerelease case retains its four draft misses.
The successor receipt records the exact discrepancies, including the
unchanged 52 false positives and one uncertain selection.

## Replacement equality with literal pytest keywords

`make evaluate-real-v5-parameter-replace-equality` replays the
`parameter-dictionary-equality-v1` predecessor and measures the new rule
against the same snapshots and frozen draft labels.
[Successor receipt](../datasets/real-v5-successors/parameter-replace-equality-v1.json) · [Engine hashes](../benchmarks/parameter-replace-equality-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Subclass comparison, factory dictionary equality | 30 / 106 | 28 | 2 | 2 | 74 | 0 |
| Subclass comparison, replacement equality | 31 / 106 | 29 | 2 | 1 | 74 | 0 |
| V5 overall, factory dictionary equality | 129 / 239 | 76 | 52 | 6 | 104 | 1 |
| V5 overall, replacement equality | 130 / 239 | 77 | 52 | 5 | 104 | 1 |

Both subclass revisions supply five rows at `tests/test_replace.py`
lines 34–43. The `version` and `expected` columns contain strings and
`parts` uses builtin `dict` with literal keyword values. At line 45,
the left factory supplies the exact `Version` receiver for
`replace(**parts)`. The right factory supplies another exact `Version`.
[Base test](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/tests/test_replace.py#L34-L45) · [Head test](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/tests/test_replace.py#L34-L45)

`Version.replace` calls `self.to_dict()` at line 668 of
`src/semver/version.py`. The field reader constructs a fresh dictionary
at lines 236–242. Its five properties read initialized private fields
directly. Line 669 updates the fresh dictionary using the collected
keywords, all of which fit the field dictionary and constructor. The
normal return at line 671 invokes the receiver's exact class through
builtin `type(self)(**version)`. The `TypeError` handler builds a
diagnostic and raises at line 678, so it has no normal exit to the
assertion. The initial `__eq__` binding is the edited comparison
wrapper at lines 41–52.
[Base method](https://github.com/python-semver/python-semver/blob/bd97cfcd595c882d92b73430d4bf5c880d6062dc/src/semver/version.py#L654-L678) · [Head method](https://github.com/python-semver/python-semver/blob/bc41390f388d88114e8529b17fe145c5af390cbb/src/semver/version.py#L654-L678)

The neighboring `test_replace_method_replaces_requested_parts` uses
the legacy helper. It returns
`str(Version.parse(version).replace(**parts))` at line 395 of
`src/semver/_deprecated.py`. The test remains unselected in the
subclass case.

The only added recommendation is
`tests/test_replace.py::test_should_return_versioninfo_with_replaced_parts`.
Its evidence connects test line 45 to
`src/semver/version.py::_comparator.wrapper` in both revisions.
The five rows contribute one definition-level recommendation at
distance 1 and score 90. Both SemVer graphs gain one edge. The
prerelease case uses its unchanged wrapper and keeps its 71
recommendations. Both Cached Property cases and all existing
recommendation scores and evidence match the predecessor.

The remaining subclass draft miss is
`tests/test_deprecated_functions.py::test_should_raise_deprecation_warnings`.
The prerelease case retains four draft misses. The successor receipt
also records the 52 retained false positives and one uncertain selection.

## Rich comparison paths to the changed helper

`make evaluate-real-v5-comparison-helper` checks the
`parameter-replace-equality-v1` predecessor and measures the new proof
on the same snapshots and frozen draft labels.
[Successor receipt](../datasets/real-v5-successors/comparison-helper-v1.json) · [Engine hashes](../benchmarks/comparison-helper-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Prerelease comparison, replacement equality | 71 / 105 | 31 | 40 | 4 | 30 | 0 |
| Prerelease comparison, comparison helper | 73 / 105 | 33 | 40 | 2 | 30 | 0 |
| V5 overall, replacement equality | 130 / 239 | 77 | 52 | 5 | 104 | 1 |
| V5 overall, comparison helper | 132 / 239 | 79 | 52 | 3 | 104 | 1 |

Both prerelease revisions bind the initial comparison to the unchanged
`_comparator.wrapper`. The wrapper accepts both exact `Version` operands
and forwards them unchanged at line 52. The bound operator calls
`Version.compare` and tests its result against zero. The comparison
method's conversion branches are skipped for these operands. The
constructor's integer normalization, initialized fields and tuple
reader establish equal core tuples. The source `_cmp` therefore
returns zero and the early return is bypassed. The actual call to
`Version._nat_cmp` is at line 416 before the change and line 412
after it.
[Base comparison method](https://github.com/python-semver/python-semver/blob/5dae7b67131299c8f955579bb239f2e580baa582/src/semver/version.py#L396-L425) · [Head comparison method](https://github.com/python-semver/python-semver/blob/0f30183605ebb1cb43de1a6b8baad5dcd754f685/src/semver/version.py#L392-L421)

| Test in `tests/test_compare.py` | Assertion range | Normalized core | Operator call before / after | Recommendation delta |
| --- | ---: | --- | --- | --- |
| `test_should_compare_prerelease_and_build_with_numbers` | 299–301 | `(1, 9, 1)` | `__lt__` at 479 / 475 | Added |
| `test_should_compare_version_info_objects` | 138 | `(0, 10, 4)` | `__ne__` at 475 / 471 | Added |
| `test_should_compare_prerelease_with_numbers_and_letters` | 129 | `(1, 9, 1)` | `__lt__` at 479 / 475 | Conservative evidence replaced by a resolved proof |

All three paths are proved independently in both revisions. Each edge
cites its assertion range and the helper's definition at lines 140–162
before or 140–160 after. The verified intermediate calls appear in its
evidence text. The selected edge is scoped to its test so a shared
wrapper cannot transfer the proof to another test. Each path has
distance 1 and score 83. The evidence upgrade previously had score
30 and distance 3. All original graph edges retain their evidence.
[Base tests](https://github.com/python-semver/python-semver/blob/5dae7b67131299c8f955579bb239f2e580baa582/tests/test_compare.py) · [Head tests](https://github.com/python-semver/python-semver/blob/0f30183605ebb1cb43de1a6b8baad5dcd754f685/tests/test_compare.py)

The prerelease case retains two draft misses,
`tests/test_compare.py::test_should_compare_version_dictionaries` and
`tests/test_pysemver-cli.py::test_should_process_parsed_cli_arguments`.
The subclass case retains its prior recommendations, including its
single draft miss. The successor receipt records all surviving
discrepancies and the uncertain selection.

Both SemVer graphs gain three test-scoped edges. In the subclass
case the additional edges only appear before the change. Its head
wrapper's acceptance tuple uses `type(self)`, a form outside this
guard proof, and its helper is unchanged. Both Cached Property
analyses match the predecessor. The replay has 36 resolved, 87
conservative and nine changed-test recommendations.

## Rich comparison through literal dictionary conversion

`make evaluate-real-v5-dictionary-comparison-helper` replays the
`comparison-helper-v1` predecessor and checks the successor against the
same snapshots and frozen draft labels.
[Successor receipt](../datasets/real-v5-successors/dictionary-comparison-helper-v1.json) · [Engine hashes](../benchmarks/dictionary-comparison-helper-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Prerelease comparison, comparison helper | 73 / 105 | 33 | 40 | 2 | 30 | 0 |
| Prerelease comparison, dictionary comparison helper | 74 / 105 | 34 | 40 | 1 | 30 | 0 |
| V5 overall, comparison helper | 132 / 239 | 79 | 52 | 3 | 104 | 1 |
| V5 overall, dictionary comparison helper | 133 / 239 | 80 | 52 | 2 | 104 | 1 |

The only added recommendation is
`tests/test_compare.py::test_should_compare_version_dictionaries` in the
prerelease case. Its first assertion is at line 167 in both revisions.
The left operand is `Version(0, 10, 4)`. The right operand is a builtin
`dict` with literal keyword values for `major`, `minor`, `patch`,
`prerelease` and `build`. Builtin `dict` has no subclass priority over the
verified source class. The wrapper's guard accepts this dictionary and
forwards it to `__ne__` at line 52. The bound operator invokes
`Version.compare` at line 475 before or 471 after.
[Base assertion](https://github.com/python-semver/python-semver/blob/5dae7b67131299c8f955579bb239f2e580baa582/tests/test_compare.py#L161-L167) · [Head assertion](https://github.com/python-semver/python-semver/blob/0f30183605ebb1cb43de1a6b8baad5dcd754f685/tests/test_compare.py#L161-L167)

`Version.compare` binds `cls = type(self)`, skips the string branch, and
converts the dictionary with `other = cls(**other)` at line 400 before
or 396 after. The explicit keys bind the constructor. Both normalized
core tuples are `(0, 10, 4)`, so the comparison bypasses the early
return and calls `Version._nat_cmp` at line 416 before or 412 after.
The resolved evidence is a test-scoped edge from line 167 to the helper
at lines 140–162 before and 140–160 after. It records the conversion and
intermediate call sites. Later assertions and the comparator's outcome
are outside the proof.
[Base conversion and helper call](https://github.com/python-semver/python-semver/blob/5dae7b67131299c8f955579bb239f2e580baa582/src/semver/version.py#L396-L416) · [Head conversion and helper call](https://github.com/python-semver/python-semver/blob/0f30183605ebb1cb43de1a6b8baad5dcd754f685/src/semver/version.py#L392-L412)

The new recommendation has distance 1 and score 84. The additional
incoming edge changes three existing scores from 83 to 84 with the
same scoring formula and evidence. The three tests in `tests/test_compare.py`
are `test_should_compare_prerelease_and_build_with_numbers`,
`test_should_compare_prerelease_with_numbers_and_letters`, and
`test_should_compare_version_info_objects`. There are no removals. The
replay has 37 resolved, 87 conservative and nine changed-test recommendations.

The subclass graph also gains a dictionary-to-helper proof in its base
revision. Its head wrapper's acceptance tuple uses `type(self)`, which the
guard proof declines. Its helper is unchanged, and its recommendations
match the predecessor. Both Cached Property analyses and all earlier
recommendation evidence remain intact.

The remaining draft misses are
`tests/test_pysemver-cli.py::test_should_process_parsed_cli_arguments`
in the prerelease case and
`tests/test_deprecated_functions.py::test_should_raise_deprecation_warnings`
in the subclass case. The successor records all 52 retained draft false
positives and the single uncertain selection. These measurements use
the frozen source labels and static analysis.

## Literal namespace callbacks through the CLI

`make evaluate-real-v5-namespace-callback` first replays the
`dictionary-comparison-helper-v1` predecessor. The successor measures the
same snapshots and frozen draft labels.
[Successor receipt](../datasets/real-v5-successors/namespace-callback-v1.json) · [Engine hashes](../benchmarks/namespace-callback-v1-preservation.json)

| Measurement | Selected / discovered | Draft TP | FP | FN | TN | Uncertain selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Prerelease comparison, dictionary helper | 74 / 105 | 34 | 40 | 1 | 30 | 0 |
| Prerelease comparison, namespace callback | 75 / 105 | 35 | 40 | 0 | 30 | 0 |
| V5 overall, dictionary helper | 133 / 239 | 80 | 52 | 2 | 104 | 1 |
| V5 overall, namespace callback | 134 / 239 | 81 | 52 | 1 | 104 | 1 |

In both prerelease snapshots, the pytest table at lines 48–101 of
`tests/test_pysemver-cli.py` supplies a callback, a fresh namespace and
a context manager. The row at lines 71–75 supplies `cmd_compare`,
`Namespace(version1="1.2.3", version2="1.2.3")` and
`does_not_raise("0")`. The local context factory is bound by
`contextlib.contextmanager` and immediately yields its supplied value.
Entry to the context at line 103 reaches the direct `func(args)` call at
line 104.
[Base test](https://github.com/python-semver/python-semver/blob/5dae7b67131299c8f955579bb239f2e580baa582/tests/test_pysemver-cli.py#L48-L105) · [Head test](https://github.com/python-semver/python-semver/blob/0f30183605ebb1cb43de1a6b8baad5dcd754f685/tests/test_pysemver-cli.py#L48-L105)

The public import resolves through `src/semver/__init__.py:23` to the
assignment at `src/semver/_deprecated.py:401–403`. The assignment
wraps the source-owned `cli.cmd_compare` with the deprecation factory.
After its supported warning prefix, the wrapper forwards the original
arguments at line 81. The CLI command reads `version1` and parses it at
line 70, then passes `version2` to `Version.compare` at line 71.
[Base wrapper](https://github.com/python-semver/python-semver/blob/5dae7b67131299c8f955579bb239f2e580baa582/src/semver/_deprecated.py#L398-L406) · [Head wrapper](https://github.com/python-semver/python-semver/blob/0f30183605ebb1cb43de1a6b8baad5dcd754f685/src/semver/_deprecated.py#L398-L406) · [Command](https://github.com/python-semver/python-semver/blob/0f30183605ebb1cb43de1a6b8baad5dcd754f685/src/semver/cli.py#L62-L71)

`Version.compare` converts the second string through the same bound parser
at line 398 before or 394 after. The source parser uses the default strict
pattern, captures three decimal strings and leaves the prerelease and build
groups empty for these inputs. The source constructor normalizes both core
tuples to `(1, 2, 3)`. Their equality bypasses the early return and reaches
`Version._nat_cmp` at line 416 before or 412 after. The neighboring compare
rows use `(1, 2, 3)` versus `(2, 1, 3)` and `(2, 4, 0)` versus
`(2, 1, 3)`. Their nonzero core comparisons return at line 413 before or
409 after. Those rows supply no helper evidence.
[Base compare](https://github.com/python-semver/python-semver/blob/5dae7b67131299c8f955579bb239f2e580baa582/src/semver/version.py#L396-L416) · [Head compare](https://github.com/python-semver/python-semver/blob/0f30183605ebb1cb43de1a6b8baad5dcd754f685/src/semver/version.py#L392-L412)

The only added recommendation is
`tests/test_pysemver-cli.py::test_should_process_parsed_cli_arguments`.
Its resolved edge cites line 104 in both revisions and the helper definition
at lines 140–162 before and 140–160 after. It has distance 1 and score 85.
The same additional incoming edge raises four scores from 84 to 85.
Their selected IDs and evidence are preserved. The four definitions in
`tests/test_compare.py` are `test_should_compare_prerelease_and_build_with_numbers`,
`test_should_compare_prerelease_with_numbers_and_letters`,
`test_should_compare_version_dictionaries` and
`test_should_compare_version_info_objects`.

All earlier graph edges retain their evidence. The subclass case gains
the callback edge in both revisions to its unchanged helper and retains
all 31 recommendations. Both Cached Property reports match their
predecessors. The successor contains 38 resolved, 87 conservative and
nine changed-test recommendations. The remaining v5 draft miss is
`tests/test_deprecated_functions.py::test_should_raise_deprecation_warnings`
in the subclass case. The 52 draft false positives and one uncertain
selection are retained.

The proof covers the source route under ordinary pytest collection, with
standard-library context entry and the deprecation wrapper's normal
forwarding path. It declines captured collection hooks and does not
establish external plugin or warning-filter behavior. These counts measure
static evidence against draft dependency labels.
