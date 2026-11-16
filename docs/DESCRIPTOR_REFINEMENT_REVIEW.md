# Milestone 9B descriptor binding

## Source decision before implementation

The starting tree is merged 9A at `41753b3522246fe8c947a27326ada95b1c285dce`.
The pinned before/head AST difference moves the receiver of
`_ClassMethodDescriptor.__call__` into the positional-only list. All 36 current
recommendations use aggregate module/import evidence.

One bounded route is ordinary class lookup followed by a call without a receiver.
`UnboundMethodTest.test_class_call_without_instance` reads `Cached.get` through
the descriptor's class-access branch. That branch returns a separate unbound
wrapper. Its empty-argument path has no receiver to forward. The deprecated
outer `@classmethod` route can instead invoke the edited raw descriptor and
remains conservative in both revisions, regardless of the analysis host's version.

The proposed proof resolves source constructors, decorator factories and binding
from captured ASTs, checks their eager effects, and inspects the resulting direct
call. It declines on possible raw calls, ambiguous dispatch, unknown arguments,
escaping values, unsupported decorators and reflective mutation. Only the
aggregate fallback contribution of the proved test may be omitted. Direct
resolved evidence, edits outside the receiver signature change, and unsupported
binding paths keep their existing propagation.

## Supported proof

`descriptor_binding.py` applies when the entire module AST edit moves only the
first parameter of one source descriptor's `__call__` into the positional-only
list. The query covers one direct zero-argument descriptor invocation, optionally
preceded by a simple constructor, factory, or receiver alias. It also recognizes
the standard `unittest.TestCase.assertRaises(TypeError)` context used by the
pinned example. The source model traces eager imports, class/decorator creation,
literal defaults and owned receiver fields before resolving ordinary `__get__`.
The final invocation must end in an inert value or a verified terminal
`TypeError`. Both revisions must pass, and the proof excludes only this test's
contribution from the edited module's aggregate traversal.

For the removed test, the relevant source is lines 1013–1015 of
`tests/test_cachedmethod.py`, including `Cached.get()`. The decorator factories
construct a raw descriptor during class creation. The ordinary class lookup
passes `None` as the instance and returns a distinct `_Unbound` wrapper.
With no arguments, that wrapper looks up a receiver in an empty keyword map.
The wrapper's signature read uses the original plain method's metadata.
The empty map forces `TypeError` before forwarding can occur. The source proof
also follows the surrounding eager factory and registration effects.

The query allows selected standard-library binding and metadata operations in
specific data shapes. It keeps raw callable dispatch, both `@classmethod`
decorator orders, shadowing, ambiguous or inherited receiver binding, unknown
callbacks, escaping values, dynamic introspection, custom access hooks,
unsupported initialization, cycles and exhausted budgets conservative. It uses
the existing 12,000-step and 24-level proof limits and builds no graph edges.
The analyzer reads AST and source data throughout. A possible classmethod
dependency stays conservative across analyzed Python versions.

## Regression evidence

Before implementation, two expected exclusions failed and 25 controls passed.
The final focused suite includes class and instance binding, raw invocation,
constructor and factory aliases, decorators and rebinding, shared mixins,
custom hooks and metaclasses, eager effects, reflection, revisions, deleted
methods, cycles and budget exhaustion. An additional negative control found
that `except Exception` could catch a modeled `TypeError` and reach the raw
descriptor. The proof now checks the supported builtin exception ancestry.

The publication review found three more ways to reach the raw descriptor.
Reading a property can invoke its getter, repeated `next()` calls advance the
iterator, and a non-`None` initializer result can raise `TypeError` and enter an
exception handler. Three regressions reproduced these wrong exclusions before
the correction. The proof now declines on property reads and non-`None`
initializer results, and tracks position for supported concrete iterators.

A test-scoped replay disables only the new descriptor exclusion and reproduces
the precise `lfu-callback-v1` analysis hash. Evidence validation runs for both
reports. All 35 retained recommendation objects match exactly, including scores,
distances, explanation categories, paths, edge IDs, and revision evidence.
The 603 nodes, 879 edges, three changed IDs, removed-symbol inventory, source
files and 3,076 diagnostics match. The impact list falls from 143 to 142.

## Measured result

The only removed ID is
`tests/test_cachedmethod.py::UnboundMethodTest.test_class_call_without_instance`.
There are zero added IDs. The existing source label is unaffected.

