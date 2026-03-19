from __future__ import annotations

import asyncio
import contextlib
import inspect
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from pomefi.streaming.events import EVENT_SKILL_DONE, EVENT_SKILL_RESULT_READY, EVENT_SKILL_START, make_event

SkillRunner = Callable[[str, str], Awaitable[dict[str, Any]]]

SUMMARY_SOFT_TIMEOUT_SECONDS = 12.0
ENTITY_INFO_SOFT_TIMEOUT_SECONDS = 18.0
TIMELINE_SOFT_TIMEOUT_SECONDS = 20.0
WATCH_CALENDAR_SOFT_TIMEOUT_SECONDS = 20.0
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
SKILL_TIMEOUT_SECONDS: dict[str, float] = {
    "summary": SUMMARY_SOFT_TIMEOUT_SECONDS,
    "entity_info": ENTITY_INFO_SOFT_TIMEOUT_SECONDS,
    "timeline": TIMELINE_SOFT_TIMEOUT_SECONDS,
    "watch_calendar": WATCH_CALENDAR_SOFT_TIMEOUT_SECONDS,
    "relationship": RELATIONSHIP_SOFT_TIMEOUT_SECONDS,
}
CRITICAL_SKILLS = {"timeline"}


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
        accepts_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in signature.parameters.values())
        if "event_handler" in signature.parameters or accepts_kwargs:
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
        is_critical = skill in CRITICAL_SKILLS

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
        is_critical=bool(is_critical) if isinstance(is_critical, bool) else skill in CRITICAL_SKILLS,
    )
    await emit(
        make_event(
            EVENT_SKILL_DONE,
            skill=skill,
            status=status,
            latency_ms=elapsed,
            error=error,
            data_origin=str(data.get("data_origin") or "") if isinstance(data, dict) else "",
            network_evidence=[dict(item) for item in list(data.get("network_evidence") or []) if isinstance(item, dict)]
            if isinstance(data, dict)
            else [],
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
    runtime_skill_trace: dict[str, dict[str, Any]] = {}

    def _note_skill_event(event: dict[str, Any]) -> None:
        if str(event.get("type") or "") != "skill_event":
            return
        skill = str(event.get("skill") or "")
        nested = event.get("event")
        if not skill or not isinstance(nested, dict):
            return
        if str(nested.get("type") or "") != "timeline_phase":
            return
        phase = str(nested.get("phase") or "").strip()
        if not phase:
            return
        skill_trace = runtime_skill_trace.setdefault(
            skill,
            {
                "phase_latency_ms": {},
                "phase_status": {},
                "phase_error": {},
            },
        )
        skill_trace["phase_latency_ms"][phase] = int(nested.get("latency_ms") or 0)
        skill_trace["phase_status"][phase] = str(nested.get("status") or "unknown")
        skill_trace["phase_error"][phase] = nested.get("error")

    async def emit(event: dict[str, Any]) -> None:
        _note_skill_event(event)
        await queue.put(event)

    async def _await_with_soft_timeout(
        *,
        skill: str,
        task: asyncio.Task[dict[str, Any]],
        timeout_s: float,
    ) -> dict[str, Any]:
        skill_started_ms = _now_ms()
        timeout_error = f"timeout_soft_{int(timeout_s)}s"
        timeout_data: dict[str, Any]
        if skill == "relationship":
            timeout_data = {
                **dict(RELATIONSHIP_TIMEOUT_PLACEHOLDER),
                "recovered": False,
                "unrecovered_reason_code": "KIMI_TIMEOUT_UNRECOVERED",
            }
        elif skill == "timeline":
            timeout_data = {
                "summary": "时间线生成超时，先返回其他卡片。",
                "series": [],
                "events": [],
                "recovered": False,
                "unrecovered_reason_code": "TIMELINE_TIMEOUT_UNRECOVERED",
            }
        elif skill == "watch_calendar":
            timeout_data = {
                "summary": "日历抽取超时，先返回其他卡片。",
                "items": [],
                "recovered": False,
                "unrecovered_reason_code": "KIMI_TIMEOUT_UNRECOVERED",
            }
        elif skill == "entity_info":
            timeout_data = {
                "summary": "公司主体分析超时，先返回其他卡片。",
                "recovered": False,
                "unrecovered_reason_code": "KIMI_TIMEOUT_UNRECOVERED",
            }
        else:
            timeout_data = {
                "summary": "核心行情分析超时，先返回其他卡片。",
                "metrics": {},
                "recovered": False,
                "unrecovered_reason_code": "AKSHARE_NETWORK_UNRECOVERED",
            }

        try:
            return await asyncio.wait_for(asyncio.shield(task), timeout=timeout_s)
        except asyncio.TimeoutError:
            if not task.done():
                task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
            if skill in runtime_skill_trace:
                timeout_data["trace"] = {
                    "phase_latency_ms": dict(runtime_skill_trace[skill].get("phase_latency_ms") or {}),
                    "phase_status": dict(runtime_skill_trace[skill].get("phase_status") or {}),
                    "phase_error": dict(runtime_skill_trace[skill].get("phase_error") or {}),
                }
            result = _skill_result(
                skill=skill,
                status="degraded",
                data=timeout_data,
                sources=[],
                error=timeout_error,
                latency_ms=max(int(_now_ms() - skill_started_ms), 0),
                error_category="timeout",
                data_ready=False,
                is_critical=skill in CRITICAL_SKILLS,
            )
            await emit(
                make_event(
                    EVENT_SKILL_DONE,
                    skill=skill,
                    status="degraded",
                    latency_ms=int(result.get("latency_ms") or 0),
                    error=timeout_error,
                )
            )
            return result

    async def orchestrate() -> None:
        tasks = {
            skill: asyncio.create_task(_run_skill(skill, runners[skill], symbol, company_name, emit=emit))
            for skill in ALL_SKILL_NAMES
        }
        collectors = {
            skill: asyncio.create_task(
                _await_with_soft_timeout(
                    skill=skill,
                    task=tasks[skill],
                    timeout_s=relationship_timeout_s
                    if skill == "relationship"
                    else float(SKILL_TIMEOUT_SECONDS.get(skill, 20.0)),
                )
            )
            for skill in ALL_SKILL_NAMES
        }
        collector_to_skill = {task: skill for skill, task in collectors.items()}
        pending_collectors: set[asyncio.Task[dict[str, Any]]] = set(collectors.values())
        result_map: dict[str, dict[str, Any]] = {}

        try:
            while pending_collectors:
                done_collectors, _ = await asyncio.wait(
                    pending_collectors,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for collector_task in done_collectors:
                    pending_collectors.discard(collector_task)
                    skill = collector_to_skill[collector_task]
                    try:
                        result_map[skill] = collector_task.result()
                    except asyncio.CancelledError:
                        continue
                    except Exception as exc:
                        result_map[skill] = _skill_result(
                            skill=skill,
                            status="error",
                            data={"summary": "技能执行异常。", "recovered": False, "unrecovered_reason_code": "UNKNOWN_UNRECOVERED"},
                            sources=[],
                            error=str(exc),
                            latency_ms=0,
                            error_category="unknown",
                            data_ready=False,
                            is_critical=skill in CRITICAL_SKILLS,
                        )
                    await emit(make_event(EVENT_SKILL_RESULT_READY, skill=skill, result=dict(result_map[skill])))

            for skill in ALL_SKILL_NAMES:
                if skill in result_map:
                    continue
                collector = collectors[skill]
                if collector.done() and not collector.cancelled():
                    with contextlib.suppress(Exception):
                        result_map[skill] = collector.result()
                        await emit(make_event(EVENT_SKILL_RESULT_READY, skill=skill, result=dict(result_map[skill])))
                        continue
                result_map[skill] = _skill_result(
                    skill=skill,
                    status="error",
                    data={"summary": "技能执行异常。", "recovered": False, "unrecovered_reason_code": "UNKNOWN_UNRECOVERED"},
                    sources=[],
                    error="skill_result_missing",
                    latency_ms=0,
                    error_category="unknown",
                    data_ready=False,
                    is_critical=skill in CRITICAL_SKILLS,
                )
                await emit(make_event(EVENT_SKILL_RESULT_READY, skill=skill, result=dict(result_map[skill])))

            await emit(
                make_event(
                    "orchestrator_done",
                    skill_results=result_map,
                )
            )
        except Exception as exc:
            await emit(make_event("orchestrator_error", error=str(exc)))
        finally:
            for collector in collectors.values():
                if not collector.done():
                    collector.cancel()
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
