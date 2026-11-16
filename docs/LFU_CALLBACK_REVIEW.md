# Milestone 9A — literal-raising callbacks

## Source decision, recorded before implementation

Starting point: merged milestone 7, `a4d29a7c7c462c32f0bb7978e45708166b0106b0`,
clean working tree. PR #16 and post-merge run 43930425754 passed. Starting source,
corpus, baseline, UI artifact and stable-report hashes are recorded locally in
`reports/milestone9a-before/`. Historical labels remain agent drafts.

The pinned Cachetools LFU change edits existing LFU mapping bodies. The current
query rejects every enclosing function with a nested definition, before examining
its behavior. In `tests/test_rr.py::RRCacheTest.test_rr_bad_choice`, the local
`bad_choice(seq)` contains only `raise ValueError("test error")`. It is passed
directly to the source-known, unrelated `RRCache` constructor. Its argument is
never inspected. RR's choice hook raises; it does not call LFU. The retained
recommendation instead follows test → test module → cachetools module.

The other surviving RR test uses a loop and an iterator callback. Cached-wrapper
tests include nested decorators, stored callables and shared mixins; TTL/TLRU
tests include custom timer/context behavior. Those mechanisms are excluded here.

### Proposed bounded proof

Permit the existing mapping query to continue past direct local synchronous
functions whose sole statement raises an unshadowed builtin `ValueError`,
`TypeError`, `RuntimeError` or `KeyError`, with zero or one literal argument.
These ordinary exception constructors have no source callback in this form.
No annotations, defaults, decorators, type parameters, cause, closure reads,
return values or other statements qualify. The callback name must be unique and
unrebound, and every use must pass it directly to a source-known plain constructor
with only literal arguments and qualifying callback arguments. Constructor aliases
may use existing resolution; callback aliases/escaping/mutation remain unsupported.
The existing receiver, initialization, inheritance, revision and budget checks
must still prove no reference to the edited mapping root. This creates no edges.

Unknown receivers/arguments, shared test definitions, effectful/custom hooks,
shadowed exceptions, async/conditional/nested classes, callback rebinding and
budget exhaustion must retain fallback. Before and head are checked separately;
deletions and broader edits retain existing behavior. Discovery, ranking, report
2.0, source limits, labels and all old receipts are outside the change.

Synthetic source regressions will establish this boundary before behavior changes.
The expected improvement is deliberately small; this does not address all 125 LFU
false positives or establish that any test can safely be skipped.

## Implemented boundary and regression evidence

The implementation follows that decision. Builtin identity scans are bounded by
the existing 2,000-visit limit and cached per file/name. Recognizable reflective
namespace access/rebinding also declines, including `globals`, `__builtins__`,
`__dict__`, `getattr` and `setattr`. This is not a general dynamic-dispatch model.
The callback body is read as AST only, never called or imported.

Before implementation, five intended exclusion regressions failed and 28 controls
passed. A subsequent adversarial check exposed three reflective-binding holes;
those regressions failed before the guard was tightened. The final mapping suite
passes **114 tests**, including 47 callback-boundary tests. Constructor aliases
are supported; callback aliases, rebinding and escapes deliberately keep fallback.
Effectful hooks, inherited overrides, shared definitions, required test arguments,
unknown receivers, source revision differences, deleted methods and both traversal
and builtin-identity budgets retain conservative behavior.

A test-scoped replay restores only the old nested-definition veto and reproduces
the exact preserved milestone 7 LFU analysis hash. It compares every retained
recommendation object, validates both reports, and checks the complete graph,
changed/removed IDs, source files and warnings. This does not execute an upstream
repository or add a production historical-analyzer mode.

## Measured change

Counts are draft-label case/definition pairs. There was no relabeling or independent
review. Only this ID is removed:

`tests/test_rr.py::RRCacheTest.test_rr_bad_choice`

**Added IDs: none.** All 138 retained LFU recommendations have identical scores,
distances, reasons, evidence paths, edge IDs and revision evidence. The six affected
and eight uncertain IDs all remain selected. The 606 nodes, 886 edges, 12 changed
IDs, full source/diagnostics and removed-symbol inventory are unchanged. The impact
list loses only the same test ID (394 → 393); selected count is 139 → 138.

