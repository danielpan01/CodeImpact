# Real-repository evaluation v1

This is a **six-change purposive pilot**, separate from the 25 authored examples
in `../cases`. It measures agreement with **agent-drafted dependency labels**.
It is not independently reviewed ground truth, runtime failure evidence, or a
production accuracy benchmark. No upstream test, import, dependency installation,
checkout, build, or setup script was executed.

## Reproduce offline

From the CodeImpact root, using the installed pinned development environment:

```sh
make evaluate-real
# All selected IDs, classifications, snapshots and evidence:
# reports/real-evaluation.json
.venv/bin/python scripts/review_real.py > reports/real-label-review.md
```

The evaluation and review generator need no network or GitHub credential. The
review generator does not invoke the analyzer. Exit codes for evaluation are 0
(recorded baseline matches), 1 (discrepancies drifted), and 2 (invalid input,
provenance, evidence or output). A passing baseline **retains recorded mistakes**.
Reports cannot be written inside the dataset. No command automatically relabels
cases or accepts a new baseline.

## Selection and source provenance

[selection.json](selection.json) records the policy, all revision pins, reasons
for selection, and eight considered/excluded changes. The pilot covers MarkupSafe,
ItsDangerous and Schedule: small public libraries for HTML strings, signed
serialization and scheduling, with two functional changes each. These repositories
were chosen for bounded inspection and permissive licenses, before analyzer output.
This is not random sampling, the latest two changes, or representative of Python.
No repository was rejected for size; all three fit. Exclusions concern changes,
not fabricated repository candidates. Two selected heads are merge commits; every
case compares the head with its explicitly recorded first parent, not a PR branch
or an inferred moving reference.

Captured on 2026-11-11 using `scripts/capture_real.py` and the existing bounded
GitHub REST Git-object reader over HTTPS. The script checks public repository
identity and reads immutable commits, complete recursive trees, Python blobs and
root license blobs. Optional `gh auth token` authentication stays in memory and
is never stored in dataset files. It never clones, extracts an archive, or imports
upstream source. Future recapture is optional and online:

```sh
.venv/bin/python scripts/capture_real.py --output reports/real-recapture
```

Use a new output directory; existing capture files are never overwritten. Capture
is not required by `make evaluate-real` and does not draft labels or update cases.
Compare a recapture with `cases/` and `provenance/` explicitly before accepting it.

- `cases/<id>.json`: complete supported before/after Python source strings using
  the existing corpus schema 1.0, plus every discovered test's label and rationale.
- `provenance/<id>.json`: repository/change URL, exact commit/parent/tree objects,
  full recursive tree inventory (including non-Python entries), every Python file's
  SHA-256, original Git blob SHA-1 and size, complete original license text/hash,
  selection rationale and label-review metadata.
- [ATTRIBUTION.md](ATTRIBUTION.md): copyright notices and accessible license copies.
- [REVIEW.md](REVIEW.md): all six Python diffs, 201 label checkboxes/rationales,
  source links pinned to the head revision, frozen label hashes, and exclusions.

The snapshots include **all ordinary UTF-8 `.py` blobs in supported scope**,
including tests, setup files, benchmarks, examples and docs configuration. They are
source data, not importable fixture directories. Existing exclusions remain
`.venv`, `venv`, `node_modules`, `vendor`, `.git`, symlinks and submodules. C source,
non-Python files and project dependencies are outside analysis scope; their tree
entries are retained, not their contents (except licenses). None of the twelve
captured revisions has excluded Python paths, symlinks or submodules. This is
complete supported Python coverage, not a claim to preserve every repository byte.

Existing source limits are unchanged: 300 Python files, 200,000 bytes per file,
2,000,000 bytes per revision; recursive trees at most 20,000 entries. Capture keeps
4 MB per response, 20 MB network bytes, 650 requests and a 60-second case deadline.
The real cases reuse the authored loader's 1 MB per case / 20 MB corpus budget.
Additional metadata is bounded at 4 MB per file / 20 MB total. Oversized, truncated,
non-UTF-8 or incomplete inputs fail; nothing is silently trimmed.

