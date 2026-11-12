# Fresh-repository evaluation v2

Six pinned changes across Atomicwrites, Python Slugify and Cachetools, kept separate
from the authored 25 and real-source v1 six. All 581 labels are agent drafts.
No upstream source/tests/dependencies were executed, imported, installed or checked out.

## Run offline

```sh
make evaluate-real-v2
# reports/real-v2-evaluation.json: full snapshots, IDs, metrics and evidence
.venv/bin/python scripts/review_real.py --corpus corpus/real-v2 > reports/v2-label-review.md
```

The review generator inspects source only; it does not run the analyzer. Compare
its output with REVIEW.md. CI runs all three offline evaluations after make check.
No credential, download, upstream installation or live GitHub call is needed.
Exit 0 means the recorded mistakes are reproduced, 1 means baseline drift, and
2 means invalid data/evidence, changed frozen analyzer or invalid output. No
command auto-relabels, updates baselines, or writes inside this dataset.

## Files and boundaries

- PROTOCOL.md and selection.json record pre-analysis policy, exact revisions,
  selection reasons and ten considered/excluded changes.
- cases/ contains complete supported Python snapshots and exhaustive head-test
  labels. Provenance retains full trees, exact source hashes and license bytes.
- frozen-inputs.json records the reference analyzer commit, six engine/ingestion
  source hashes, canonical snapshot/label/selection hashes, and review-pack hash.
- first-run.json preserves first measured IDs/counts/classifications/explanations,
  per-case analysis hashes, original empty-baseline drift and full raw-report hash.
  Full evidence is reproducible with the command above; the 6.5 MB initial raw
  report is an ignored local artifact, not required for offline replay.
- preservation.json pins every original authored/v1 dataset file and both stable
  report byte hashes. Regression tests validate these separately.
- REVIEW.md lists every draft label and pinned source reference. REVIEW_NOTES.md
  provides a blank human review record; it does not claim a review occurred.
- licenses/ and ATTRIBUTION.md retain original MIT notices for redistribution.

All ordinary UTF-8 .py blobs in supported scope are preserved; existing excluded
folders, symlinks and submodules remain outside that scope. None of these twelve
revisions has excluded Python paths, symlinks or submodules. Non-Python tree
entries are preserved, but their bytes are not, except licenses. No silent trimming.
Limits remain 300 Python files, 200,000 bytes/file, 2 MB/revision, 1 MB/case and
20 MB corpus input. Metadata stays at 4 MB/file and 20 MB total, including v2
receipts and the frozen review pack. Capture uses existing request/time/byte limits.

The first measured total is 65 TP, 284 FP, 44 FN, 166 TN; 362/581 selected, including
13 of 22 uncertain definitions. See the separate [results](../../docs/REAL_EVALUATION_V2.md).
Uncertain counts include unselected tests. No labels were changed to improve metrics.
First-run selection is fresh relative to the frozen engine, not an independently
reviewed benchmark; using these cases for subsequent fixes makes them regression data.

## Human review and subsequent revisions

Read PROTOCOL.md, REVIEW.md and pinned sources before measured recommendations.
Record actual reviewer, date, test IDs, evidence links and disagreements in
REVIEW_NOTES.md. Keep insufficiently supported judgments uncertain. Hashes attest
to file integrity, not independent certification or correctness of the labels.
Do not mark a case reviewed without a completed real review and its reference.

This gate intentionally pins the initial engine and first measurement. Do not
rewrite first-run.json to make a change pass. A later authorized analyzer/label
milestone must retain these initial receipts and explicitly version its new engine,
labels and baseline, with an explained diff and updated gate. A genuine human review
can be recorded now without rewriting the historical draft assessment. Both dataset
and report schemas remain explicit: v2 adds fresh_evaluation_schema_version 1.0,
while retaining dataset wrapper 1.0, evaluation 1.0 and analysis report 2.0.

Optional online recapture, never needed by evaluation or CI:

```sh
.venv/bin/python scripts/capture_real.py --selection corpus/real-v2/selection.json --output reports/v2-recapture
```

Use a new directory; the existing bounded capture script refuses overwrites.
Verify original trees/blobs/licenses against the receipts. The receipts are HTTPS
capture attestations, not signed commit authentication; coordinated changes to
all receipts cannot be detected by self-contained hashes alone.
