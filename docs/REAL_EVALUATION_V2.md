# Fresh-repository evaluation v2 — observed results

The original fresh evaluation ran on 2026-11-12 against `bef99db1bbc144ac399ecb3f537269293fe3f22e`.
Its sources, labels and first measurement remain preserved. A subsequent bounded
module-level partial-call fix now uses these cases as **development/regression data**.
All six cases retain agent-drafted labels; no human review or upstream runtime failures
are claimed. These purposive samples are not production accuracy. Keep the full test suite.

[Source protocol](../corpus/real-v2/PROTOCOL.md) · [Original capture/review protocol](../corpus/real-v2/README.md) · [581-label review pack](../corpus/real-v2/REVIEW.md) · [First measurement](../corpus/real-v2/first-run.json) · [Attribution](../corpus/real-v2/ATTRIBUTION.md)

## Current measurement: bounded argument guards

**406/581 selected; 109 TP, 284 FP, 0 FN, 166 TN.** Draft-label precision is
109/393 (27.74%); recall is 109/109 (100%). All 22 uncertain definitions remain:
13 selected and 9 unselected. Exactly seven false positives introduced by partial
binding are removed, with every affected selection retained. These are case/test
pairs with draft labels, not independent executions or production accuracy.

| Case | Selected / tests | TP | FP | FN | TN | Uncertain total / selected | Resolved / fallback / changed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `atomicwrites_path` | 6 / 6 | 6 | 0 | 0 | 0 | 0 / 0 | 0 / 6 / 0 |
| `atomicwrites_prefix` | 6 / 6 | 6 | 0 | 0 | 0 | 0 / 0 | 0 / 6 / 0 |
| `cachetools_descriptor` | 36 / 154 | 0 | 31 | 0 | 115 | 8 / 5 | 0 / 36 / 0 |
| `cachetools_lfu` | 150 / 156 | 6 | 136 | 0 | 6 | 8 / 8 | 0 / 147 / 3 |
| `slugify_ascii` | 100 / 126 | 63 | 37 | 0 | 23 | 3 / 0 | 23 / 75 / 2 |
| `slugify_boundary` | 108 / 133 | 28 | 80 | 0 | 22 | 3 / 0 | 28 / 78 / 2 |

Current explanation totals: **51 resolved paths, 348 conservative paths, 7 changed tests**.
Atomicwrites and Cachetools measurements are unchanged. Slugify selects **208/259**:
91 TP, 117 FP, 0 FN, 45 TN; all six uncertain IDs remain unselected. The graph is
unchanged. Twenty retained ASCII-case evidence paths now follow `_modern_slugify`
instead of the legacy branch, consistent with the bound `algorithm="modern"`;
their scores, distances, reason categories and revision presence are unchanged.

The seven removed IDs are listed in the intermediate measurement below. Three use
`allow_unicode=True`; four case/test pairs reject invalid lengths/separators before
calling the edited helper. Filtering applies only to bounded resolved call paths;
other module/import fallback remains. Unknown/modified arguments, callbacks,
mutable partial keywords and unsupported control flow retain recommendations.

The [new active baseline](../corpus/real-v2/baselines/argument-guards-v1.json) stores
current measurements and hashes separately. **Both prior v2 baselines, every
snapshot/label and all provenance remain byte-identical.** The gate verifies these
receipts and current results without relabeling or accepting drift automatically.

## Intermediate measurement: bounded partial binding (preserved)


**413/581 selected; 109 TP, 291 FP, 0 FN, 159 TN.** Draft-label precision is
109/400 (27.25%); recall is 109/109 (100%). All 22 uncertain definitions remain:
13 selected and 9 unselected. These are case/test pairs, not independent executions.
All **44 original misses** are now selected, alongside **seven new false positives**.
The fixed call edges identify the underlying function; they do not prune branches
based on bound/call-site arguments or prove that a test runs/fails.

