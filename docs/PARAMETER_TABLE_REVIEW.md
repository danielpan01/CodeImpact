# Milestone 9C test parameter tables and production body edits

## Baseline trace

Local and remote main started clean at PR #21,
`7f1f99d6b565fa90833f09c864661c45fb7629fe`. Before editing, the
`inflection_title` analysis hash matched `additive-exports-v1`. All 22
definitions were selected, with one draft true positive and 21 draft false
positives. Typed paths and revision evidence passed validation.

The production change modifies only the body of `inflection.py::titleize`.
It changes the regex character class to include Unicode word characters and
adds a `.title()` call to the text passed to the substitution. The test
module adds two literal rows to `MIXTURE_TO_TITLEIZED`, for `ana índia` and
`Ana Índia`. Its test definitions are unchanged.

The production function is an active seed. Its walk reaches only
`test_inflection.py::test_titleize`, with a direct call in both revisions.
The production module is an aggregate seed. That walk reaches the same test
through `titleize` and its module initialization edge. The test-module seed
reaches all 22 tests. For `test_titleize`, resolved call evidence takes
priority. The other 21 use a one-hop conservative path to their own module,
with distance 1, score 50 and revision `both`.

Each other test was checked against both production walks and its source
dependencies. The table below groups all 21 candidates. None has a path to the
production seed in either walk. Several call functions used by `titleize`,
such as `humanize` or `underscore`. Those calls follow the dependency edges
away from their caller and do not reach `titleize`.

| Tests in `test_inflection.py` | Source dependencies |
| --- | --- |
| `test_camelize`, `test_camelize_with_lower_downcases_the_first_letter`, `test_camelize_with_underscores` | `camelize`, plus unchanged camel-case parameter data where applicable |
| `test_underscore`, `test_humanize`, `test_dasherize` | Their corresponding formatter and unchanged parameter data |
| `test_ordinal`, `test_ordinalize` | The corresponding ordinal formatter and unchanged number rows |
| `test_parameterize`, `test_parameterize_and_normalize`, `test_parameterize_with_custom_separator`, `test_parameterize_with_multi_character_separator`, `test_parameterize_with_no_separator` | `parameterize`, unchanged input/expected rows and string replacement for the multi-character separator |
| `test_pluralize_empty_string`, `test_pluralize_plural`, `test_pluralize_plurals`, `test_pluralize_singular`, `test_singularize_plural`, `test_uncountability` | `pluralize` and/or `singularize`, with unchanged data, including `UNCOUNTABLES` for its decorator |
| `test_tableize` | `tableize`, its `pluralize` and `underscore` dependencies, and unchanged tableize rows |
| `test_uncountable_word_is_not_greedy` | Plural/singular readers and temporary mutation of `UNCOUNTABLES` with exception-safe cleanup |

The proof to test is whether the test-module table contribution can be
excluded independently. It must use verified initialization and collection
behavior in each revision and retain fallback if it cannot audit a test's
use of shared data. The before report and per-seed replay are in
`reports/titleize-before/`.

## Implemented boundary

The existing literal-table proof still starts with a complete table-only edit
of the test module. The mixed case applies only to tests defined in that
module. In each reachable production file that uses the new branch, exactly
one existing, undecorated, top-level function may change. Its header and
all other module statements must match. The existing audit still checks
imports, function headers, module initialization and the selected test's
calls and data reads in both revisions. An eager call to an edited function,
including through a wrapper or a default argument, keeps fallback.

For the mixed case, every changed binding must be registered directly in a
supported `pytest.mark.parametrize` decorator. The registered rows must be
literal, with the declared arity. Other references to the changed table keep
fallback, including aliases and test-time mutation. Multiple supported tests
may share a table. Each is still a reader. Unproved decorators, signatures
and collection hooks, unsupported initialization and exhausted budgets retain
fallback. Parameter variants stay grouped by test definition.

Each successful proof omits the contribution of the edited test module for
that test. The existing resolved and aggregate production traversals still
run with their original seeds and edges. Other table-reading tests retain
their module paths. The application report stays at schema 2.0.

## Measured change

The two remaining recommendations retain their exact evidence.

| Selected ID | Evidence path | Revision | Score |
| --- | --- | --- | ---: |
| `test_inflection.py::test_titleize` | `test_titleize → inflection.py::titleize` | both | 81 |
| `test_inflection.py::test_uncountable_word_is_not_greedy` | `test_uncountable_word_is_not_greedy → test_inflection.py::<module>` | both | 50 |

The second test's temporary mutation of the shared production set
`UNCOUNTABLES` and its `try/finally` cleanup exceed the body audit. Its one
remaining draft false positive keeps the original conservative path. The
refinement does not infer argument-based bypasses of the production rules.

There are zero new recommendations and no evidence replacements. The following
20 IDs lose their test-table contribution and have no independent production
path.

```text
test_inflection.py::test_camelize
test_inflection.py::test_camelize_with_lower_downcases_the_first_letter
test_inflection.py::test_camelize_with_underscores
test_inflection.py::test_dasherize
test_inflection.py::test_humanize
test_inflection.py::test_ordinal
test_inflection.py::test_ordinalize
test_inflection.py::test_parameterize
test_inflection.py::test_parameterize_and_normalize
test_inflection.py::test_parameterize_with_custom_separator
test_inflection.py::test_parameterize_with_multi_character_separator
test_inflection.py::test_parameterize_with_no_separator
test_inflection.py::test_pluralize_empty_string
test_inflection.py::test_pluralize_plural
test_inflection.py::test_pluralize_plurals
test_inflection.py::test_pluralize_singular
test_inflection.py::test_singularize_plural
test_inflection.py::test_tableize
test_inflection.py::test_uncountability
test_inflection.py::test_underscore
```

The report keeps 40 nodes, 70 edges and three changed symbols. The impact list
goes from 24 to 4 by dropping the same 20 tests. Recommendations keep the same
resolved call count of one. Conservative explanations drop from 21 to one.

| Scope | Selected before → after | TP / FP / FN / TN before → after |
| --- | ---: | --- |
| Titleize case | 22/22 → 2/22 | 1 / 21 / 0 / 0 → 1 / 1 / 0 / 20 |
| Inflection overall | 30/44 → 10/44 | 7 / 23 / 0 / 14 → 7 / 3 / 0 / 34 |
| Expanded v3 overall | 67/120 → 47/120 | 42 / 25 / 0 / 41 → 42 / 5 / 0 / 61 |

All 12 uncertain definitions remain unselected. The other five v3 analyses
and all authored, v1 and v2 measurements match their predecessors.
The `parameter-tables-v1` receipts link the preserved additive-export and
literal-table history. Labels remain drafts pending independent review.
[Verification record](VALIDATION.md#milestone-9c--test-parameter-tables-and-production-body-edits)
