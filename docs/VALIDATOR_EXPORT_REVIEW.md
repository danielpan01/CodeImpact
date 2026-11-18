# Milestone 9C validator addition and package exports

## Baseline trace

Local and remote main started clean at PR #20's merge,
`c1bfd751b0c6f4f64434e3c6d90d08166346b6df`. Before implementation the pinned
`iso8601_validator` report matched the `literal-tables-v1` analysis hash and
passed typed evidence validation. It selected all eight definitions, with
2 draft true positives, 6 draft false positives, 0 false negatives and
0 true negatives.

The implementation file adds `is_iso8601` with builtin annotations and a
deferred body that matches the existing compiled regex. The package initializer
explicitly re-exports that function and changes its literal `__all__` sequence.
The head source contains `"is_iso8601" "ParseError"` exactly. The parsed list
has one entry `is_iso8601ParseError`, with neither original string as a
separate entry. The named import still binds both functions and classes
independently of this list. The wildcard import surface can change, including
an import error for the missing concatenated name.

| Definition in `iso8601/test_iso8601.py` | Actual before/after evidence |
| --- | --- |
| `test_parse_invalid_date` | Test itself changed, distance 0, score 90 |
| `test_parse_valid_date` | Test itself changed, distance 0, score 90 |
| `test_fixedoffset_eq` | Test → own module → package initializer, distance 2, score 32 |
| `test_hypothesis_valid_datetimes_with_timezone` | Test → own module → package initializer, distance 2, score 32 |
| `test_hypothesis_valid_naive_datetimes` | Test → own module → package initializer, distance 2, score 32 |
| `test_iso8601_regex` | Test → own module → package initializer, distance 2, score 32 |
| `test_parse_no_timezone_different_default` | Test → own module → package initializer, distance 2, score 32 |
| `test_parse_utc_different_default` | Test → own module → package initializer, distance 2, score 32 |

All eight paths have revision `both`. The six package paths use the line 13
import edge followed by the conservative initialization edge to
`iso8601/__init__.py::<module>`. The module graph records `from . import iso8601`
as an import of the package as well as its child. The added function is its
own active seed. The implementation and test module aggregate passes reach
only the two changed tests. Their head bodies add assertions for the validator,
and the zero-hop paths take priority over the new head-only calls.

The four plain tests use the same regex, fixed offset constructor, parser or
UTC binding in both revisions. The two Hypothesis tests also call the unchanged
parser, with values supplied by decorated test execution. Keep their fallback
unless that separate execution mechanism is supported. The proof must also
account for module collection, including the stable, known decorators on sibling
tests. Record local baseline output under `reports/validator-before/`.

## Supported proof

The change must add plain, public functions in a direct child module and add
matching explicit re-exports in the top-level package initializer. The child
must have the same remaining AST, and the initializer may only add the named
imports and edit a literal string sequence assigned to `__all__`. The proof
checks binding uniqueness, the new functions' definition-time headers and
the unchanged implementation and initialization in each revision. An added
definition's body is deferred. The proof uses a small set of standard library
operations and rejects unproved calls, namespace access or mutation. It caps
the audited trees at 12,000 AST nodes per module.

An eligible test is a plain top-level synchronous function without parameters
or decorators. Its module can import the package, child or existing members
explicitly. The test's body must use only operations with known source bindings
or supported data operations. Test collection is checked in both revisions.
The two known sibling collection forms modeled here are literal-row pytest
parametrization and Hypothesis datetime strategy construction. Decorating the
test being considered still places its execution outside the proof. A captured
conftest, unknown setup, wildcard import, ambiguous or rebound import, dynamic
lookup, namespace escape, unsupported initializer or exhausted audit retains
the original fallback.

The analyzer walks the package initializer's active seed separately. When both
revisions pass the audit, it drops only that test's contribution from the package
seed. The implementation module's existing aggregate pass already distinguishes
the added callable from unchanged members. The added callable and the two changed
tests still have their own seeds. All original typed edges, including the import
edges and revision-specific source spans, remain available for evidence.

## Measured change

Four recommendations were removed, and none were added.

| Removed ID | Unchanged members that the test uses |
| --- | --- |
| `iso8601/test_iso8601.py::test_fixedoffset_eq` | `FixedOffset` |
| `iso8601/test_iso8601.py::test_iso8601_regex` | `ISO8601_REGEX.match` |
| `iso8601/test_iso8601.py::test_parse_no_timezone_different_default` | `FixedOffset` and `parse_date` |
| `iso8601/test_iso8601.py::test_parse_utc_different_default` | `FixedOffset`, `parse_date` and `UTC` |

The remaining recommendations, in score order, retain their exact original
objects, including typed edge IDs, score, distance and revision.

| Selected ID | Evidence |
| --- | --- |
| `iso8601/test_iso8601.py::test_parse_invalid_date` | Test itself changed, score 90 |
| `iso8601/test_iso8601.py::test_parse_valid_date` | Test itself changed, score 90 |
| `iso8601/test_iso8601.py::test_hypothesis_valid_datetimes_with_timezone` | Same package fallback path, score 32 |
| `iso8601/test_iso8601.py::test_hypothesis_valid_naive_datetimes` | Same package fallback path, score 32 |

The graph still has 23 nodes, 36 edges and six changed symbols. Only the four
removed tests leave the impacted list, which goes from 7 to 3. Package fallback
explanations for the case drop from six to two. Both remaining draft false
positives use Hypothesis to supply inputs and wrap test execution. The proof
retains them because it models only those decorators' construction during
collection.

| Scope | Selected before → after | TP / FP / FN / TN before → after |
| --- | ---: | --- |
| Validator addition | 8/8 → 4/8 | 2 / 6 / 0 / 0 → 2 / 2 / 0 / 4 |
| PyISO8601 overall | 10/16 → 6/16 | 4 / 6 / 0 / 6 → 4 / 2 / 0 / 10 |
| Expanded v3 overall | 71/120 → 67/120 | 42 / 29 / 0 / 37 → 42 / 25 / 0 / 41 |

All 12 uncertain v3 definitions stay unselected. The other five v3 analyses
have their prior hashes. This includes the separate validator errors case and
the two Inflection cases. All authored, v1 and v2 results match the predecessor.
Draft labels describe source dependencies and still await independent review.

The versioned `additive-exports-v1` receipts record the current v2 engine replay
and current v3 measurement. They link the preserved `literal-tables-v1` receipts.
The application report stays at schema 2.0. Full test, determinism and integrity
results are in [the validation record](VALIDATION.md#milestone-9c--validator-addition-and-package-exports).