| Case | Selected / tests | TP | FP | FN | TN | Uncertain total / selected | Resolved / fallback / changed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `atomicwrites_path` | 6 / 6 | 6 | 0 | 0 | 0 | 0 / 0 | 0 / 6 / 0 |
| `atomicwrites_prefix` | 6 / 6 | 6 | 0 | 0 | 0 | 0 / 0 | 0 / 6 / 0 |
| `cachetools_descriptor` | 36 / 154 | 0 | 31 | 0 | 115 | 8 / 5 | 0 / 36 / 0 |
| `cachetools_lfu` | 150 / 156 | 6 | 136 | 0 | 6 | 8 / 8 | 0 / 147 / 3 |
| `slugify_ascii` | 105 / 126 | 63 | 42 | 0 | 18 | 3 / 0 | 28 / 75 / 2 |
| `slugify_boundary` | 110 / 133 | 28 | 82 | 0 | 20 | 3 / 0 | 30 / 78 / 2 |

Intermediate totals: **58 resolved-call paths, 348 conservative fallback paths, 7 changed tests**.
Atomicwrites and Cachetools measurements are unchanged. Slugify then selected 215/259:
91 TP, 124 FP, 0 FN, 38 TN; all six uncertain definitions remain unselected.
Exact IDs, reason counts and evidence are retained in the generated report and the
[preserved partial baseline](../corpus/real-v2/baselines/module-partial-v1.json).

The seven false positives introduced at that stage (now removed) were:

- `ModernArgumentValidationTests.test_modern_rejects_bool_and_non_int_max_length`
  and `.test_modern_rejects_non_str_separator`, in both cases (four case/test pairs).
  Source validation raises before reaching the edited helper; the resolved call path
  did not yet account for that early exit.
- `ReleaseRegressionTests.test_modern_fitting_post_replacements_preserve_delimiters`,
  `.test_modern_hard_cut_does_not_end_in_post_replacement_delimiters`, and
  `.test_modern_word_boundary_hard_cut_keeps_delimiters_with_the_next_word` in
  `slugify_ascii`. Each uses `allow_unicode=True`, bypassing the changed transliterator.

All live in `tests/test_release.py`. The original unaffected labels/rationales are
unchanged. Existing 284 false positives remain, including the Cachetools fallback
examples below. That milestone stopped at bounded call binding; the subsequent guard filter above repairs these seven.

## Original measurement (preserved)


**362/581 static test definitions selected; 65 TP, 284 FP, 44 FN, 166 TN.**
Precision is 65/349 (18.6%); recall is 65/109 (59.6%) against classified draft labels.
All **22 uncertain definitions** remain counted: **13 selected, 9 unselected**.
These totals count case/test pairs; repeated revisions and tests are not independent samples.
These are the original `bef99db` results; the current gate uses the separate argument-guard baseline above.

| Case | Selected / tests | TP | FP | FN | TN | Uncertain total / selected | Resolved / fallback / changed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `atomicwrites_path` | 6 / 6 | 6 | 0 | 0 | 0 | 0 / 0 | 0 / 6 / 0 |
| `atomicwrites_prefix` | 6 / 6 | 6 | 0 | 0 | 0 | 0 / 0 | 0 / 6 / 0 |
| `cachetools_descriptor` | 36 / 154 | 0 | 31 | 0 | 115 | 8 / 5 | 0 / 36 / 0 |
| `cachetools_lfu` | 150 / 156 | 6 | 136 | 0 | 6 | 8 / 8 | 0 / 147 / 3 |
| `slugify_ascii` | 80 / 126 | 43 | 37 | 20 | 23 | 3 / 0 | 3 / 75 / 2 |
| `slugify_boundary` | 84 / 133 | 4 | 80 | 24 | 22 | 3 / 0 | 3 / 79 / 2 |

Aggregate reasons: **6 resolved-call paths, 349 conservative module/import paths,
7 changed tests**. Original selected IDs are retained per case and repository in `first-run.json`.
The generated `reports/real-v2-evaluation.json` contains current IDs and all typed
evidence paths, full snapshots, source ranges and revision evidence, plus the
original aggregate summary. The root dataset documents remain preserved as the
original capture record; current gate behavior is documented below.