| Measurement | Selected / discovered | TP | FP | FN | TN | Uncertain selected / total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LFU, preserved discovery baseline | 139 / 156 | 6 | 125 | 0 | 17 | 8 / 8 |
| LFU, current 9A | 138 / 156 | 6 | 124 | 0 | 18 | 8 / 8 |
| V2, preserved discovery baseline | 395 / 581 | 109 | 273 | 0 | 177 | 13 / 22 |
| V2, current 9A | 394 / 581 | 109 | 272 | 0 | 178 | 13 / 22 |

Current per-case v2 measurements:

| Case | Selected / discovered | TP | FP | FN | TN | Uncertain selected / total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| atomicwrites_path | 6 / 6 | 6 | 0 | 0 | 0 | 0 / 0 |
| atomicwrites_prefix | 6 / 6 | 6 | 0 | 0 | 0 | 0 / 0 |
| cachetools_descriptor | 36 / 154 | 0 | 31 | 0 | 115 | 5 / 8 |
| cachetools_lfu | 138 / 156 | 6 | 124 | 0 | 18 | 8 / 8 |
| slugify_ascii | 100 / 126 | 63 | 37 | 0 | 23 | 0 / 3 |
| slugify_boundary | 108 / 133 | 28 | 80 | 0 | 22 | 0 / 3 |

V2 retains nine unselected uncertain definitions. Explanation totals are 51 resolved,
336 conservative and seven changed-test recommendations. All five nontarget case
analyses are byte-identical after stable serialization. The authored and v1 reports
are byte-identical; v3's entire expanded measurement remains 85/120 selected,
42 TP / 43 FP / 0 FN / 23 TN, with all 12 uncertain definitions unselected.
The original v3 denominator of 90 plus 30 exclusions remains separately frozen.

## Versioned history and frontend preservation

All **109 historical corpus files** and **186 protected files/artifacts** keep their
starting hashes, including milestone 7 receipts, old reports, UI fixture manifests
and screenshot baselines. New files are:

- [V2 current baseline](../corpus/real-v2/baselines/lfu-callback-v1.json), linked to
  `test-discovery-v1` → mapping → argument → partial; only the reviewed false-positive
  annotation is removed and the current limitation wording is updated.
- [V3 engine replay](../corpus/real-v3/baselines/lfu-callback-v1.json), linked to its
  preserved discovery receipt and new v2 receipt; measurements/labels are identical.
- [Preservation extension](../benchmarks/lfu-callback-v1-preservation.json), linked
  to the unchanged milestone 7 preservation receipt. Only the mapping module and
  two evaluator modules have new implementation hashes. This is not a new performance
  benchmark or a new dataset capture.

Current output names are `reports/real-v2-lfu-callback-v1-evaluation.json` (wrapper
6.0) and `reports/real-v3-lfu-callback-v1-evaluation.json` (wrapper 3.0). Application,
API/export, snapshot and evaluation contracts remain unchanged. Normal commands
remain strict; corruption of the discovery predecessors fails before analysis.

The dashboard is unchanged. Its real-analysis diagnostics browser test now requires
138 recommendations and absence of the exact reviewed ID while still requiring all
3,128 raw notes and complete exported data. Historical UI fixtures retain their
original results. No expected screenshot, mask, rule, tolerance or interaction
assertion was weakened or regenerated.

## Remaining work

The 124 remaining LFU false positives include nested cache wrappers/decorators,
shared helpers and timer/iterator behavior beyond this proof. The second surviving
RR test's iterator callback is still unsupported. Descriptor's 31 and Slugify's 117
false positives are unchanged. The next roadmap step is **one 9B mechanism**:
inspect the descriptor instance/classmethod distinction with its eight uncertain
labels (five currently selected) preserved. Do not combine it with Slugify or 9C
module-data work. Fixture injection, runtime imports and general dynamic dispatch
remain outside scope. Unselected tests are not established safe to skip.

Live hosting, the human pilot and independent source-label review remain deferred
or pending as before. No runtime test failure, production accuracy, accessibility
certification or independent usability finding is claimed. Exact commands, results
and remaining automated-review findings are in [VALIDATION.md](VALIDATION.md).
