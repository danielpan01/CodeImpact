# Milestone 9B Slugify legacy dispatch

## Source decision before implementation

Starting commit is merged descriptor milestone `383b819667f91e3bcf6a39e23c1cf5a7b6b3554e`.
The boundary case changes the body of `_modern_truncate` and adds a test file.
In both revisions `tests/test_legacy.py::TestSlugify.test_accented_text` imports
`slugify` from the package's static wildcard export. Its three literal-text
calls omit the keyword-only `algorithm`, which defaults to `'legacy'`.
Validation accepts that value, the equality guard selects `_legacy_slugify`,
and the immediate return bypasses the modern branch. The selected callable
comes from `slugify/_legacy.py`. The prior recommendation is a conservative
path directly to the changed implementation module.

The proposed proof checks one known literal dispatch into a separate,
unchanged source module. It audits initialization and re-exports, binds the
actual arguments and defaults, and inspects the selected branch for source
dependencies. The default legacy backend import alternatives name fixed
external modules outside the captured project. This proof concerns the captured
source graph and assumes those external data-processing APIs follow their
ordinary contracts. Assigning a project module or an unknown value to the
import selector, escaping a callable, unknown code during eager initialization,
or a source reference back to the edited implementation keeps fallback.

Positive modern, mixed, overridden and uncertain paths keep their evidence.
The ASCII control changes the selected legacy module itself. The proof must
decline on that revision pair before excluding any aggregate contribution.

## Implemented boundary

The analyzer uses the existing top-level body-change inventory, source re-export
resolver, argument binder and literal guard evaluation. Applicability requires
one existing plain function-body edit in the aggregate module. Each test must
use a bounded sequence of direct calls and data assertions. Every call must
bind a known literal dispatcher option and take a terminal return into an
unchanged source module. The other branch must resolve to a function on the
edited call chain. The proof checks both snapshots before removing the test's
aggregate contribution. Resolved and other active paths run through the
existing propagation.

For a `unittest.TestCase` method, the proof requires an unambiguous, direct
subclass of the standard `TestCase` with only distinct undecorated test methods,
docstrings or `pass` in its class body. This keeps construction, execution and
cleanup under the supported unittest lifecycle. Other class members, including
`__new__` and `doCleanups` overrides, keep conservative fallback.

The eager audit follows captured package and test imports, checks defaults and
annotations, and permits a limited set of passive standard-library data forms
and local data transformations. A call that reaches the edited function during
initialization keeps the path. Runtime traversal in the selected module checks
same-module helper calls, rejects escaped callable and namespace values, and
carries only stable scalar bindings into branch decisions. The fixed default
backend alternatives are absent from the captured module inventory. The local
import handle may only feed an immediate named external call with a data
argument and a string result annotation. This boundary treats those external
APIs as opaque data processors. It models captured source dependencies and
does not infer arbitrary third-party import or plugin behavior.

Unknown input, rebound callables or defaults, unknown eager dependencies,
arbitrary runtime imports, callback escape, compound test control flow and
exhausted budgets keep fallback. The proof uses the existing 2,000-step
argument and 16-level call bounds alongside the 12,000-step source audit
bound. Partial-bound modern calls and explicit overrides keep their existing
resolution. The ASCII case changes the selected legacy module itself, so it
fails the unchanged-dependency check. The proof adds no Unicode-mode rule.

## Regression and evidence

Two tests for omitted and explicit legacy options failed before the fix.
The predecessor initially also missed the synthetic rebinding test because
its only callable was shadowed. The control now has a separate stable import
that provides an aggregate contribution, so it exercises the new filter.
Replaying the original behavior with the new filter disabled reproduces the
two intended failures with 23 controls passing. Further red controls caught
a possible eager call into the edited body and an unconstrained runtime-import
result. The final audit declines both.

