# Independent source-label review pilot for real evaluation v4

**Self-review complete.** The original draft author reviewed both cases and
retained all 51 labels. The owner chose to skip the independent human-review
pilot. The two cases retain their draft classifications, including seven
uncertain labels. The review packets, submitted self-review records and frozen
measurements remain available.

| Case | Affected | Unaffected | Uncertain | Total |
| --- | ---: | ---: | ---: | ---: |
| `humanize_small_delta` | 5 | 28 | 0 | 33 |
| `oyaml_error_context` | 3 | 8 | 7 | 18 |
| **Total** | **8** | **36** | **7** | **51** |

The packets include both pinned commits, a complete captured Python diff,
definition line spans, existing draft rationales, and numbered source from both
revisions. They include file hashes and license notices. The Markdown works with
the companion JSON template offline. Reviewers get the source, discovery
inventory, and draft labels before viewing analyzer results.
[Original source-only review workflow](../corpus/real-v4/REVIEW_WORKFLOW.md)

## Prepare the packets

Run from the CodeImpact repository root.

```sh
packet_dir=reports/real-v4-review-pilot
mkdir -p "$packet_dir"
for case_id in humanize_small_delta oyaml_error_context; do
  .venv/bin/python -m scripts.review_real_v4 --pilot-packet "$case_id" \
    > "$packet_dir/$case_id.md"
  .venv/bin/python -m scripts.review_real_v4 --template "$case_id" \
    > "$packet_dir/$case_id-template.json"
done
.venv/bin/python -m scripts.review_real_v4 --summarize > "$packet_dir/summary.json"
```

Send each reviewer the Markdown packet and blank JSON template for their case.
The maintainer summary is for the maintainer. Store submitted records outside
`corpus/real-v4` and include only explicit submissions when generating a summary.

## Review a case

In the directory containing the packet and template, copy the template to a
working record. Set `case_id` to the case you received.

```sh
case_id=humanize_small_delta
cp "$case_id-template.json" "$case_id-review.json"
```

1. Read the packet and check the relevant change, test inputs, and setup in both
   revisions. Use `uncertain` where the pinned source leaves an important
   dependency unproved.
2. Edit the copied JSON. Enter your name in `reviewer`, an ISO date in
   `reviewed_on`, a traceable `review_reference`, and any discovery observations
   in `discovery_notes`. Keep the pinned hashes and each `original` label.
3. For each reviewed test, enter its `proposed` label, your rationale, and at
   least one `evidence` span. A span uses `revision` (`base` or `head`), `path`,
   `line`, and inclusive `end_line`. Use the numbered source in the packet.
   An agreement also needs rationale and evidence.
4. Delete the entries you have not reviewed from `decisions`. Send the copied
   JSON record to the maintainer. Reviewers with a configured checkout can use
   the same validation command as the maintainer.

## Validate and summarize submissions

Run from the repository root. Replace the example paths with the submitted
records. Pass one record per reviewer per case. If a reviewer sends an update,
choose the intended record before summarizing.

```sh
.venv/bin/python -m scripts.review_real_v4 \
  --validate reports/label-reviews/humanize_small_delta-review.json

packet_dir=reports/real-v4-review-pilot
.venv/bin/python -m scripts.review_real_v4 --summarize \
  reports/label-reviews/humanize_small_delta-review.json \
  reports/label-reviews/oyaml_error_context-review.json \
  > "$packet_dir/summary.new.json" &&
  mv "$packet_dir/summary.new.json" "$packet_dir/summary.json"
```

`--summarize` with no paths reports readiness and lists every unreviewed ID.
When records are present, the summary counts definitions once per case and
retains each rationale and cited span.

- **Agreement** means all submitted decisions for that ID match its draft.
- **Proposed label change** means the submitted decisions agree on a different
  label.
- **Unresolved disagreement** means reviewers proposed different labels. The
  summary preserves every proposal and its evidence rather than voting.
- **Unreviewed** means no record contains a decision for that ID.

A partial record contributes only its recorded decisions and discovery notes.
Complete coverage means every ID has a decision from at least one reviewer. It
can still include unresolved disagreements. Validation checks record structure,
frozen hashes, known IDs, and pinned source ranges. Maintainers verify reviewer
independence and the substance of the evidence separately.

Review records and summaries are separate from the published measurements.
Any approved label revision follows the existing workflow for a new versioned
label receipt and evaluation.
