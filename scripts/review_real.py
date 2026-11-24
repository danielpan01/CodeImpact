"""Render a deterministic, source-only label review pack, without running the analyzer."""

import argparse
import ast
import difflib
from pathlib import Path
from urllib.parse import quote

from codeimpact.discovery import LEGACY_POLICY
from codeimpact.real_evaluate import load_real


def python_diff(case):
    lines = []
    for path in sorted(case.request.base.files.keys() | case.request.head.files.keys()):
        lines.extend(
            line.rstrip("\n")
            for line in difflib.unified_diff(
                case.request.base.files.get(path, "").splitlines(True),
                case.request.head.files.get(path, "").splitlines(True),
                fromfile="base/" + path,
                tofile="head/" + path,
            )
        )
    return lines


def review_pack(directory, *, discovery_policy=LEGACY_POLICY, outside=None):
    selection, cases, provenance, _ = load_real(directory, discovery_policy=discovery_policy)
    lines = [
        "# Real-repository label review pack",
        "",
        "Generated from pinned source and frozen labels; this command does not run the analyzer.",
        "Labels were initially agent drafted; per-case review status is recorded below.",
        "This pack alone does not establish independent review or upstream test execution.",
        "",
        "Read [the protocol](README.md) first. Review source and uncertain labels before results.",
        "Record your name, date and review reference only after checking every label in a case.",
        "Discuss disagreements explicitly; do not relabel tests just to match recommendations.",
        "",
        "Counts are static definition IDs, not parametrized cases or inherited test executions.",
        "Affected means dependency on a changed callable/default, not expected assertion failure.",
        "An import or class construction alone does not exercise all methods.",
        "Uncertain cases remain in the denominator inventory.",
        "",
    ]
    for case in cases:
        p = provenance[case.id]
        lines += [
            f"## {case.id}",
            "",
            f"[{p.repository}]({p.change_url}) — {case.description}",
            "",
            f"Before: `{p.base.commit.sha}`; after: `{p.head.commit.sha}`.",
            "",
            f"Label status: **{p.label_review.status}**; author: {p.label_review.author}; "
            f"reviewer: {p.label_review.reviewer or 'none'}.",
            f"Frozen label SHA-256: `{p.label_review.labels_sha256}`.",
            "",
            "### Complete Python change",
            "",
            "````diff",
        ]
        lines.extend(python_diff(case))
        lines += ["````", "", "### Draft labels and source", ""]
        for label in ["expected_affected", "expected_unaffected", "unclassified"]:
            labels = getattr(case, label)
            lines += [f"#### {label} ({len(labels)})", ""]
            for sid, rationale in sorted(labels.items()):
                path, qual = sid.split("::")
                body = ast.parse(case.request.head.files[path]).body
                node = None
                for part in qual.split("."):
                    node = next(
                        n
                        for n in body
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                        and n.name == part
                    )
                    body = node.body
                url = f"https://github.com/{p.repository}/blob/{p.head.commit.sha}/{quote(path)}#L{node.lineno}-L{node.end_lineno}"
                lines += [f"- [ ] [`{sid}`]({url}) — {rationale}"]
            lines.append("")
        if outside is not None:
            entries = outside[case.id]
            lines += [f"### Outside discovery ({len(entries)})", ""]
            for sid, reason in sorted(entries.items()):
                path = sid.split("::", 1)[0]
                url = f"https://github.com/{p.repository}/blob/{p.head.commit.sha}/{quote(path)}"
                lines.append(f"- [`{sid}`]({url}) — `{reason}`")
            lines.append("")
    lines += ["## Selection exclusions", "", selection.policy, ""]
    for item in selection.exclusions:
        lines.append(
            f"- [{item.repository}@{item.revision[:12]}]"
            f"(https://github.com/{item.repository}/commit/{item.revision}): {item.reason}"
        )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("corpus/real"))
    args = parser.parse_args()
    print(review_pack(args.corpus), end="")


if __name__ == "__main__":
    main()
