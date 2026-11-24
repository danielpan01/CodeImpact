# Bounded test discovery

The filename expansion below records Milestone 7. The active policy adds
[mixed-case unittest methods](#mixed-case-unittest-methods) under the same
supported filenames.

## Milestone 7 — literal `test.py`

Implemented November 16, 2026, from clean `7084ab04dd60881a6dde6e91986911f1d9f6ece2`,
after the authorized merge of [milestone 8C / PR #15](https://github.com/danielpan01/CodeImpact/pull/15).
Its [post-merge checks passed](https://github.com/danielpan01/CodeImpact/actions/runs/43808633061).
There were no pre-existing uncommitted changes. The owner subsequently requested
publication of milestone 7. Hosting and the human pilot
remain deferred. Independent source-label review remains pending.

## Supported policy

`test-files-v2` adds **literal, case-sensitive `test.py`** at any directory depth
to the existing `test_*.py` and `*_test.py` filename rules. One shared filename
predicate is used by the analyzer, corpus label validation and discovery audit.
The corpus walker remains independent of recommendation generation.

Within those files, direct `def` and `async def` definitions named `test_*` are
indexed, recursively through direct class/function bodies. Class names need not
start with `Test`; direct nested functions remain supported as before. This is
static source discovery, **not pytest collection or a count of test executions**.

- `tests.py`, `testing.py`, `Test.py`, utility/production filenames and merely being
  inside a `tests/` directory do not qualify. Test-shaped production functions
  remain ordinary functions, not recommended test nodes.
- Definitions inside conditionals, loops, `try`, `with` or `match` bodies are not
  indexed. The source-only evaluation audit identifies such test-shaped definitions
  where parsing permits; an unparseable file is reported separately.
- Parametrization, inherited test executions and plugin/configuration-driven
  collection remain outside discovery. Dependency analysis infers limited
  [same-directory fixture evidence](ARCHITECTURE.md#bounded-pytest-fixture-injection).
  [Literal runtime import resolution](ARCHITECTURE.md#literal-runtime-import-calls)
  also runs independently of discovery.
- Duplicate qualified names retain the analyzer's existing final-definition/one-ID
  behavior. The corpus validator rejects ambiguous duplicate test labels; this
  milestone does not claim complete duplicate-definition semantics.
- Each revision is indexed independently. Removed tests remain visible as removed
  symbols, but only current head tests can be recommended. Deleted dependencies,
  before-only and mixed evidence keep the existing graph behavior.

Only the analyzer's filename predicate changes. IDs, caller-to-dependency edges,
ranking, selection filters, source limits and exact typed evidence paths are
unchanged. No milestone 9 fallback tuning is included. Upstream source was read
and parsed as data; it was never executed, imported, installed or collected by pytest.

## Source-only labels established first

The unchanged Ordered Set pop snapshot and its edited `pop` method were inspected
before implementing or running expanded discovery. The separate
[30-definition draft](../corpus/real-v3/baselines/test-discovery-v1-labels.json)
records exact IDs, source ranges, rationales, source/inventory hashes and review
status. Its pre-analysis SHA-256 remains:

`bb40f5912e4cc8e535c8aa908db2c44871a355336ca9f4457df862356653b879`

The draft has **1 affected, 17 unaffected and 12 uncertain** definitions.
`test_pop` directly invokes the edited method; this establishes a dependency, not
an observed failure. The 17 controls use local unchanged operations without a pop
route. The 12 uncertain labels involve external pickle behavior or inherited
operators/methods whose implementation is absent from the pinned snapshot.
They were not converted to negatives after observing nonselection.

The [original review pack](../corpus/real-v3/REVIEW.md), 90 frozen labels, original
30-entry outside-discovery inventory, snapshots, licenses and provenance are all
unchanged. The new draft is an additional review pack, not independent approval.
Its hash records integrity, not independent proof of labeling order or correctness.

Eight discovery regressions failed before implementation (seven existing-scope
controls passed). Regressions cover supported/excluded names, classes/nesting,
duplicates, revisions, removed tests/dependencies, parse failures, deterministic
results, source safety and exact evidence. Evaluation guards additionally reject
missing/altered new labels, wrong source ranges, historical edits, omitted or extra
inventory and unauthorized annotation fields before recommendations are measured.

## Original and expanded measurements

Counts are case/definition pairs, not unique runtime test executions. TP/FP/FN/TN
measure agreement with draft dependency labels. Uncertain definitions are excluded
from those four counts and reported separately.

| Measurement | Discovered | Selected | TP | FP | FN | TN | Uncertain total / selected | Outside discovery |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Original v3, frozen | 90 | 84 | 41 | 43 | 0 | 6 | 0 / 0 | 30 |
| Expanded v3, `test-discovery-v1` | 120 | 85 | 42 | 43 | 0 | 23 | 12 / 0 | 0 in these six heads |
| Newly covered Ordered Set pop case | 30 | 1 | 1 | 0 | 0 | 17 | 12 / 0 | 0 |

Current v3 draft-label precision is **42/85 (49.41%)**, recall **42/42 (100%)**
within classified discovered definitions. These are not production accuracy or
permission to omit tests. The 12 unselected uncertain definitions remain unknown.
The original 90-definition denominator and 30 exclusions remain explicit fields
in the current report; the original result is not silently reinterpreted.

Only `test.py::test_pop` is newly recommended. Its exact path is
`test.py::test_pop → test.py::<module> → ordered_set.py::<module>`.
This is **conservative module/import evidence**, not a newly resolved instance call.
The full typed edge IDs, revision evidence and exported sources are validated by
the existing evaluator for every recommendation. The other five v3 analyses are
byte-identical after the existing removal of elapsed timing.

Authored results remain **23 TP / 0 FP / 2 FN / 32 TN**, with two uncertain selections.
V1 remains **45 TP / 0 FP / 0 FN / 123 TN**, 56/201 selected, including 11 uncertain.
V2 remains **109 TP / 273 FP / 0 FN / 177 TN**, 395/581 selected, including 13 uncertain;
its complete stable measurement is identical to `mapping-fallback-v1`.

## Preservation and versioned contracts

The starting receipt captured all 306 tracked file hashes and 176 protected
historical files/artifacts in `reports/milestone7-before/`. Historical corpus,
benchmark receipts, original screenshots and stable evaluation outputs are never
rewritten. New receipts are:

- [V2 current replay](../corpus/real-v2/baselines/test-discovery-v1.json): ten engine
  hashes, the unchanged mapping measurement, and the mapping → argument → partial
  historical receipt chain.
- [V3 current measurement](../corpus/real-v3/baselines/test-discovery-v1.json): ten
  engine hashes, original freeze/baseline hashes, new label hash, current audit,
  explicit discrepancy annotations and expanded measurement.
- [Preservation extension](../benchmarks/test-discovery-v1-preservation.json): pins
  the original milestone 6 receipt, the exact three new corpus files and current
  engine/evaluator files. Historical checks still verify every original corpus
  byte; only the five explicitly changed implementation files use current hashes.
  This is not a replacement performance benchmark.

`make evaluate-real-v2` writes **`reports/real-v2-discovery-v1-evaluation.json`**,
with fresh wrapper **5.0**. `previous_summary` now refers to mapping; argument,
partial and original summaries remain separately named. `make evaluate-real-v3`
writes **`reports/real-v3-discovery-v1-evaluation.json`**, with holdout wrapper
**2.0**, `original_summary`, `original_discovery`, the full new label receipt,
current discovery policy and current-baseline match status. The original stable
report filenames are preserved. Normal evaluation rejects drift; it never creates
or accepts a baseline automatically.

**Application/export report 2.0, snapshot input, dataset 1.0 and evaluation 1.0
are unchanged.** No discovery metadata was added to the public API contract. The
UI derives current counts from nonremoved test nodes and explains the supported
policy. Its optional outside-scope count concerns only already indexed test-shaped
functions; it explicitly excludes definitions the index cannot see.

## Frontend and visual review

Tests now offers an expandable **Test discovery scope** explanation below the
results, preserving the first complete phone recommendation. Empty states still
distinguish zero discovery, discovered-but-unselected tests, and filtered-out
recommendations. The explanation is keyboard reachable and uses the existing
44 px controls, focus styling, typography and theme surfaces. The empty-results
panel scrolls when expanded content exceeds desktop height; browser checks verify
that its final paragraph is reachable. Filters, evidence, changed-code navigation,
full export and lossless diagnostics are retained.

Ordered Set is now a positive discovery/evidence/export browser case. A separate
[authored unsupported-scope input](../tests/fixtures/unsupported-discovery.json)
keeps meaningful zero-discovery coverage: one test-shaped function in `checks.py`
and another under a conditional in a supported file. Its source audit reports
both exclusions; the UI correctly counts only the one indexed ordinary function.
The original Ordered Set zero-discovery UI fixture and manifest entry are retained
as archived 8C evidence; the active matrix uses the new fixture.

The first canonical comparison passed 14 images and identified two intentional
changes. Expected/actual/diff images were inspected. Review also caught and fixed
clipped expanded desktop text. The phone capture now includes the full app shell,
using the existing mixed-state capture pattern, after a component-only capture
clipped the control despite correct live layout bounds. Only these two new expected
images were recorded under new names; all 16 original 8C images remain unchanged:

| State | Before (8C) | After (7) | Reviewed difference |
| --- | --- | --- | --- |
| Filtered empty result, phone light | [Before](../web/tests/quality/baselines/empty-phone-light.png) | [After](../web/tests/quality/baselines/milestone7-empty-phone-light.png) | Scope disclosure added after the existing complete export note; retained selection/reset; full-page capture protects the entire control |
| Zero discovery, desktop dark | [Before](../web/tests/quality/baselines/zero-discovery-desktop-dark.png) | [After](../web/tests/quality/baselines/milestone7-zero-discovery-desktop-dark.png) | Actual authored fixture counts, literal `test.py` guidance and scope disclosure; unchanged evidence-empty action |

There are still 16 active comparisons (18 retained PNGs), with the same exact
pixel tolerance, browser/font pins and zero retries. The 48-scan accessibility
matrix opens the scope explanation; the visual zero-discovery image keeps it
collapsed to protect the heading/action. No rule or region is excluded. This is
partial automated and agent review, not accessibility certification or independent
usability testing. Final verification and remaining findings are in
[VALIDATION.md](VALIDATION.md#milestone-7--bounded-test-discovery-november-16-2026).

## Next step

Milestone **9A**, one bounded Cachetools LFU fallback pattern, is next. Its 125
false positives remain; descriptor, Slugify and module-data refinements belong to
separate 9B/9C tasks. Preserve affected/uncertain paths, draft source controls before
tuning, and add another versioned measurement. Live hosting and a human pilot stay
deferred unless the owner resumes them.

## Subsequent milestone 9A

Milestone 7 merged as PR #16 at `a4d29a7c7c462c32f0bb7978e45708166b0106b0`.
The subsequent [9A refinement](LFU_CALLBACK_REVIEW.md) leaves discovery policy,
labels, denominators and this milestone's receipts unchanged. New current output
names use `lfu-callback-v1`; all expanded v3 measurements stay identical. The active
roadmap now proceeds to one bounded 9B mechanism, while hosting and the human pilot
remain deferred.

## Mixed-case unittest methods

`test-files-v3` adds synchronous, undecorated methods whose names begin with
`test` followed by an uppercase ASCII letter. The method must be directly
defined on an undecorated, top-level class whose sole base is
`unittest.TestCase`. The supported binding is a unique, unconditional,
unaliased `import unittest` before the class definition. The class and method
bindings must also be unique in their respective scopes.

The proof declines when a captured Python module or package could shadow
`unittest`, visible rebinding or object escape makes the import ambiguous, or
the module directly accesses the `sys` import cache or search path hooks.
Wildcard imports, alias imports, unqualified bases, dynamic/multiple bases,
custom metaclasses, decorated or asynchronous methods, module-level mixed-case
functions, nested classes and nested helpers do not qualify for this extension.
Definitions under compound statements and unsupported filenames stay outside
the rule. Ordinary `test_` definitions retain their prior behavior.

This source rule classifies definitions independently in base and head.
A method removed or no longer eligible in head cannot be recommended as a
current test. A surviving method may have before-only evidence for a deleted
dependency. Stable IDs, exact evidence paths, ranking and the application
report contract follow the existing rules. The proof covers lexical source
and captured paths. Runtime imports, setup behavior, custom loaders,
monkey-patching hidden behind other modules and inherited test executions
remain outside the discovery claim.

The two frozen IceCream cases each contain 30 excluded `TestIceCream` methods
and two excluded `TestIceCreamInstall` methods. Separate labels for all 64
case/definition pairs were drafted and frozen before expanded analysis.
The original inventory and source-only review pack remain under v2.
[Exact draft IDs, source ranges and rationales](../corpus/real-v4-successors/unittest-discovery-v1/labels.json)
· [Both replay targets and results](REAL_EVALUATION_V4.md#mixed-case-unittest-successor)
