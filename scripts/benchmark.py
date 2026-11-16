"""Measure fresh analysis processes on fixed JSON inputs; no upstream code is run."""

import argparse
import asyncio
import hashlib
import json
import math
import os
import platform
import statistics
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import psutil

from codeimpact.analyzer import analyze
from codeimpact.demo import demo_request
from codeimpact.evaluate import validate_report
from codeimpact.execution import WorkerRunner
from codeimpact.fresh_evaluate import CURRENT_SOURCES
from codeimpact.models import AnalysisRequest, Snapshot
from codeimpact.real_evaluate import canonical_hash, load_real

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = "02598a155bda061b56d03a0fcee161e13df10e89"


def inputs():
    cases = {"demo": demo_request()}
    for dataset, ids in (
        ("real-v2", {"cachetools_lfu"}),
        ("real-v3", {"inflection_title", "iso8601_errors"}),
    ):
        _, corpus, _, _ = load_real(ROOT / "corpus" / dataset)
        cases.update({case.id: case.request for case in corpus if case.id in ids})
    chain = "\n".join(f"def f{i}(): return f{i + 1}()" for i in range(179))
    base = {
        "chain.py": chain + "\ndef f179(): return 1\n",
        "test_chain.py": "from chain import f0\ndef test_chain(): assert f0() == 1\n",
    }
    head = base | {"chain.py": base["chain.py"].replace("return 1", "return 2")}
    cases["chain_180"] = AnalysisRequest(base=Snapshot(files=base), head=Snapshot(files=head))
    functions = "\n".join(f"def f{i}(): return {i}" for i in range(200))
    tests = "from wide import *\n" + "\n".join(
        f"def test_{i}(): assert f{i}() == {i}" for i in range(200)
    )
    base = {"wide.py": functions, "test_wide.py": tests}
    head = base | {"wide.py": functions.replace("def f0(): return 0", "def f0(): return -1")}
    cases["wide_200"] = AnalysisRequest(base=Snapshot(files=base), head=Snapshot(files=head))
    return cases


def summarize(values):
    ordered = sorted(values)
    return {
        "median": statistics.median(ordered),
        "p95": ordered[math.ceil(len(ordered) * 0.95) - 1],
        "min": ordered[0],
        "max": ordered[-1],
    }


async def measure(repeats):
    if not 3 <= repeats <= 30:
        raise ValueError("Use between 3 and 30 measured repetitions")
    runner = WorkerRunner()
    results = []
    for name, request in inputs().items():
        expected = analyze(request).model_dump(mode="json", exclude={"stats": {"elapsed_ms"}})
        expected_hash = canonical_hash(expected)
        samples = []
        for index in range(repeats + 1):
            result = await runner.run(request)
            validate_report(request, result.report)
            stable = result.report.model_dump(mode="json", exclude={"stats": {"elapsed_ms"}})
            if canonical_hash(stable) != expected_hash:
                raise ValueError(f"Worker report drift: {name}")
            if index:  # one unmeasured warmup; every repetition still starts a new process
                samples.append(
                    {
                        "wall_ms": round(result.wall_ms, 3),
                        "analysis_ms": result.report.stats["elapsed_ms"],
                        "cpu_ms": round(result.usage.cpu_ms, 3),
                        "peak_rss_bytes": result.usage.peak_rss_bytes,
                        "sampled_peak_rss_bytes": result.sampled_peak_rss_bytes,
                    }
                )
        results.append(
            {
                "case": name,
                "input_sha256": canonical_hash(request.model_dump()),
                "analysis_sha256": expected_hash,
                "files_base": len(request.base.files),
                "files_head": len(request.head.files),
                "source_bytes": sum(
                    len(s.encode())
                    for side in (request.base, request.head)
                    for s in side.files.values()
                ),
                "symbols": len(expected["nodes"]),
                "edges": len(expected["edges"]),
                "selected": len(expected["recommendations"]),
                "samples": samples,
                "summary": {
                    metric: summarize([s[metric] for s in samples]) for metric in samples[0]
                },
            }
        )
        print(name, results[-1]["summary"], flush=True)
    await runner.close()
    sources = CURRENT_SOURCES | {f"src/codeimpact/{name}.py" for name in ("execution", "worker")}
    return {
        "schema_version": "1.0",
        "recorded_at": datetime.now(UTC).isoformat(),
        "base_commit": REFERENCE,
        "implementation": "milestone 6 working tree",
        "source_sha256": {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sorted(sources)
        },
        "machine": {
            "os": platform.platform(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "logical_cpus": os.cpu_count(),
            "ram_bytes": psutil.virtual_memory().total,
        },
        "method": {
            "repetitions": repeats,
            "warmups_per_case": 1,
            "concurrency": 1,
            "worker_lifetime": "fresh process per sample",
            "p95": "nearest rank",
            "wall_scope": "spawn, JSON IPC, analysis, report validation and RSS watchdog",
            "rss": "OS per-process peak; includes runtime/shared pages, not incremental heap",
            "limitations": "Small fixed local sample; not network latency, service capacity, "
            "production p95 or analyzer accuracy.",
        },
        "worker_limits": asdict(runner.limits),
        "cases": results,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path("reports/performance.json"))
    args = parser.parse_args(argv)
    if args.output.resolve().is_relative_to((ROOT / "corpus").resolve()):
        parser.error("Benchmark output must be outside historical corpora")
    report = asyncio.run(measure(args.repeats))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=args.output.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        temporary.replace(args.output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"Measured report: {args.output}")


if __name__ == "__main__":
    main()