| Repository | Selected / tests | TP | FP | FN | TN | Uncertain total / selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `tkem/cachetools` | 186 / 310 | 6 | 167 | 0 | 121 | 16 / 13 |
| `un33k/python-slugify` | 164 / 259 | 47 | 117 | 44 | 45 | 6 / 0 |
| `untitaker/python-atomicwrites` | 12 / 12 | 12 | 0 | 0 | 0 | 0 / 0 |

## Exact changes and complete supported coverage

| Case / change | Before | After | Python files before / after | Source bytes before / after |
| --- | --- | --- | ---: | ---: |
| [atomicwrites_path](https://github.com/untitaker/python-atomicwrites/commit/2a91f2ef3e85b6a6c4dca3209a02eaba9b003059) | `4705e84ce6cb31b6df0bd6a641280617b27b66d0` | `2a91f2ef3e85b6a6c4dca3209a02eaba9b003059` | 4 / 4 | 13827 / 14052 |
| [atomicwrites_prefix](https://github.com/untitaker/python-atomicwrites/commit/4705e84ce6cb31b6df0bd6a641280617b27b66d0) | `55eed75c5d1337380314d03098703289e511af29` | `4705e84ce6cb31b6df0bd6a641280617b27b66d0` | 4 / 4 | 13820 / 13827 |
| [slugify_boundary](https://github.com/un33k/python-slugify/commit/c9e9698c70c8fe1ffe6e13158bb19a6251471b8b) | `b91081447b68517081089aeb758628036fd79222` | `c9e9698c70c8fe1ffe6e13158bb19a6251471b8b` | 16 / 17 | 91297 / 93508 |
| [slugify_ascii](https://github.com/un33k/python-slugify/commit/cf6cd3dad45dea9641755adab80c00a9dbaee709) | `2fe6cec4842039814217cb8d089c6fcb9f8c154b` | `cf6cd3dad45dea9641755adab80c00a9dbaee709` | 14 / 14 | 86856 / 87582 |
| [cachetools_lfu](https://github.com/tkem/cachetools/commit/e96310286ed0f5a8bcb5a2f52adc1bab7ebe8634) | `825bf661a71b910693b0b289ec3ee12978046b73` | `e96310286ed0f5a8bcb5a2f52adc1bab7ebe8634` | 21 / 21 | 195711 / 196523 |
| [cachetools_descriptor](https://github.com/tkem/cachetools/commit/8c953ab8cabb147c6921b5d08d262078e22891ec) | `ba26e56aee0670a28979f02b94fb344515fe33ab` | `8c953ab8cabb147c6921b5d08d262078e22891ec` | 21 / 21 | 195140 / 195143 |

Every revision includes its complete supported Python tree, including setup, documentation
configuration and helper scripts. No repository was trimmed or replaced after analysis.
All selected licenses are MIT. Ten considered changes were excluded for documented
source-scope reasons; none of the three repositories exceeded limits. The sample favors
localized changes and manually inspectable small libraries; it is not newest-two or random sampling.
Atomicwrites is historical/unmaintained; its inclusion is evaluation data, not a library recommendation.

## Concrete mistakes in the original measurement

1. **Originally missed partial-bound modern calls (44 FNs, now repaired).**
   `tests/test_release.py::ModernArgumentValidationTests.test_modern_accepts_valid_int_max_length`
   calls the module binding `slugify = partial(public_slugify, algorithm="modern")`.
   Source inspection follows that binding into `_modern_slugify` and the edited helper.
   The reference analyzer retains only the test-to-module edge and does not recover
   this dependency. Both the ASCII and truncation changes miss this unchanged test.
2. **Legacy and unicode-bypass overselection (117 FPs across Slugify).**
   `TestSlugify.test_accented_text` in `tests/test_legacy.py` uses the legacy default,
   yet the boundary change selects it through a conservative path to
   `slugify/slugify.py::<module>`. For the ASCII change, the unicode-mode counterpart
   bypasses `_transliterate` but is selected. General body-change branch filtering
   is outside the existing constructor/default-only argument filter.
3. **Protocol fallback across unrelated caches (136 FPs).**
   `tests/test_cached.py::CacheWrapperTest.test_decorator_cond_info` uses a generic
   `Cache`, not LFUCache. Its path is `test → test module → cachetools module`.
   The reference warning explicitly retains broad fallback for an unmodeled protocol
   change. Similar paths reach FIFO/LRU/TTL controls. No precise LFU dependency is claimed.
4. **Deprecated classmethod fallback reaches ordinary instance methods (31 FPs).**
   `CacheMethodTest.test_cond_nospace` reaches `Cached → cachedmethod → _cachedmethod module
   → _descriptor module`, although the edit is confined to `_ClassMethodDescriptor.__call__`.
   The eight actual classmethod IDs stay uncertain because behavior differs with Python version;
   five are selected. This case has no classified affected definitions, so recall is null.

## What this evaluation does not measure

- Source dependencies are labeled at callable/default level, not changed-line execution or failures.
  A valid call into an edited function can be affected even if a particular edited branch is not taken.
- Slugify subprocess-only tests and README-executed examples remain uncertain; analyzed source
  was never run, and non-Python README contents/installed subprocess identity are not assumed.
- Cachetools mixin definitions reused by incompatible cache subclasses are pooled uncertain IDs.
  Tests named exactly `test` and inherited methods defined in `tests/__init__.py` are outside
  CodeImpact's existing `test_*`/test-file discovery rule; no pytest/unittest collection was run.
- Atomicwrites has six affected discovered tests and no unaffected controls in its complete trees.
  No synthetic control was added to improve these denominators.
- Git tree/blob integrity is verified offline. Capture metadata is an HTTPS attestation, not
  commit-signature authentication or independent proof of label authorship/timing.

## Reproduce and interpret the gate

```sh
make evaluate-real-v2
```

The first run correctly exited 1 against empty discrepancy annotations. Its measured IDs,
counts, classifications, explanation categories, per-case stable-analysis hashes, and raw
report hash are retained in `first-run.json`. Only discrepancy maps, selected-uncertain
baselines and limitation explanations were then deliberately annotated. All 581 labels,
sources, provenance and review-pack bytes stayed fixed. The partial and argument-guard milestones add separate versioned baselines with
current source hashes, measurements and in-memory discrepancy overlays. Original case
files, first-run receipt, `module-partial-v1`, labels, source, provenance and review
bytes remain untouched. The current gate verifies the preserved historical inputs,
the previous baseline's file hash, and the active argument-guard baseline.
Exit 0 means the active imperfect baseline matches; 1 means measured drift; 2 means
invalid inputs/provenance/evidence, changed current engine, or invalid output.
Fresh wrapper **3.0** reports original and partial summaries alongside current results;
`first_measurement_matches` is false and `current_measurement_matches` is true.
Historical engines are not rerun by this command. The dataset's root documents remain
preserved as the original capture record; current reproduction is this section.

The original authored corpus remains **23 TP / 0 FP / 2 FN / 32 TN**, plus two uncertain
selections. V1 remains **45 TP / 0 FP / 0 FN / 123 TN**, plus 11 uncertain selections.
All original dataset bytes and stable reports are preserved; they are not pooled into v2 metrics.

## Recommended next analyzer milestone

**Bounded protocol-aware fallback narrowing for Cachetools.** Begin with the 136
LFU-change false positives versus unaffected cache implementations, retaining unknown
receivers, shared mixins and uncertain labels. Treat the 31 descriptor/classmethod
fallback mistakes as a separate scope. Slugify's 117 remaining fallback mistakes
also need work beyond the current resolved-path filter. Preserve all three v2
measurements and every label; independent human review remains outstanding. Fixture
injection, runtime imports and general dynamic dispatch remain separate limitations.
