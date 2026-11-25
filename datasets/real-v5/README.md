# Real evaluation v5

The four selected single-parent changes come from Cached Property and Python
SemVer. [Protocol](PROTOCOL.md) records the selection rules and
[Candidates](CANDIDATES.md) records the inspected prefixes. Both were completed
before the first analyzer run. Benefits and limitations are recorded in the
[v5 results](../../docs/REAL_EVALUATION_V5.md).

The case JSON stores complete supported Python source for each pinned revision.
Each provenance record binds that source to its Git tree, blob IDs, SHA-256
digests, first-parent relationship, and root BSD-3-Clause notice. The license
files reproduce those notices verbatim. Follow the change links from the
selection log and use the pinned paths in each draft rationale to inspect the
dependencies. The replay verifies the captured Git tree and source hashes
locally. The receipts do not authenticate the service that supplied them.

`discovery.json` inventories both revisions. `frozen-inputs.json` binds the
selection, snapshots, notices, draft labels and reference analyzer bytes.
`first-run.json` preserves the first stable measurement and exact
recommendation paths. `baseline.json` separately records the observed
discrepancies and uncertain selections. Run `make evaluate-real-v5` from the
project root. The gate writes the full stable report to
`reports/real-v5-evaluation.json` without contacting the upstream repositories.
Human review was skipped at the owner's direction. The labels remain drafts.
