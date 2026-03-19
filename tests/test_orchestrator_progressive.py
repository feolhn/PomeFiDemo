from __future__ import annotations

import asyncio
from typing import Any

from pomefi.stock_wiki.orchestrator import run_parallel_skills_stream


def _runner(skill: str, delay: float, status: str = "valid"):
    async def _impl(_symbol: str, _company_name: str) -> dict[str, Any]:
        await asyncio.sleep(delay)
        return {
            "skill": skill,
            "status": status,
            "latency_ms": int(delay * 1000),
            "data": {"summary": f"{skill}:{status}"},
            "sources": [],
            "error": None if status == "valid" else f"{skill}_failed",
            "error_category": None if status == "valid" else "unknown",
            "data_ready": status == "valid",
            "is_critical": skill == "timeline",
        }

    return _impl


def test_skill_result_ready_emits_before_orchestrator_done() -> None:
    runners = {
        "summary": _runner("summary", 0.01),
        "entity_info": _runner("entity_info", 0.03),
        "timeline": _runner("timeline", 0.02),
        "watch_calendar": _runner("watch_calendar", 0.04),
        "relationship": _runner("relationship", 0.05),
    }

    async def _collect() -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        async for event in run_parallel_skills_stream(symbol="300750", company_name="宁德时代", runners=runners):
            events.append(event)
        return events

    events = asyncio.run(_collect())
    ready_indexes = [index for index, event in enumerate(events) if event.get("type") == "skill_result_ready"]
    done_indexes = [index for index, event in enumerate(events) if event.get("type") == "orchestrator_done"]
    assert ready_indexes
    assert done_indexes
    assert max(ready_indexes) < done_indexes[0]


def test_timeline_failure_does_not_cancel_other_skills() -> None:
    runners = {
        "summary": _runner("summary", 0.01),
        "entity_info": _runner("entity_info", 0.03),
        "timeline": _runner("timeline", 0.02, status="error"),
        "watch_calendar": _runner("watch_calendar", 0.04),
        "relationship": _runner("relationship", 0.05),
    }

    async def _collect() -> tuple[list[dict[str, Any]], dict[str, Any]]:
        events: list[dict[str, Any]] = []
        done_event: dict[str, Any] | None = None
        async for event in run_parallel_skills_stream(symbol="300750", company_name="宁德时代", runners=runners):
            events.append(event)
            if event.get("type") == "orchestrator_done":
                done_event = event
        assert done_event is not None
        return events, done_event

    events, done_event = asyncio.run(_collect())
    assert not any(event.get("type") == "orchestrator_short_circuit" for event in events)
    skill_results = dict(done_event.get("skill_results") or {})
    assert skill_results["timeline"]["status"] == "error"
    assert skill_results["summary"]["status"] == "valid"
    assert skill_results["entity_info"]["status"] == "valid"
    assert skill_results["watch_calendar"]["status"] == "valid"
    assert skill_results["relationship"]["status"] == "valid"
