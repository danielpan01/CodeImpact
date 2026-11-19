# Inflection set mutation and cleanup

## Source audit before the change

The pinned `inflection_title` case matches the `parameter-tables-v1` analysis
hash `eaadfb0bcc1a4c83db4b738f639fd4bfa041dba2a8e6330b6990ff715a2386fc`.
It selects 2/22 definitions, with 1 draft true positive, 1 draft false
positive, 0 false negatives and 20 true negatives. Both paths passed typed
evidence validation. The conservative `test_uncountable_word_is_not_greedy`
path ends at its own test module in both revisions, at distance 1 and score 50.
The resolved `test_titleize → inflection.py::titleize` path has distance 1,
score 81 and evidence in both revisions.

The [pinned Python snapshots](../corpus/real-v3/cases/inflection_title.json)
compare `1969b3a06a9ff06d023863e388cf8af01978d297` and
`e32443bb7dc1ba91a15336b5baab908d25f4b93a`. Both contain a direct
`import inflection` in the test module. In both revisions
`inflection.py:79–88` assigns `UNCOUNTABLES` once to a literal string set that
lacks `"ors"`. The existing initialization audit follows the captured imports
and eager calls, including the rule-list population. The separate
`test_uncountability` decorator enumerates the set into one-element tuples.
[Capture provenance](../corpus/real-v3/provenance/inflection_title.json)

The before test spans lines 294–314, and the after test spans 296–316. It binds
`"ors"` and `"sponsor"` to locals, adds `"ors"` through the source module, then
checks the unchanged `pluralize` and `singularize` functions. The former reads
the set through membership, and the latter iterates it. Both also read
unchanged rule lists. The `finally` suite contains one `remove` with the same
receiver and key, so it runs even when an assertion or supported call raises.

The independent edits are two literal rows in `MIXTURE_TO_TITLEIZED` and the
body of `titleize`. The set-mutation test neither consumes that parameter table
nor reaches the changed function. `test_titleize` uses both. The source facts
above describe captured definitions and their dependencies. Independent review
of the labels is pending.

## Supported proof

The proof runs within the existing mixed parameter-table analysis. It accepts
an undecorated, argument-free test with optional distinct local string assignments,
then one qualified `add` immediately before `try/finally`. The `try` body can
contain assertions and audited calls. The `finally` body must be a single
`remove` with the identical receiver and key. The receiver must belong to the
source module with the deferred function edit. Its binding must come from a
literal string set that lacks the candidate key and has no audited eager writes.

Both revisions must establish the binding, setup, cleanup and assertion
dependencies. A changed table read, a call to the edited body, an unsupported
helper, an opaque escape, a rebound or aliased receiver, or an exhausted query
budget keeps fallback. The proof uses the initialized source state and the
calls of the one test. Inter-test ordering, concurrent writers, external plugins
and arbitrary runtime state remain outside its scope.

The existing mixed-edit checks still verify direct collection references to
the changed parameter table. Only the test-module seed's contribution can be
dropped. Other seeds and paths keep their own evidence. The Inflection rule-table
case still recommends the set-mutation test because the production rules it
reads changed in that case.

## Measured result

`test_inflection.py::test_uncountable_word_is_not_greedy` is the only removed
recommendation and impacted ID. No recommendations were added. The retained
`test_inflection.py::test_titleize` recommendation and its full typed evidence
match the predecessor, including revision `both`, distance 1 and score 81.
The titleize case still has 40 nodes, 70 edges and three changed symbols. Its
impacted count falls from four to three. Its one conservative explanation is
removed and its one resolved explanation is retained.

| Scope | Selected before → after | TP / FP / FN / TN before → after |
| --- | --- | --- |
| Titleize | 2/22 → 1/22 | 1 / 1 / 0 / 20 → 1 / 0 / 0 / 21 |
| Inflection overall | 10/44 → 9/44 | 7 / 3 / 0 / 34 → 7 / 2 / 0 / 35 |
| Expanded v3 | 47/120 → 46/120 | 42 / 5 / 0 / 61 → 42 / 4 / 0 / 62 |

All 12 uncertain definitions stay unselected. The other five v3 analysis hashes
match their predecessor. The new analysis hash for titleize is
`58a8cbd365ed42ed18a28b0b91cce6acbe8e877b531cdf553ad4474efe78ccb2`.
The separate [set-cleanup-v1 receipt](../corpus/real-v3/baselines/set-cleanup-v1.json)
links the preserved `parameter-tables-v1` baseline. Independent review remains
pending. [Verification record](VALIDATION.md#inflection-set-mutation-and-finally-cleanup)
