# Human source-label review

Status is **pending independent review**. Review the pinned source and draft
rationales in [REVIEW.md](REVIEW.md) before looking at recommendations or scores.
Check both revisions, the changed source, concrete calls, and the applicable
test input or setup path. Affected means a source dependency on the change.
Record uncertainty for unclear dispatch, fixture, or external-library behavior.
The outside-discovery list describes scope. It does not assign metric labels.

Work from the repository root. Create a separate record outside the frozen
dataset for each case you review.

```sh
mkdir -p reports/label-reviews
.venv/bin/python -m scripts.review_real_v4 --template humanize_small_delta \
  > reports/label-reviews/humanize-small-delta-review.json
```

Replace the blank reviewer name, ISO date, review reference and discovery notes.
The notes should confirm or question the discovery inventory and mention any
excluded definitions you examined. For each decision, retain `original` and
set `proposed` to affected, unaffected or uncertain. Keep the same value to
record agreement. Add a rationale and one or more pinned source spans with
`revision` (base or head), `path`, `line` and inclusive `end_line`. Delete
unreviewed decisions from a partial record. A zero-discovery case has no label
decisions, so record any observations in the discovery notes.

```sh
.venv/bin/python -m scripts.review_real_v4 \
  --validate reports/label-reviews/humanize-small-delta-review.json
```

The validator reports remaining IDs and proposed revisions. It verifies the
frozen input and label hashes, record structure, original classifications and
cited source ranges. Independent identity and correctness still require a
human. Share the reviewed record with the maintainer using the chosen review
reference. A future approved label revision must cite the reviewer, date,
source and old/new classifications and use a separate versioned label receipt
and measurement. Keep this dataset, original labels and first-run receipt
intact. A review record neither changes the metrics nor upgrades v4's draft
status automatically.

Regenerate the source-only pack with
`.venv/bin/python -m scripts.review_real_v4` and compare it with `REVIEW.md`.
These commands read saved source as data. No upstream tests run.
