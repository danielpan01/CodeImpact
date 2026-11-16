"""Explicitly refresh rendered-UI fixtures; upstream source is only parsed as data."""

import hashlib
import json
from pathlib import Path

from codeimpact.analyzer import analyze
from codeimpact.demo import demo_request
from codeimpact.models import AnalysisRequest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "web/tests/quality/fixtures"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    inputs = {
        "mixed": "tests/fixtures/mixed-revisions.json",
        "large": "corpus/real-v2/cases/cachetools_lfu.json",
        "unsupported-discovery": "tests/fixtures/unsupported-discovery.json",
    }
    requests = {"demo": demo_request()}
    provenance = {"demo": "src/codeimpact/demo.py"}
    for name, path in inputs.items():
        data = json.loads((ROOT / path).read_text())
        requests[name] = AnalysisRequest.model_validate(data.get("request", data))
        provenance[name] = path
    # Retain archived fixture receipts (including 8C's original zero-discovery
    # report); refreshed current fixtures are reviewed separately.
    manifest_path = OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for name, request in requests.items():
        report = analyze(request).model_dump(mode="json")
        # The only variable display field. No counts, source, warnings or evidence
        # are omitted, rewritten or masked. This is a UI fixture, not a benchmark.
        report["stats"]["elapsed_ms"] = 12.5
        content = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        (OUTPUT / f"{name}.json").write_text(content)
        source = provenance[name]
        manifest[name] = {
            "input": source,
            "input_sha256": hashlib.sha256((ROOT / source).read_bytes()).hexdigest(),
            "report_sha256": hashlib.sha256(content.encode()).hexdigest(),
            "recommendations": len(report["recommendations"]),
            "warnings": len(report["warnings"]),
        }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {len(requests)} complete UI reports. Review fixtures and baselines separately.")


if __name__ == "__main__":
    main()
