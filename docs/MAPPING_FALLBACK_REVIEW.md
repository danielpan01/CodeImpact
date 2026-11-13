# Mapping fallback: source controls and review status

November 12, 2026. Independent human label review is **pending**. No reviewer,
review date or approval is recorded. The six v2 provenance records still say
`draft`, with null reviewer/reference; their original labels and review-pack bytes
are unchanged. The owner's waiver of the frontend developer walkthrough was a
separate usability decision and does not constitute source-label approval.

These are agent source-inspection notes for the bounded LFU milestone. Source was
read from the pinned JSON snapshots as data. No Cachetools code was imported,
installed, checked out or executed. Existing labels informed implementation, so the
results are development/regression measurements, not independent accuracy.

## Source boundary

The [original LFU case](../corpus/real-v2/cases/cachetools_lfu.json) pins Cachetools
`825bf661a71b910693b0b289ec3ee12978046b73` →
`e96310286ed0f5a8bcb5a2f52adc1bab7ebe8634`. It contains complete supported Python
trees, six affected labels, 142 unaffected labels and eight pooled uncertain labels.
The change rewrites LFU-specific storage/touch behavior; sibling cache implementations
share `Cache` but do not inherit `LFUCache`. Item operations alone previously kept
the entire importing test module in aggregate fallback.

The bounded query can distinguish the following known sibling receivers and their
source methods in both revisions. Eleven originally selected unaffected definitions
are now omitted; their labels and rationale text are unchanged:

| Pinned source file / class | Removed test definitions | Source basis |
| --- | --- | --- |
| `tests/test_fifo.py::FIFOCacheTest` | `test_fifo`, `test_fifo_getsizeof`, `test_fifo_update_existing` | Constructs `FIFOCache`; queue ordering and item operations follow FIFO/Cache methods, not LFU |
| `tests/test_lru.py::LRUCacheTest` | `test_lru`, `test_lru_clear`, `test_lru_getsizeof`, `test_lru_update_existing` | Constructs `LRUCache`; its ordered storage, clearing and inherited Cache operations are separate from LFU |
| `tests/test_rr.py::RRCacheTest` | `test_rr`, `test_rr_default_choice`, `test_rr_getsizeof`, `test_rr_update_existing` | Constructs `RRCache`; random/custom-choice eviction and Cache storage do not use LFU's link/touch implementation |

The mapping ABC generic aliases and lexical private fields are necessary to identify
these source receivers. This does not prove runtime non-failure, callback purity or
safe test skipping. Unknown arguments/receivers, pooled inherited mixins, custom
hooks and assigned callables retain the conservative path. In particular,
`tests/test_func.py::TTLDecoratorTest.test_ttl_datetime` remains selected: the
class-stored decorator is outside the bounded callable proof.

## Observed outcome and retained work

LFU changes from 150/156 selected (6 TP, 136 FP, 0 FN, 6 TN, 8 uncertain selected)
to **139/156 selected (6 TP, 125 FP, 0 FN, 17 TN, 8 uncertain selected)**. All six
affected IDs and all eight uncertain IDs are retained. The 11 omitted definitions
were false positives under the existing draft labels; no labels were revised after
observing the new result.

The graph, source evidence and changed/deleted IDs are unchanged. All 139 retained
recommendations keep their scores, distances, reason categories and revision presence;
22 switch from an unrelated class path to an existing test-module import path.
Every path passes evidence validation. The five other v2 analyses are identical. The descriptor case still
has 31 false positives and 5/8 uncertain selections; the two Slugify cases retain
117 false positives and all six uncertain IDs unselected. Authored/v1 reports are
byte-identical. Overall v2 is 109 TP / 273 FP / 0 FN / 177 TN, with 13/22 uncertain
selections. No stronger population-level accuracy claim follows from these counts.

The [new baseline](../corpus/real-v2/baselines/mapping-fallback-v1.json) is separate
from the original first run, partial and argument baselines. It pins current engine
hashes and an in-memory discrepancy overlay. All original corpus bytes remain
intact. The [validation record](VALIDATION.md) records checks; the
[581-label review pack](../corpus/real-v2/REVIEW.md) remains the source for a future
independent reviewer. Review should include the removed controls, retained LFU
positives, shared mixin uncertainty and descriptor/version caveats before broader
accuracy claims. No person has been contacted or credited with that review.
