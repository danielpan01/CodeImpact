# Milestone 6 performance measurements

Measured November 14, 2026 on macOS 26.6.2 arm64, Python 3.12.0, 15 logical CPUs and
24 GiB RAM as reported by the host. This is the local milestone 6 working tree based
on merged PR #11 (`02598a155bda061b56d03a0fcee161e13df10e89`). The
[raw receipt](../benchmarks/milestone6.json) includes all 60 samples, exact input,
engine/worker and stable-report hashes, machine metadata and resource settings.

Each of six fixed inputs gets one unmeasured warmup and ten measured **fresh worker
processes**, sequentially at concurrency one. Wall time includes process startup,
JSON transport, analysis, typed reply validation and RSS polling. Report
`stats.elapsed_ms` remains the unchanged engine-only timer. CPU time and OS peak RSS
are sampled inside the worker after report serialization; a separate parent watchdog
samples RSS through worker exit. RSS includes runtime/shared pages and is not incremental
heap or whole-service memory. P95 uses nearest rank: with ten samples it is the maximum.

| Input | Files base/head | Source bytes, both sides | Symbols / edges | Median wall ms | P95 wall ms | Max worker peak RSS MiB |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| Checkout demo | 8 / 8 | 1,230 | 16 / 20 | 86.3 | 86.4 | 34.7 |
| Cachetools LFU (v2) | 21 / 21 | 392,234 | 606 / 886 | 1,120.9 | 1,140.8 | 85.1 |
| Inflection titleize (v3) | 4 / 4 | 64,793 | 40 / 70 | 149.1 | 171.7 | 41.6 |
| PyISO8601 errors (v3) | 6 / 6 | 50,506 | 23 / 37 | 107.9 | 128.9 | 37.9 |
| Synthetic 180-function chain | 2 / 2 | 9,026 | 183 / 362 | 150.9 | 151.5 | 41.6 |
| Synthetic 200-function module | 2 / 2 | 22,935 | 402 / 401 | 151.9 | 172.8 | 44.7 |

These inputs cover a tiny demo, the larger existing fallback case, two fresh-source
cases, and generated deep/wide source shapes. They are source strings only; upstream
code/tests are never executed. Every worker result matches the direct unchanged
analyzer excluding its elapsed-time field, and every recommendation passes the
edge-by-edge evidence validator. The wide input uses a wildcard import; its zero
recommendations are the existing analyzer result, not a correctness claim.

Reproduce with `make benchmark` (writes ignored `reports/performance.json`), or:

```sh
.venv/bin/python scripts/benchmark.py --repeats 10 --output reports/performance.json
```

Run measurements without concurrent test/build workloads. The tool refuses output
under `corpus/`. Do not replace a historical receipt when rerunning; record a new
dated artifact if publishing a comparison. [Preservation hashes](../benchmarks/preservation.json)
cover all 106 historical corpus files, the 16 pre-existing engine/model/ingestion/
evaluation modules apart from the API, and the four stable evaluation reports.

The largest measured worker stayed below the default 20-second wall and 256 MiB RSS
watchdog budgets. This small fixed local sample does **not** establish production
P95, maximum input capacity, concurrent throughput, network latency, Linux memory
behavior, browser rendering speed or analyzer accuracy. No speedup is claimed:
disposable processes intentionally add startup/transport overhead to bound failures.
The existing correctness and discovery limitations remain in every evaluation.

Deployment preparation and platform caveats are in [DEPLOYMENT.md](DEPLOYMENT.md).
Resource semantics follow Python's [resource limits](https://docs.python.org/3.12/library/resource.html)
and [async subprocess lifecycle](https://docs.python.org/3.12/library/asyncio-subprocess.html).