The prepublication lifecycle review added source-only tests that call the
edited function through `__new__` and `doCleanups`, with only a legacy call in
each test body. Both initially lost their recommendations. They now retain
validated module/import evidence in both revisions. A plain `TestCase` with
the same test body still qualifies for exclusion. This correction preserves
the exact 66 removed Boundary IDs and changes only hash metadata in the
unpublished receipts.

A test-scoped predecessor replay reproduces the complete, frozen
`descriptor-binding-v1` analysis hash and validates both reports. Every retained
recommendation matches its score, distance, reason, path, edge IDs and revision
evidence. All 189 graph nodes, 336 edges, source files, change records and 646
diagnostics match. The impact list falls from 117 to 51, losing the same 66 IDs.

## Measurements

| Population | Selected before → after | TP / FP / FN / TN before → after | Uncertain selected / unselected |
| --- | ---: | --- | ---: |
| Boundary | 108/133 → 42/133 | 28 / 80 / 0 / 22 → 28 / 14 / 0 / 88 | 0 / 3 |
| ASCII | 100/126 → 100/126 | 63 / 37 / 0 / 23 → 63 / 37 / 0 / 23 | 0 / 3 |
| Slugify overall | 208/259 → 142/259 | 91 / 117 / 0 / 45 → 91 / 51 / 0 / 111 | 0 / 6 |
| V2 overall | 393/581 → 327/581 | 109 / 271 / 0 / 179 → 109 / 205 / 0 / 245 | 13 / 9 |

All 28 affected Boundary IDs remain selected. The Boundary case retains
28 resolved, 12 conservative and two changed-test recommendations.
Conservative recommendations fall from 78 to 12 in Boundary and from 335
to 269 in v2. V2 retains 51 resolved and seven changed-test recommendations.
The other five v2 case analyses match their predecessor hashes. Authored
and v1 reports match byte for byte, and the full expanded v3 measurement
matches, including 85/120 selected and all 12 uncertain definitions unselected.

There are **zero added IDs**. The **66 removed IDs** are all labeled unaffected
in the existing draft and all use the verified legacy dispatch route.