| Measurement | Before | After |
| --- | ---: | ---: |
| Descriptor selected | 36 / 154 | 35 / 154 |
| Descriptor TP / FP / FN / TN | 0 / 31 / 0 / 115 | 0 / 30 / 0 / 116 |
| V2 selected | 394 / 581 | 393 / 581 |
| V2 TP / FP / FN / TN | 109 / 272 / 0 / 178 | 109 / 271 / 0 / 179 |

All eight uncertain descriptor labels remain explicit. Within
`tests/test_classmethod.py::CachedClassMethodTest`, the five selected methods are
`test_condition`, `test_info`, `test_locked`, `test_shared_cache` and
`test_typed`. `test_clear`, `test_clear_condition` and `test_clear_locked`
remain unselected. These counts are separate from the true negatives. This
descriptor case has zero affected labels, so the synthetic positive controls
supply the direct and classmethod reachability evidence.

| Case or repository | Selected / discovered | TP / FP / FN / TN | Uncertain selected / unselected | Resolved / conservative / changed |
| --- | ---: | ---: | ---: | ---: |
| atomicwrites_path | 6 / 6 | 6 / 0 / 0 / 0 | 0 / 0 | 0 / 6 / 0 |
| atomicwrites_prefix | 6 / 6 | 6 / 0 / 0 / 0 | 0 / 0 | 0 / 6 / 0 |
| cachetools_descriptor | 35 / 154 | 0 / 30 / 0 / 116 | 5 / 3 | 0 / 35 / 0 |
| cachetools_lfu | 138 / 156 | 6 / 124 / 0 / 18 | 8 / 0 | 0 / 135 / 3 |
| slugify_ascii | 100 / 126 | 63 / 37 / 0 / 23 | 0 / 3 | 23 / 75 / 2 |
| slugify_boundary | 108 / 133 | 28 / 80 / 0 / 22 | 0 / 3 | 28 / 78 / 2 |

| Case or repository | Selected / discovered | TP / FP / FN / TN | Uncertain selected / unselected | Resolved / conservative / changed |
| --- | ---: | ---: | ---: | ---: |
| tkem/cachetools | 173 / 310 | 6 / 154 / 0 / 134 | 13 / 3 | 0 / 170 / 3 |
| un33k/python-slugify | 208 / 259 | 91 / 117 / 0 / 45 | 0 / 6 | 51 / 153 / 4 |
| untitaker/python-atomicwrites | 12 / 12 | 12 / 0 / 0 / 0 | 0 / 0 | 0 / 12 / 0 |
| V2 overall | 393 / 581 | 109 / 271 / 0 / 179 | 13 / 9 | 51 / 335 / 7 |

LFU remains 138/156 selected, with 6 TP, 124 FP, 0 FN and 18 TN, and all eight
uncertain definitions selected. The other five v2 analyses match their complete
prior hashes. The authored and v1 stable reports match byte for byte. All six
expanded v3 analyses match their prior measurements, including 85/120 selected
and all 12 uncertain outcomes unselected. The original v3 denominator of 90
and its 30 outside-discovery definitions remain frozen separately.

## Receipts and next step

The new [v2 baseline](../corpus/real-v2/baselines/descriptor-binding-v1.json),
[v3 replay](../corpus/real-v3/baselines/descriptor-binding-v1.json) and
[preservation receipt](../benchmarks/descriptor-binding-v1-preservation.json)
link their LFU predecessors. Both evaluators verify the current engine,
measurements and historical chains. V2's only annotation update is the removed
false positive and the current scope wording. App/API/export schema 2.0 and
every previous measurement remain available.

The remaining 30 descriptor false positives include instance forwarding with
arguments, inheritance, escaped wrappers and introspection. The next roadmap
slice is one bounded Slugify fallback mechanism. Its 117 false positives include
legacy/default call paths and unicode-mode bypasses that retain aggregate import
evidence after resolved-path filtering. Study one of those patterns independently
before making a change. Module-data work follows separately. Labels are agent
drafts, and the complete test suite remains the correctness gate. Hosting and
the human pilot stay deferred. Actual verification and manual-review findings
are recorded in [VALIDATION.md](VALIDATION.md#milestone-9b--bounded-descriptor-binding).
