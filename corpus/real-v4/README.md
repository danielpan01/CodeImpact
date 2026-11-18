# Fresh-repository evaluation v4

Six pinned first-parent changes across new public repositories. The protocol,
candidate decisions, complete supported Python snapshots, provenance, source-only
labels and review pack were frozen before measurement on the PR #22 analyzer.

- [Selection protocol](PROTOCOL.md) and [candidate decisions](CANDIDATES.md)
- [Source-only review pack](REVIEW.md) and [review workflow](REVIEW_WORKFLOW.md)
- [License attribution](ATTRIBUTION.md) and exact base/head notices under `licenses/`
- [Evaluation results](../../docs/REAL_EVALUATION_V4.md)

Run `make evaluate-real-v4` from the project root. It verifies the freeze and
reports to `reports/real-v4-evaluation.json`. The original result is pinned by
`first-run.json`. The separate `baseline.json` enumerates expected mistakes
and uncertain selections. Labels and metrics apply to discovered definition IDs.
IceCream's unittest-style methods are listed outside discovery.

Git tree reconstruction, blob checks and source SHA-256 provide integrity
against the recorded pins. The commits and first-parent metadata come from the
public GitHub API. They are capture records rather than raw signed-commit
verification. Capture and replay treat upstream source as data.