```text
tests/test_legacy.py::TestSlugify.test_accented_text
tests/test_legacy.py::TestSlugify.test_accented_text_with_non_word_characters
tests/test_legacy.py::TestSlugify.test_contains_numbers
tests/test_legacy.py::TestSlugify.test_custom_separator
tests/test_legacy.py::TestSlugify.test_cyrillic_text
tests/test_legacy.py::TestSlugify.test_differently_cased_stopword_match
tests/test_legacy.py::TestSlugify.test_ends_with_number
tests/test_legacy.py::TestSlugify.test_extraneous_seperators
tests/test_legacy.py::TestSlugify.test_html_decimal_off
tests/test_legacy.py::TestSlugify.test_html_decimal_on
tests/test_legacy.py::TestSlugify.test_html_entities_off
tests/test_legacy.py::TestSlugify.test_html_entities_on
tests/test_legacy.py::TestSlugify.test_html_hexadecimal_off
tests/test_legacy.py::TestSlugify.test_html_hexadecimal_on
tests/test_legacy.py::TestSlugify.test_max_length
tests/test_legacy.py::TestSlugify.test_max_length_cutoff_not_required
tests/test_legacy.py::TestSlugify.test_multi_character_separator
tests/test_legacy.py::TestSlugify.test_multiple_stopword_occurances
tests/test_legacy.py::TestSlugify.test_multiple_stopwords
tests/test_legacy.py::TestSlugify.test_non_word_characters
tests/test_legacy.py::TestSlugify.test_numbers_and_symbols
tests/test_legacy.py::TestSlugify.test_numbers_only
tests/test_legacy.py::TestSlugify.test_phonetic_conversion_of_eastern_scripts
tests/test_legacy.py::TestSlugify.test_regex_pattern_keep_underscore
tests/test_legacy.py::TestSlugify.test_replacements
tests/test_legacy.py::TestSlugify.test_replacements_german_umlaut_custom
tests/test_legacy.py::TestSlugify.test_save_order
tests/test_legacy.py::TestSlugify.test_starts_with_number
tests/test_legacy.py::TestSlugify.test_stopword_removal
tests/test_legacy.py::TestSlugify.test_stopword_removal_casesensitive
tests/test_legacy.py::TestSlugify.test_stopwords_with_different_separator
tests/test_legacy.py::TestSlugify.test_word_boundary
tests/test_legacy.py::TestSlugifyUnicode.test_accented_text
tests/test_legacy.py::TestSlugifyUnicode.test_accented_text_with_non_word_characters
tests/test_legacy.py::TestSlugifyUnicode.test_contains_numbers
tests/test_legacy.py::TestSlugifyUnicode.test_custom_separator
tests/test_legacy.py::TestSlugifyUnicode.test_cyrillic_text
tests/test_legacy.py::TestSlugifyUnicode.test_differently_cased_stopword_match
tests/test_legacy.py::TestSlugifyUnicode.test_emojis
tests/test_legacy.py::TestSlugifyUnicode.test_ends_with_number
tests/test_legacy.py::TestSlugifyUnicode.test_extraneous_seperators
tests/test_legacy.py::TestSlugifyUnicode.test_html_decimal_off
tests/test_legacy.py::TestSlugifyUnicode.test_html_decimal_on
tests/test_legacy.py::TestSlugifyUnicode.test_html_entities_off
tests/test_legacy.py::TestSlugifyUnicode.test_html_entities_on
tests/test_legacy.py::TestSlugifyUnicode.test_html_hexadecimal_off
tests/test_legacy.py::TestSlugifyUnicode.test_html_hexadecimal_on
tests/test_legacy.py::TestSlugifyUnicode.test_max_length
tests/test_legacy.py::TestSlugifyUnicode.test_max_length_cutoff_not_required
tests/test_legacy.py::TestSlugifyUnicode.test_multi_character_separator
tests/test_legacy.py::TestSlugifyUnicode.test_multiple_stopword_occurances
tests/test_legacy.py::TestSlugifyUnicode.test_multiple_stopwords
tests/test_legacy.py::TestSlugifyUnicode.test_non_word_characters
tests/test_legacy.py::TestSlugifyUnicode.test_numbers_and_symbols
tests/test_legacy.py::TestSlugifyUnicode.test_numbers_only
tests/test_legacy.py::TestSlugifyUnicode.test_phonetic_conversion_of_eastern_scripts
tests/test_legacy.py::TestSlugifyUnicode.test_regex_pattern_keep_underscore
tests/test_legacy.py::TestSlugifyUnicode.test_replacements
tests/test_legacy.py::TestSlugifyUnicode.test_replacements_german_umlaut_custom
tests/test_legacy.py::TestSlugifyUnicode.test_save_order
tests/test_legacy.py::TestSlugifyUnicode.test_save_order_rtl
tests/test_legacy.py::TestSlugifyUnicode.test_starts_with_number
tests/test_legacy.py::TestSlugifyUnicode.test_stopword_removal
tests/test_legacy.py::TestSlugifyUnicode.test_stopword_removal_casesensitive
tests/test_legacy.py::TestSlugifyUnicode.test_stopwords_with_different_separator
tests/test_legacy.py::TestSlugifyUnicode.test_word_boundary
```

The 14 remaining Boundary false positives include compiled regex arguments,
backend/exception tests, CLI forwarding and compound test bodies. The ASCII
case contributes another 37. These are draft source-dependency labels, with
independent review pending. The next roadmap slice is 9C, beginning with one
bounded module-data pattern from the v3 Inflection or PyISO8601 cases.

The v2 and v3 `legacy-dispatch-v1` successors link their unchanged
`descriptor-binding-v1` predecessors. Fresh wrapper 8.0 and holdout wrapper 5.0
write new report filenames. All historical inputs, API/export schema 2.0, and
the original v3 outside-discovery inventory retain their prior records.
[Verification and preservation results](VALIDATION.md#milestone-9b--bounded-slugify-dispatch)
