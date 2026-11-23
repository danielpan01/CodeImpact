# Inflection finite uncountability guard

## Source audit

Clean main at PR #30 reproduced `empty-string-guard-v1`. The rule case
selected 7/22 definitions with 6 draft true positives, 1 false positive,
0 false negatives, and 15 true negatives. `test_uncountability` had the
conservative path `test_uncountability → inflection.py::pluralize →
inflection.py::<module>` in both revisions, at distance 2 and score 40.
The independent test-module edit is to `SINGULAR_TO_PLURAL`. The existing
proof already excludes that contribution.

The decorator at lines 283–286 before and 284–287 after constructs one
single-value tuple for each member of `inflection.UNCOUNTABLES`. Both
literal sets contain `equipment`, `fish`, `information`, `jeans`, `money`,
`rice`, `series`, `sheep`, and `species`. Each is a nonempty lowercase ASCII
word. The ordinary pytest parameter decorator materializes those rows before
the test bodies run. The captured sibling test temporarily adds the absent
ASCII word `ors` and removes it in `finally`.

For each of the nine values in both revisions, `word.lower()` is identical
to `word` and is in the set. `pluralize` returns the original string before
its `PLURALS` loop. The `singularize` prefix tries the fixed template
`(?i)\b(%s)\Z` against the same set. Each interpolated string consists solely
of ASCII letters. The pattern containing the input itself matches at the
start word boundary and end of string. Any earlier match also returns the
original input, so iteration order cannot affect that result. The
`SINGULARS` loop is unreachable for each input.

The third assertion compares `pluralize(word)` and `singularize(word)` as
separate calls. Both produce the same original value. In a nested call,
the proven identity result from `pluralize` would supply that same input to
`singularize`. A synthetic regression covers that composition.
[Pinned snapshots](../corpus/real-v3/cases/inflection_rules.json) ·
[Capture provenance](../corpus/real-v3/provenance/inflection_rules.json)

## Supported proof

The module-data query recognizes one directly bound `pytest.mark.parametrize`
comprehension with a single tuple column and a direct reference to an unchanged,
source-owned literal set. All members must be lowercase ASCII words. The
test's equality assertions can compare the parameter and audited single-argument
qualified calls. Each supported callee returns its parameter from its first
guard, so that same value can feed the next call in a nested expression.

The membership guard supports the pinned `not word or word.lower() in SET`
shape. The loop guard supports the exact `re.search` template above through
a verified standard-library binding. The proof uses the self-match property of
the fixed template over literal ASCII words. It does not run the regex or
interpret other regular-expression syntax. Shadowed bindings, alternate flags,
unproved return values, generator functions and extra guard effects keep
fallback.

Initialization, decorator binding and collection use the existing audit.
The production exclusion also checks reachable peer tests in the single
captured test module for effects. Peer rule-table reads are allowed in that
effects check. Other mutations and escapes are rejected, except for the
existing matched `add` and `finally: remove` shape with an ASCII key absent
from the original set. That insertion leaves every collected member in the
set, contributes a safe literal to the fixed regex template, and removes only
the added value. This supports the pinned sibling even when a guard assertion
fails. Eager mutation, other test modules, unproved setup, opaque calls and
budget exhaustion retain fallback. The proof runs against both revisions.

## Measurement

The only removed recommendation and impacted ID is
`test_inflection.py::test_uncountability`. All six draft-affected tests keep
their complete recommendation objects and typed evidence. The earlier
empty-string exclusion remains. The graph retains 40 nodes, 70 edges and two
changed module IDs. No paths are replaced or added. The impacted count falls
from 23 to 22, and the conservative recommendation count falls from seven
to six.

| Scope | Selected before → after | TP / FP / FN / TN before → after |
| --- | --- | --- |
| Inflection rules | 7/22 → 6/22 | 6 / 1 / 0 / 15 → 6 / 0 / 0 / 16 |
| Inflection overall | 8/44 → 7/44 | 7 / 1 / 0 / 36 → 7 / 0 / 0 / 37 |
| Expanded v3 | 45/120 → 44/120 | 42 / 3 / 0 / 63 → 42 / 2 / 0 / 64 |

All twelve uncertain definitions stay unselected, and the other five v3
analysis hashes match. The new `inflection_rules` analysis hash is
`8c970621061fc8a21dc9ab5e879c1f2e36989bdd300921aa1a9228382031b7b7`.
Independent label review remains pending.
[Successor receipt](../corpus/real-v3/baselines/finite-string-guards-v1.json) ·
[Verification](VALIDATION.md#inflection-finite-uncountability-guard)
