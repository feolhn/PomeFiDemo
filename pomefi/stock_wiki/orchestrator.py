from __future__ import annotations

import asyncio
import contextlib
import inspect
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from pomefi.streaming.events import EVENT_SKILL_DONE, EVENT_SKILL_START, make_event

SkillRunner = Callable[[str, str], Awaitable[dict[str, Any]]]

RELATIONSHIP_SOFT_TIMEOUT_SECONDS = 5.0
RELATIONSHIP_TIMEOUT_PLACEHOLDER = {
    "summary": "正在深度分析中...",
    "pending": True,
    "nodes": [],
    "edges": [],
}

CORE_SKILL_NAMES = (
    "summary",
    "entity_info",
    "timeline",
    "watch_calendar",
)
ALL_SKILL_NAMES = CORE_SKILL_NAMES + ("relationship",)


def _now_ms() -> float:
    return time.perf_counter() * 1000.0


def _skill_result(
    *,
    skill: str,
    status: str,
    data: dict[str, Any] | None,
    sources: list[dict[str, Any]] | None,
    error: str | None,
    latency_ms: int,
    error_category: str | None = None,
    data_ready: bool | None = None,
    is_critical: bool | None = None,
) -> dict[str, Any]:
    return {
        "skill": skill,
        "status": status,
        "latency_ms": latency_ms,
        "data": dict(data or {}),
        "sources": list(sources or []),
        "error": error,
        "error_category": error_category,
        "data_ready": data_ready,
        "is_critical": bool(is_critical) if is_critical is not None else False,
    }


async def _invoke_runner(
    runner: SkillRunner,
    symbol: str,
    company_name: str,
    *,
    event_handler: Callable[[dict[str, Any]], Awaitable[None]],
) -> dict[str, Any]:
    try:
        signature = inspect.signature(runner)
        if "event_handler" in signature.parameters:
            result = runner(symbol, company_name, event_handler=event_handler)
        else:
            result = runner(symbol, company_name)
    except (TypeError, ValueError):
        result = runner(symbol, company_name)
    if inspect.isawaitable(result):
        return await result
    return dict(result)


async def _run_skill(
    skill: str,
    runner: SkillRunner,
    symbol: str,
    company_name: str,
    *,
    emit: Callable[[dict[str, Any]], Awaitable[None]],
) -> dict[str, Any]:
    started_ms = _now_ms()
    await emit(make_event(EVENT_SKILL_START, skill=skill))

    async def _skill_event_handler(event: dict[str, Any]) -> None:
        await emit(make_event("skill_event", skill=skill, event=event))

    try:
        payload = await _invoke_runner(
            runner,
            symbol,
            company_name,
            event_handler=_skill_event_handler,
        )
        status = str(payload.get("status") or "valid")
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        sources = payload.get("sources") if isinstance(payload.get("sources"), list) else []
        error = str(payload.get("error") or "") or None
        error_category = str(payload.get("error_category") or "") or None
        data_ready = payload.get("data_ready")
        is_critical = payload.get("is_critical")
    except Exception as exc:
        status = "error"
        data = {}
        sources = []
        error = str(exc)
        error_category = "unknown"
        data_ready = False
        is_critical = False

    elapsed = max(int(_now_ms() - started_ms), 0)
    result = _skill_result(
        skill=skill,
        status=status,
        data=data,
        sources=sources,
        error=error,
        latency_ms=elapsed,
        error_category=error_category,
        data_ready=data_ready if isinstance(data_ready, bool) else None,
        is_critical=bool(is_critical) if isinstance(is_critical, bool) else False,
    )
    await emit(
        make_event(
            EVENT_SKILL_DONE,
            skill=skill,
            status=status,
            latency_ms=elapsed,
            error=error,
        )
    )
    return result