Offline validation reconstructs Git tree objects from the complete inventory,
checks all subtree/root SHA-1s, matches the exact supported path set, verifies both
SHA-1/size and SHA-256 for source, and verifies original license bytes against the
recorded tree. It checks selected revision IDs, first-parent linkage, URLs and
frozen label hashes. Commit receipts are HTTPS capture attestations: offline checks
**do not reconstruct raw commit objects, verify commit signatures, or authenticate
GitHub afresh**. Coordinated replacement of all metadata is outside this integrity
check; review version-control diffs and recapture from the recorded URLs as needed.

## Label protocol and review status

All 201 definition IDs were labeled from source inspection before the first
analyzer run. Initial labels: 45 affected, 123 unaffected, 33 uncertain. Their
canonical hashes were frozen in provenance. The hash protects against accidental
label drift; it is not independent proof of drafting time or review. The process
order is documented here as an agent attestation.

An affected label means the visible test exercises the changed callable, consumes
the changed default, or reaches it through an inspected fixture chain. It does not
mean an assertion will fail. Function-level dependency can count even when a new
branch is not taken. Module import alone, or construction of a class with an
unrelated edited method, is insufficient. For the FIPS case this is a source-level
default-digest dependency assessment, not a measurement of FIPS import failures.

The unit is CodeImpact's static definition ID. Parametrized executions are not
expanded; one known dependent variant can establish dependency for that definition.
Inherited definitions reused with conflicting fixture contexts are left uncertain
in the timestamp case. MarkupSafe's C/native fixture variants are also uncertain
where Python-only inspection cannot establish behavior. All uncertain tests and
selected uncertain recommendations are counted separately; neither is silently
folded into TP/FP/FN/TN or precision/recall. Repeated test IDs in different changes
are separate **case-test pairs**, not independent population samples.

Review status is `draft` for every case, author `Codex`, reviewer/reference null.
A human reviewer should:

1. Read REVIEW.md, the complete snapshots, fixture definitions and pinned diffs
   before viewing the measured recommendations. Check the C/inheritance uncertainty
   policy explicitly; preserve uncertainty where evidence is insufficient.
2. Record disagreements and source references. Changing a label requires an
   explicit rationale, a deliberate label-hash update, and a retained review record;
   never change labels solely to match CodeImpact output.
3. Only after reviewing the whole case, set `label_review.status` to `reviewed`,
   with an actual named reviewer and `review_reference` (a review URL or record).
   The loader requires both fields; their presence is not independent certification.
4. Regenerate the review pack, rerun evaluation, and inspect baseline differences.
   Update known FP/FN annotations only after interpreting them, preserving source
   pins and the 25 authored cases. Update the results document with actual changes.

The initial baseline was recorded **after** the first evaluation, without changing
frozen labels or sources and without tuning the analyzer. A subsequent user-requested
selection refinement used these cases to diagnose class/module overselection. They
are now development/regression data, not an unseen benchmark. All six cases remain
`known_limitation`, all label statuses remain draft, and source/provenance/label
hashes and the review pack are unchanged. Only discrepancy annotations and limitation
explanations changed. Prior annotations and selected IDs for both datasets are
retained in [the historical baseline](../selection-baseline-v1.json).

Current selection is 56/201: 45 TP, 0 FP, 0 FN, 123 TN and 11 selected uncertain tests
out of 33. Bounded constructor/factory argument tracking removes the four previous
default-initialization FPs. The archive also retains the intermediate 60-selection
baseline. Neither update changes source, frozen labels, review status or provenance. Scoring, stable IDs,
report schema 2.0 and dashboard design are unchanged. See [measured results](../../docs/REAL_EVALUATION.md)
for per-case explanations, exact selected IDs and limitations. Authored case source
and labels are also preserved; their six former false-positive annotations were
deliberately updated by this follow-up fix.
