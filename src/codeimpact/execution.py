"""Disposable, bounded analysis processes. Only JSON crosses the process boundary."""

import asyncio
import math
import os
import signal
import sys
import time
from dataclasses import dataclass

import psutil
from pydantic import BaseModel, ConfigDict, Field

from codeimpact.models import AnalysisRequest, Report

MIB = 1024 * 1024
MAX_INPUT = 6_000_000
MAX_OUTPUT = 32 * MIB


@dataclass(frozen=True)
class WorkerLimits:
    wall_seconds: float = 20
    cpu_seconds: int = 15
    rss_bytes: int = 256 * MIB
    address_space_bytes: int = 1024 * MIB
    output_bytes: int = MAX_OUTPUT

    def __post_init__(self) -> None:
        if not math.isfinite(self.wall_seconds) or not 0 < self.wall_seconds <= 60:
            raise ValueError("Worker wall budget must be positive and at most 60 seconds")
        for value, maximum in (
            (self.cpu_seconds, 60),
            (self.rss_bytes, 1024 * MIB),
            (self.address_space_bytes, 4096 * MIB),
            (self.output_bytes, MAX_OUTPUT),
        ):
            if type(value) is not int or not 0 < value <= maximum:
                raise ValueError("Invalid worker resource budget")


class WorkerError(Exception):
    def __init__(self, code: str, message: str, status: int = 422, retryable: bool = False):
        super().__init__(message)
        self.code, self.message, self.status, self.retryable = code, message, status, retryable

    def detail(self) -> dict[str, str | bool]:
        return {"code": self.code, "message": self.message, "retryable": self.retryable}


class WorkerUsage(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    peak_rss_bytes: int = Field(ge=0)
    cpu_ms: float = Field(ge=0)


class WorkerReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report: Report
    usage: WorkerUsage


@dataclass(frozen=True)
class Execution:
    report: Report
    wall_ms: float
    sampled_peak_rss_bytes: int
    usage: WorkerUsage


class WorkerRunner:
    """The service bounds admissions; each admitted analysis gets a fresh process.

    RSS polling is a sampled watchdog, not a hard allocation cap. Linux workers
    additionally enforce RLIMIT_AS; POSIX workers enforce CPU/core-file limits.
    """

    def __init__(self, limits: WorkerLimits | None = None) -> None:
        self.limits = limits or WorkerLimits()
        self.processes: dict[int, asyncio.subprocess.Process] = {}
        self.closed = False

    def command(self) -> list[str]:
        return [
            sys.executable,
            "-I",
            "-B",
            "-m",
            "codeimpact.worker",
            str(self.limits.cpu_seconds),
            str(self.limits.address_space_bytes),
            str(self.limits.output_bytes),
        ]

    async def close(self) -> None:
        self.closed = True
        processes = list(self.processes.values())
        for process in processes:
            self.kill(process)
        await asyncio.gather(*(process.wait() for process in processes))

    @staticmethod
    def kill(process: asyncio.subprocess.Process) -> None:
        if process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass

    async def run(self, request: AnalysisRequest) -> Execution:
        if self.closed:
            raise WorkerError(
                "unavailable", "Analysis service is stopping. Retry shortly.", 503, True
            )
        payload = request.model_dump_json().encode("utf-8")
        if len(payload) > MAX_INPUT:
            raise WorkerError("too_large", "Snapshot JSON exceeds the worker input limit.", 413)
        started = time.perf_counter()
        process: asyncio.subprocess.Process | None = None
        tasks: list[asyncio.Task[object]] = []
        peak = 0
        try:
            async with asyncio.timeout(self.limits.wall_seconds):
                # No inherited credentials, PYTHONPATH, shell or pickle transport.
                spawning = asyncio.create_task(
                    asyncio.create_subprocess_exec(
                        *self.command(),
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.DEVNULL,
                        env={"PATH": os.defpath, "LANG": "C.UTF-8"},
                        start_new_session=True,
                        limit=64 * 1024,
                    )
                )
                try:
                    process = await asyncio.shield(spawning)
                except BaseException:
                    # A cancellation during spawn must still acquire/reap the child.
                    process = await spawning
                    raise
                self.processes[process.pid] = process
                if self.closed:
                    raise WorkerError(
                        "unavailable", "Analysis service is stopping. Retry shortly.", 503, True
                    )
                child = psutil.Process(process.pid)
                assert process.stdin is not None and process.stdout is not None
                writer, reader = process.stdin, process.stdout

                async def write() -> None:
                    try:
                        writer.write(payload)
                        await writer.drain()
                    except (BrokenPipeError, ConnectionResetError):
                        pass  # exit status below supplies the safe error
                    finally:
                        writer.close()

                async def read() -> bytes:
                    output = bytearray()
                    while chunk := await reader.read(64 * 1024):
                        output.extend(chunk)
                        if len(output) > self.limits.output_bytes:
                            raise WorkerError(
                                "report_too_large",
                                "Report exceeds the output limit. Analyze a smaller change.",
                            )
                    return bytes(output)

                async def watch() -> None:
                    nonlocal peak
                    assert process is not None
                    while process.returncode is None:
                        try:
                            rss = child.memory_info().rss
                        except psutil.NoSuchProcess:
                            return
                        except psutil.Error as exc:
                            raise WorkerError(
                                "unavailable", "Worker resource monitoring is unavailable.", 503
                            ) from exc
                        peak = max(peak, rss)
                        if rss > self.limits.rss_bytes:
                            raise WorkerError(
                                "memory_limit",
                                "Analysis exceeded its memory budget. Analyze a smaller change.",
                            )
                        await asyncio.sleep(0.02)

                write_task = asyncio.create_task(write())
                read_task = asyncio.create_task(read())
                watch_task = asyncio.create_task(watch())
                tasks.extend([write_task, read_task, watch_task])
                await asyncio.gather(write_task, read_task, watch_task)
                code = await process.wait()
                if code != 0:
                    if code == 75 or code in {-signal.SIGKILL, -signal.SIGXCPU}:
                        raise WorkerError(
                            "resource_limit",
                            "Analysis exceeded a resource limit or its worker stopped. "
                            "Try a smaller change.",
                        )
                    if code == 76:
                        raise WorkerError(
                            "report_too_large",
                            "Report exceeds the output limit. Analyze a smaller change.",
                        )
                    if code == 77:
                        raise WorkerError(
                            "unsupported_source", "Unsupported or overly complex Python source."
                        )
                    raise WorkerError(
                        "worker_failed", "Analysis worker failed. Retry the request.", 503, True
                    )
                try:
                    reply = WorkerReply.model_validate_json(read_task.result())
                except ValueError as exc:
                    raise WorkerError(
                        "worker_failed", "Analysis worker returned an invalid response.", 503, True
                    ) from exc
                return Execution(
                    reply.report, (time.perf_counter() - started) * 1000, peak, reply.usage
                )
        except TimeoutError as exc:
            raise WorkerError(
                "analysis_timeout",
                "Analysis exceeded its time budget. Analyze a smaller change.",
                504,
            ) from exc
        except (OSError, psutil.Error) as exc:
            raise WorkerError(
                "unavailable", "Analysis worker could not start. Retry shortly.", 503, True
            ) from exc
        finally:
            if process is not None:
                self.kill(process)
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if process is not None:
                # A paused full stdout pipe can keep Process.wait() pending even
                # after SIGKILL. Drain bounded chunks after stopping its reader.
                if process.stdout is not None:
                    while await process.stdout.read(64 * 1024):
                        pass
                await process.wait()
                self.processes.pop(process.pid, None)
