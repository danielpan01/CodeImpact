# Inflection empty-string guard

## Source audit

On clean main at PR #29, the `set-cleanup-v1` replay selected 8 of 22
definitions in `inflection_rules`, with 6 draft true positives, 2 false
positives, 0 false negatives, and 14 true negatives. The pinned analysis
hash was `e74670bc394ac30f73dd0657aa9824990c6e62e73343960abe50bd894fc3e126`.

Both revisions import `inflection` directly at test-module scope.
`test_pluralize_empty_string` calls `inflection.pluralize("")` at line 280
before and line 281 after. The source function starts at lines 282 and 284,
respectively. After the docstring, its first statement is
`if not word or word.lower() in UNCOUNTABLES: return word`. For the literal
empty string, `not word` is true. The return precedes the second operand,
the `PLURALS` loop in the `else` suite, and any read of `SINGULARS`.
[Pinned snapshots](../corpus/real-v3/cases/inflection_rules.json) ·
[Capture provenance](../corpus/real-v3/provenance/inflection_rules.json)

The production module changes its `PLURALS` and `SINGULARS` assignments.
The existing initialization audit still checks imports and eager rule-list
population. The independent test-module edit changes `SINGULAR_TO_PLURAL`.
The empty-string test has no parameter decorator or table reference. The
existing query already excludes the test-module contribution. The only
retained route is `test_pluralize_empty_string → inflection.py::pluralize →
inflection.py::<module>`, conservative in both revisions at score 40 and
distance 2. The replay yielded no other supporting path for this test.

`test_uncountability` gets a parameter from its decorator, calls both
singular and plural helpers, and also calls `singularize` on the result of
`pluralize`. The literal-empty proof cannot establish a bypass for those
calls. The six draft-affected tests have separate rule or parameter-table
dependencies. [Prior rule-table measurement](MODULE_DATA_REVIEW.md#exact-measurement-and-evidence)

## Proof boundary

The existing module-data query recognizes a direct qualified call with one
literal empty positional string inside a plain module-level test. It must
resolve to a source-owned function in the production module whose literal
table edit is being audited. The function must have one ordinary required
parameter. After an optional docstring, its first statement must return that
parameter under `not parameter`. The supported two-operand `or` form has that
same first operand and `parameter.lower() in NAME` second, with `NAME` bound
to unchanged, audited data in the same module. The empty argument satisfies
the first operand and skips the second.

Initialization and collection checks still run. Argument expansion, keywords,
named or rebound argument values, generator bodies, other guard shapes and
statements preceding the guard keep the ordinary conservative audit. Other
calls and reads in the test still run through that audit. Both revisions must
prove exclusion for a contribution to drop. Independent seeds retain their
original typed paths. No source from the captured repository was executed.

## Measurement

The only removed recommendation and impacted ID is
`test_inflection.py::test_pluralize_empty_string`. The six affected
recommendations and `test_inflection.py::test_uncountability` keep their
complete predecessor objects. The remaining seven explanations are
conservative. Added recommendations and replacement evidence both count zero.
The report retains the same 40 nodes, 70 edges, two changed symbols, diagnostics,
and source. The impact count falls from 24 to 23.

| Scope | Selected before → after | TP / FP / FN / TN before → after |
| --- | --- | --- |
| Inflection rules | 8/22 → 7/22 | 6 / 2 / 0 / 14 → 6 / 1 / 0 / 15 |
| Inflection overall | 9/44 → 8/44 | 7 / 2 / 0 / 35 → 7 / 1 / 0 / 36 |
| Expanded v3 | 46/120 → 45/120 | 42 / 4 / 0 / 62 → 42 / 3 / 0 / 63 |

All 12 uncertain definitions stay unselected. The other five v3 analyses
match their `set-cleanup-v1` hashes. The new `inflection_rules` analysis
hash is `f8b13e407ebc33ce9d14b5bc55b689b225ab9d57a424ecbef25501171ba2332e`.
Independent source-label review remains pending.
[Successor receipt](../corpus/real-v3/baselines/empty-string-guard-v1.json) ·
[Verification](VALIDATION.md#inflection-literal-empty-string-guard)