async def run_parallel_skills_stream(
    *,
    symbol: str,
    company_name: str,
    runners: dict[str, SkillRunner],
    relationship_timeout_s: float = RELATIONSHIP_SOFT_TIMEOUT_SECONDS,
) -> AsyncIterator[dict[str, Any]]:
    for skill in ALL_SKILL_NAMES:
        if skill not in runners:
            raise RuntimeError(f"Missing skill runner: {skill}")

    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def emit(event: dict[str, Any]) -> None:
        await queue.put(event)

    async def orchestrate() -> None:
        run_started_ms = _now_ms()
        tasks = {
            skill: asyncio.create_task(_run_skill(skill, runners[skill], symbol, company_name, emit=emit))
            for skill in ALL_SKILL_NAMES
        }
        try:
            core_results_list = await asyncio.gather(*(tasks[name] for name in CORE_SKILL_NAMES))
            core_results = {item["skill"]: item for item in core_results_list}

            relationship_task = tasks["relationship"]
            if relationship_task.done():
                relationship_result = relationship_task.result()
            else:
                elapsed_since_start_s = max((_now_ms() - run_started_ms) / 1000.0, 0.0)
                remaining_s = relationship_timeout_s - elapsed_since_start_s
                relationship_started_ms = _now_ms()
                if remaining_s <= 0:
                    relationship_result = _skill_result(
                        skill="relationship",
                        status="degraded",
                        data=dict(RELATIONSHIP_TIMEOUT_PLACEHOLDER),
                        sources=[],
                        error="timeout_soft_5s",
                        latency_ms=max(int(_now_ms() - relationship_started_ms), 0),
                        error_category="timeout",
                        data_ready=False,
                        is_critical=False,
                    )
                else:
                    try:
                        relationship_result = await asyncio.wait_for(
                            asyncio.shield(relationship_task),
                            timeout=remaining_s,
                        )
                    except asyncio.TimeoutError:
                        relationship_result = _skill_result(
                            skill="relationship",
                            status="degraded",
                            data=dict(RELATIONSHIP_TIMEOUT_PLACEHOLDER),
                            sources=[],
                            error="timeout_soft_5s",
                            latency_ms=max(int(_now_ms() - relationship_started_ms), 0),
                            error_category="timeout",
                            data_ready=False,
                            is_critical=False,
                        )
            if relationship_result.get("error") == "timeout_soft_5s":
                await emit(
                    make_event(
                        EVENT_SKILL_DONE,
                        skill="relationship",
                        status="degraded",
                        latency_ms=int(relationship_result.get("latency_ms") or 0),
                        error="timeout_soft_5s",
                    )
                )
            result_map = {**core_results, "relationship": relationship_result}
            await emit(make_event("orchestrator_done", skill_results=result_map))
        except Exception as exc:
            await emit(make_event("orchestrator_error", error=str(exc)))
        finally:
            relationship_task = tasks.get("relationship")
            if relationship_task is not None and not relationship_task.done():
                relationship_task.cancel()
            for task in tasks.values():
                if not task.done():
                    task.cancel()

    orchestrator_task = asyncio.create_task(orchestrate())
    try:
        while True:
            if orchestrator_task.done() and queue.empty():
                break
            event = await queue.get()
            yield event
    finally:
        if not orchestrator_task.done():
            orchestrator_task.cancel()
        with contextlib.suppress(Exception):
            await orchestrator_task


async def run_parallel_skills(
    *,
    symbol: str,
    company_name: str,
    runners: dict[str, SkillRunner],
    relationship_timeout_s: float = RELATIONSHIP_SOFT_TIMEOUT_SECONDS,
) -> dict[str, dict[str, Any]]:
    skill_results: dict[str, dict[str, Any]] | None = None
    async for event in run_parallel_skills_stream(
        symbol=symbol,
        company_name=company_name,
        runners=runners,
        relationship_timeout_s=relationship_timeout_s,
    ):
        if event.get("type") == "orchestrator_done":
            maybe_results = event.get("skill_results")
            if isinstance(maybe_results, dict):
                skill_results = maybe_results
        if event.get("type") == "orchestrator_error":
            raise RuntimeError(str(event.get("error") or "orchestrator_error"))
    if skill_results is None:
        raise RuntimeError("orchestrator_done_missing")
    return skill_results
