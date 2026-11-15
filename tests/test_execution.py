"""Process/resource failures must release capacity and retain exact analyzer reports."""

import asyncio
import json
import sys
from pathlib import Path

import psutil
import pytest

from codeimpact.analyzer import analyze
from codeimpact.demo import demo_request
from codeimpact.evaluate import validate_report
from codeimpact.execution import MIB, WorkerError, WorkerLimits, WorkerRunner
from codeimpact.models import AnalysisRequest

ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests/worker_fixture.py"


def fixture_command(monkeypatch, runner, mode):
    monkeypatch.setattr(runner, "command", lambda: [sys.executable, "-I", "-B", str(FIXTURE), mode])


def test_disposable_worker_preserves_demo_and_source_as_data(tmp_path, monkeypatch):
    sentinel = tmp_path / "executed"
    request = demo_request()
    for snapshot in (request.base, request.head):
        snapshot.files["danger.py"] = f"open({str(sentinel)!r}, 'w').write('executed')\n"
    monkeypatch.setenv("CODEIMPACT_GITHUB_TOKEN", "private-upstream-credential")
    monkeypatch.setenv("CODEIMPACT_ACCESS_KEY", "private-pilot-credential")

    async def exercise():
        runner = WorkerRunner()
        result = await runner.run(request)
        assert not runner.processes
        validate_report(request, result.report)
        assert result.report.model_dump(exclude={"stats"}) == analyze(request).model_dump(
            exclude={"stats"}
        )
        assert result.report.stats.keys() == analyze(request).stats.keys()
        assert result.wall_ms > 0 and result.usage.cpu_ms > 0
        assert result.usage.peak_rss_bytes > 0 and result.sampled_peak_rss_bytes > 0
        assert "fingerprint" not in result.report.model_dump_json()
        assert not sentinel.exists()

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "relative",
    [
        "real-v2/cases/cachetools_lfu.json",
        "real-v3/cases/inflection_title.json",
        "real-v3/cases/ordered_set_pop.json",
        "cases/deleted_function.json",
    ],
)
def test_frozen_source_and_deleted_evidence_are_exact_through_worker(relative):
    data = json.loads((ROOT / "corpus" / relative).read_text())
    request = AnalysisRequest.model_validate(data["request"])
    report = asyncio.run(WorkerRunner().run(request)).report
    expected = analyze(request)
    assert report.model_dump(exclude={"stats": {"elapsed_ms"}}) == expected.model_dump(
        exclude={"stats": {"elapsed_ms"}}
    )
    validate_report(request, report)


@pytest.mark.parametrize(
    ("mode", "limits", "code"),
    [
        ("wait", WorkerLimits(wall_seconds=0.1), "analysis_timeout"),
        ("memory", WorkerLimits(rss_bytes=32 * MIB), "memory_limit"),
        ("output", WorkerLimits(output_bytes=1024), "report_too_large"),
        ("invalid", WorkerLimits(), "worker_failed"),
        ("exit", WorkerLimits(), "worker_failed"),
        ("cpu", WorkerLimits(wall_seconds=5), "resource_limit"),
    ],
)
def test_failures_reap_child_and_allow_next_request(monkeypatch, mode, limits, code):
    async def exercise():
        runner = WorkerRunner(limits)
        original = runner.command
        fixture_command(monkeypatch, runner, mode)
        with pytest.raises(WorkerError) as failure:
            await asyncio.wait_for(runner.run(demo_request()), 8)
        assert failure.value.code == code
        assert "do not reflect" not in str(failure.value)
        assert not runner.processes
        monkeypatch.setattr(runner, "command", original)
        runner.limits = WorkerLimits()
        assert (await runner.run(demo_request())).report.recommendations

    asyncio.run(exercise())


def test_cancellation_and_shutdown_reap_workers(monkeypatch):
    async def exercise():
        runner = WorkerRunner()
        fixture_command(monkeypatch, runner, "wait")
        for close in (False, True):
            job = asyncio.create_task(runner.run(demo_request()))
            for _ in range(100):
                if runner.processes:
                    break
                await asyncio.sleep(0.01)
            assert len(runner.processes) == 1
            pid = next(iter(runner.processes))
            if close:
                await runner.close()
                with pytest.raises(WorkerError):
                    await job
            else:
                job.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await job
            assert not psutil.pid_exists(pid)
            assert not runner.processes
        with pytest.raises(WorkerError, match="stopping"):
            await runner.run(demo_request())

    asyncio.run(exercise())


