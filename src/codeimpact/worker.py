"""Trusted worker entry point; snapshots remain JSON strings and AST data."""

import json
import resource
import sys


def apply_limits(cpu_seconds: int, address_space_bytes: int) -> None:
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
    if sys.platform.startswith("linux"):
        resource.setrlimit(resource.RLIMIT_AS, (address_space_bytes, address_space_bytes))


def main() -> int:
    try:
        cpu, address_space, output_limit = (int(value) for value in sys.argv[1:])
        if not 1 <= cpu <= 60 or not 0 < address_space <= 4096 * 1024 * 1024:
            return 78
        if not 0 < output_limit <= 32 * 1024 * 1024:
            return 78
        apply_limits(cpu, address_space)
        # Apply OS limits before decoding supplied source or importing the engine.
        from codeimpact.analyzer import analyze
        from codeimpact.models import AnalysisRequest

        raw = sys.stdin.buffer.read(6_000_001)
        if len(raw) > 6_000_000:
            return 77
        request = AnalysisRequest.model_validate_json(raw)
        report = analyze(request)
        data = report.model_dump(mode="json")
        # Internal reconstruction needs fingerprints; public Report serialization
        # still excludes them and preserves the existing schema byte for byte.
        for node, serialized in zip(report.nodes, data["nodes"], strict=True):
            serialized["fingerprint"] = node.fingerprint
        encoded = json.dumps(data, separators=(",", ":")).encode("utf-8")
        if len(encoded) + 512 > output_limit:
            return 76
        usage = resource.getrusage(resource.RUSAGE_SELF)
        memory = usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024)
        metrics = json.dumps(
            {"peak_rss_bytes": memory, "cpu_ms": (usage.ru_utime + usage.ru_stime) * 1000}
        ).encode()
        sys.stdout.buffer.write(b'{"report":')
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.write(b',"usage":' + metrics + b"}")
        sys.stdout.buffer.flush()
        return 0
    except MemoryError:
        return 75
    except (ValueError, RecursionError):
        return 77
    except Exception:
        # Never serialize source-bearing exceptions or inherited environment data.
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
