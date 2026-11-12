# Fresh evaluation v2: pre-analysis protocol

Established 2026-11-12 before running the analyzer on any candidate.
Reference: bef99db1bbc144ac399ecb3f537269293fe3f22e.

Purposive selection, not random sampling: two functional Python changes each
from Atomicwrites (file writes), Python Slugify (text processing), and Cachetools
(caching). None appeared in v1. Inspect recent commit descriptions and diffs;
prefer localized bug fixes or API behavior changes with inspectable tests.
Exclude documentation, packaging/release-only, CI-only and test-only commits,
duplicate merge copies, broad multi-feature refactors, unsupported licenses,
and any incomplete or oversized supported tree. Use exact first-parent/head
pairs and existing input limits; do not trim source to meet them. Record actual
selection and exclusion reasons. No analyzer output may inform selection or
cause replacement. This introduces small-project/localized-change bias.

Inspect full supported snapshots as source data. Label every discoverable head
test with source evidence before the first analyzer call. Affected means a
source dependency on an edited callable/default, not a failing assertion;
any demonstrated parameter variant suffices. Changed/new test definitions
are affected themselves. An import alone does not exercise all methods.
Fixture, decorator, inheritance and external-library ambiguity can justify
uncertain labels, which remain in inventory and are excluded only from labeled
precision/recall denominators. Do not guess runtime platform outcomes.

Freeze sources, label hashes, selection and the analyzer hashes before measuring.
Generate the source-only review pack before measurement. All labels are agent
drafted until a real reviewer supplies a dated review record. Preserve initial
measurement and deliberately annotate mistakes afterward without changing labels.
Do not modify the analyzer. Existing authored/v1 datasets remain byte-identical.
Hashes and this process log attest to procedure, not independent certification.