def test_cancellation_during_spawn_reaps_late_child(monkeypatch):
    async def exercise():
        runner = WorkerRunner()
        fixture_command(monkeypatch, runner, "wait")
        original = asyncio.create_subprocess_exec
        spawned = asyncio.Event()
        children = []

        async def delayed(*args, **kwargs):
            process = await original(*args, **kwargs)
            children.append(process)
            spawned.set()
            await asyncio.sleep(0.05)
            return process

        monkeypatch.setattr(asyncio, "create_subprocess_exec", delayed)
        job = asyncio.create_task(runner.run(demo_request()))
        await spawned.wait()
        job.cancel()
        with pytest.raises(asyncio.CancelledError):
            await job
        assert children[0].returncode is not None
        assert not psutil.pid_exists(children[0].pid)

    asyncio.run(exercise())


def test_worker_environment_omits_credentials_and_python_injection(monkeypatch):
    async def exercise():
        runner = WorkerRunner()
        original = asyncio.create_subprocess_exec
        observed = {}

        async def capture(*args, **kwargs):
            observed.update(kwargs)
            return await original(*args, **kwargs)

        monkeypatch.setattr(asyncio, "create_subprocess_exec", capture)
        monkeypatch.setenv("CODEIMPACT_GITHUB_TOKEN", "upstream-secret")
        monkeypatch.setenv("PYTHONPATH", "/untrusted")
        await runner.run(demo_request())
        assert set(observed["env"]) == {"PATH", "LANG"}
        assert "-I" in runner.command() and "-B" in runner.command()

    asyncio.run(exercise())


def test_shutdown_during_spawn_reaps_late_child(monkeypatch):
    async def exercise():
        runner = WorkerRunner()
        fixture_command(monkeypatch, runner, "wait")
        original = asyncio.create_subprocess_exec
        spawned, release = asyncio.Event(), asyncio.Event()
        children = []

        async def delayed(*args, **kwargs):
            process = await original(*args, **kwargs)
            children.append(process)
            spawned.set()
            await release.wait()
            return process

        monkeypatch.setattr(asyncio, "create_subprocess_exec", delayed)
        job = asyncio.create_task(runner.run(demo_request()))
        await spawned.wait()
        await runner.close()
        release.set()
        with pytest.raises(WorkerError, match="stopping"):
            await asyncio.wait_for(job, 1)
        assert not runner.processes
        assert children[0].returncode is not None
        assert not psutil.pid_exists(children[0].pid)

    asyncio.run(exercise())


def test_os_spawn_failure_is_safe(monkeypatch):
    async def failed_spawn(*args, **kwargs):
        raise OSError("private operating system detail")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", failed_spawn)
    with pytest.raises(WorkerError, match="could not start"):
        asyncio.run(WorkerRunner().run(demo_request()))


def test_resource_monitor_failure_reaps_child_and_fails_closed(monkeypatch):
    runner = WorkerRunner()
    fixture_command(monkeypatch, runner, "wait")

    def denied(_self):
        raise psutil.AccessDenied()

    monkeypatch.setattr(psutil.Process, "memory_info", denied)
    with pytest.raises(WorkerError) as failure:
        asyncio.run(runner.run(demo_request()))
    assert failure.value.code == "unavailable"
    assert failure.value.status == 503
    assert not runner.processes


@pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="RLIMIT_AS enforcement is Linux-only"
)
def test_linux_address_space_limit(monkeypatch):
    runner = WorkerRunner()
    fixture_command(monkeypatch, runner, "address_space")
    with pytest.raises(WorkerError) as failure:
        asyncio.run(runner.run(demo_request()))
    assert failure.value.code == "resource_limit"
    assert not runner.processes


def test_worker_enforces_its_own_output_bound():
    with pytest.raises(WorkerError) as failure:
        asyncio.run(WorkerRunner(WorkerLimits(output_bytes=512)).run(demo_request()))
    assert failure.value.code == "report_too_large"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"wall_seconds": float("nan")},
        {"wall_seconds": 0},
        {"wall_seconds": float("inf")},
        {"cpu_seconds": 0},
        {"rss_bytes": -1},
        {"output_bytes": 0},
        {"cpu_seconds": True},
    ],
)
def test_invalid_worker_budgets_fail_early(kwargs):
    with pytest.raises(ValueError):
        WorkerLimits(**kwargs)
