# Milestone 9C literal rule tables

## Source decision before implementation

The starting tree is clean at merged Slugify milestone
`614e18bfd5d7f38b0a1a8564ba470f2fc34ded20`. PR #19 and post-merge CI passed.
Starting source, corpus, baseline, UI and historical report hashes are recorded
under `reports/module-data-before/`.

The `inflection_rules` snapshot changes only the literal `PLURALS` and
`SINGULARS` sequences in `inflection.py` and the literal
`SINGULAR_TO_PLURAL` sequence in `test_inflection.py`. Each module is an
independent initialization seed. `test_camelize` currently has evidence to
its own changed test module. A production-only filter would leave that route.

`pluralize` reads `PLURALS`, `singularize` reads `SINGULARS`, and
`tableize` calls `pluralize`. Three parametrized tests additionally read
the changed test table in their decorators. The six draft affected definitions
must remain selected through these reads. `test_camelize` uses an unchanged
literal parameter table and calls `camelize`, whose source uses regex/string
operations and a recursive call without reading either rule table.

The proposed bounded proof requires existing top-level literal sequence bindings
to account for the complete module edit. It inspects the test's body, defaults
and supported parameter decorators and follows source calls and data references.
A read of any changed binding retains fallback, including transitive reads and
decorator data. Eager initialization must use supported data operations, with
mutations confined to source-owned literal containers. Unknown calls, escaped
values, rebinding, re-export ambiguity, custom decorators, deleted bindings and
exhausted budgets retain fallback. Both revisions must prove exclusion. The
contribution is filtered for one module seed at a time.

The unchanged `_irregular` initializer updates the owned rule lists with
literal-derived strings. Its effects require an explicit source audit before
exclusion can be supported. No branch-sensitive empty/uncountable bypass is
planned. Titleize's body edit and PyISO8601's added validator have different
change shapes and remain regression controls.

## Implemented boundary

`module_data.py` recognizes complete edits confined to existing top-level
assignments of literal list/tuple rows. The outer container type, names,
assignment structure and
all other module AST nodes must match. Added or deleted bindings, rebinding,
nonliteral values and unrelated body edits decline. All reachable imported
source modules must either match exactly between revisions or satisfy this
same table-edit shape. Alias imports and re-exports keep conservative behavior.

The query inspects source data reads through direct calls, transitive calls,
defaults and a narrow literal `pytest.mark.parametrize` form. Reads of edited
tables retain fallback even when arguments might bypass the table at runtime.
A callback is supported only as source inspected for known regex substitution.
Unknown calls, namespace escapes, mutation during test execution, custom test
lifecycle and unsupported decorators retain fallback. Source functions are
scanned across all syntactic branches. Recursion without an eager effect is
scanned once per active callable, within a 12,000-step and 24-level bound.

The initialization audit permits literal module data, plain function headers,
known regex/string/scalar operations and literal-data source helpers. Import-time
mutations are limited to `insert`, `append` and `add` on source-owned
literal containers, with data-only arguments. This covers the existing
`_irregular` registration routine. Only a bare mutator receiver may reference
an edited container during initialization; consuming its contents, including
copying rows or using them in a condition, retains fallback. A bare default or
parameter-decorator reference may register data, but each invoked test/function
checks that reference again. Calls inside defaults receive the normal effects
audit. Global rebinding, aliasing the rule data
at module scope, calls to unavailable helpers and escaping a module or callable
decline the proof. This audit describes the captured source and supported
standard-library contracts. Captured `conftest.py` files and custom module or
function test hooks also decline; external pytest configuration is not inferred.
Changed parameter tables must keep literal rows with the decorator's declared
arity and remain unmutated, so a collection failure cannot be hidden by excluding
an unrelated test. Unchanged parameter expressions retain the ordinary data-read
audit; their shape is not inferred or changed by this contribution.

Each active module seed has its own traversal. The production and test-data
contributions are filtered independently for each test, using both revisions.
Other source seeds can still support the same test. Graph edges remain the
original typed evidence. The public report continues to use schema 2.0.

## Regression and scope review

The pre-change suite recorded three expected failures with 16 controls passing.
These failures covered simultaneous production/test table changes, a test sharing
its changed parameter module, and audited rule registration. Additional controls
cover direct/transitive readers, defaults, aliases/re-exports, mutation, escaped
data, rebinding, eager effects, unknown decorators, deleted bindings, before-only
reads, recursive readers and budget exhaustion.

The first exploratory replay also narrowed the titleize case because that snapshot
has an edited test table. Review identified its separate production function-body
change. The final query declines whenever a reachable module has another change
shape, and the entire titleize analysis now matches its predecessor. This boundary
has a focused regression.

Final source review found that the initial eager audit could hide a table read
when an initializer copied rows into another global or used the table as a
condition. It also missed function setup/teardown and captured conftest hooks.
Six added source-only controls failed against that candidate. The final proof
retains every one, including a helper invoked from a default expression, while
the plain literal registration control still qualifies. The corpus measurement
does not change. Only current unpublished engine/receipt hashes were refreshed.

Three further failing controls cover a rule-list to tuple replacement and
malformed or mutated changed parameter rows. These also retain fallback. An
initial collection guard rejected unchanged comprehensions and concatenations;
the final guard audits this contribution's changed parameter binding and keeps
the normal data-read audit for other expressions. The complete Inflection
measurement and exact 14 removals still match.

A test-scoped replay disables the new filter and reproduces the exact historical
`legacy-dispatch-v1` analysis hash for `inflection_rules`. Every current
recommendation passes the typed evidence validator. The 40 nodes, 70 edges,
two changed module IDs, complete source and 173 diagnostics match the preceding
report. Only the same 14 tests leave the impact list, from 38 to 24.

## Exact measurement and evidence

There are **14 removed IDs and zero added IDs**. Each removed definition uses
unchanged parameter data and a table-free formatting, case, ordinal or
transliteration call chain. Both its production-module and test-module routes
are excluded after the separate source proofs.

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
test_inflection.py::test_titleize
test_inflection.py::test_underscore
```

All six affected definitions remain selected.

```text
test_inflection.py::test_pluralize_plural
test_inflection.py::test_pluralize_plurals
test_inflection.py::test_pluralize_singular
test_inflection.py::test_singularize_plural
test_inflection.py::test_tableize
test_inflection.py::test_uncountable_word_is_not_greedy
```

Three parameterized readers retain their original changed-test-table paths.
`test_uncountable_word_is_not_greedy` retains conservative evidence because
its test-time set mutation and exception flow exceed the exclusion boundary.
The other four retained tests lose their unrelated test-module contribution
and receive an existing production path, in both revisions.

| Test suffix | Current trail after the test | Before → after score | Before → after distance |
| --- | --- | ---: | ---: |
| `test_pluralize_plurals` | `pluralize → inflection module` | 50 → 40 | 1 → 2 |
| `test_tableize` | `tableize → inflection module` | 50 → 40 | 1 → 2 |
| `test_pluralize_empty_string` | `pluralize → inflection module` | 50 → 40 | 1 → 2 |
| `test_uncountability` | `pluralize → inflection module` | 50 → 40 | 1 → 2 |

All eight reasons remain conservative module/import dependencies. Four
recommendations match their full previous objects. The four path replacements
have exact regression assertions and retain `both` revision evidence. The
existing distance-based scoring formula accounts for their score change.

| Measurement | Selected before → after | TP / FP / FN / TN before → after |
| --- | ---: | --- |
| Inflection rules | 22/22 → 8/22 | 6 / 16 / 0 / 0 → 6 / 2 / 0 / 14 |
| Expanded v3 | 85/120 → 71/120 | 42 / 43 / 0 / 23 → 42 / 29 / 0 / 37 |

| Case or repository | Selected / discovered | TP / FP / FN / TN | Uncertain selected / unselected | Resolved / conservative / changed |
| --- | ---: | ---: | ---: | ---: |
| inflection_rules | 8/22 | 6 / 2 / 0 / 14 | 0 / 0 | 0 / 8 / 0 |
| inflection_title | 22/22 | 1 / 21 / 0 / 0 | 0 / 0 | 1 / 21 / 0 |
| iso8601_errors | 2/8 | 2 / 0 / 0 / 6 | 0 / 0 | 2 / 0 / 0 |
| iso8601_validator | 8/8 | 2 / 6 / 0 / 0 | 0 / 0 | 0 / 6 / 2 |
| ordered_set_pop | 1/30 | 1 / 0 / 0 / 17 | 0 / 12 | 0 / 1 / 0 |
| ordered_set_syntax | 30/30 | 30 / 0 / 0 / 0 | 0 / 0 | 30 / 0 / 0 |

| Case or repository | Selected / discovered | TP / FP / FN / TN | Uncertain selected / unselected | Resolved / conservative / changed |
| --- | ---: | ---: | ---: | ---: |
| jpvanhal/inflection | 30/44 | 7 / 23 / 0 / 14 | 0 / 0 | 1 / 29 / 0 |
| micktwomey/pyiso8601 | 10/16 | 4 / 6 / 0 / 6 | 0 / 0 | 2 / 6 / 2 |
| rspeer/ordered-set | 31/60 | 31 / 0 / 0 / 17 | 0 / 12 | 30 / 1 / 0 |
| V3 overall | 71/120 | 42 / 29 / 0 / 37 | 0 / 12 | 33 / 36 / 2 |

The two remaining rule-case false positives are `test_pluralize_empty_string`
and `test_uncountability`. Argument-sensitive bypass of a table read is outside
this slice. Titleize's 21 and the validator-addition case's six false positives
remain. Expanded v3 keeps all 12 uncertain definitions unselected. All six v2
analyses match their predecessor, including 327/581 selected and 13/22 uncertain
selections. Authored and v1 stable report bytes match as well.

## Receipts and next slice

New `literal-tables-v1` receipts pin the current v3 measurement and the identical
v2 measurement under the new engine. They link the preserved `legacy-dispatch-v1`
receipts and their full historical chains. Fresh wrapper 9.0 and holdout wrapper
6.0 use separate output filenames. Original v3 discovery, the 90-definition
denominator and its 30 excluded definitions remain preserved.

Labels remain agent drafts pending independent review. The next bounded 9C
slice can study the PyISO8601 validator-addition/export path and its six remaining
false positives, with its original labels and evidence as controls. Titleize's
function-body edit needs its own source pattern. Live hosting and the human
pilot stay deferred. [Verification record](VALIDATION.md#milestone-9c--literal-rule-table-dependencies)
