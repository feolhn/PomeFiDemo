from __future__ import annotations

import asyncio
import time
from typing import Any

from pomefi.stock_wiki.aggregator import aggregate_stock_wiki_payload
from pomefi.stock_wiki.orchestrator import run_parallel_skills, run_parallel_skills_stream


def _valid_runner(skill: str):
    async def _runner(symbol: str, company_name: str) -> dict[str, Any]:
        await asyncio.sleep(0.02)
        return {
            "status": "valid",
            "data": {"summary": f"{skill}:{symbol}:{company_name}"},
            "sources": [{"source": skill}],
            "error": None,
        }

    return _runner


async def _slow_relationship(_symbol: str, _company_name: str) -> dict[str, Any]:
    await asyncio.sleep(6.0)
    return {
        "status": "valid",
        "data": {"summary": "done", "pending": False, "nodes": [{"id": "CATL"}], "edges": []},
        "sources": [{"source": "relationship"}],
        "error": None,
    }


def test_relationship_soft_timeout_partial_release() -> None:
    runners = {
        "summary": _valid_runner("summary"),
        "entity_info": _valid_runner("entity_info"),
        "timeline": _valid_runner("timeline"),
        "watch_calendar": _valid_runner("watch_calendar"),
        "relationship": _slow_relationship,
    }

    started = time.perf_counter()
    results = asyncio.run(
        run_parallel_skills(
            symbol="300750",
            company_name="宁德时代",
            runners=runners,
        )
    )
    elapsed = time.perf_counter() - started

    assert elapsed < 5.8
    assert all(results[name]["status"] == "valid" for name in ("summary", "entity_info", "timeline", "watch_calendar"))
    assert results["relationship"]["status"] == "degraded"
    assert results["relationship"]["error"] == "timeout_soft_5s"
    assert results["relationship"]["data"]["summary"] == "正在深度分析中..."
    assert results["relationship"]["data"]["pending"] is True
    assert results["relationship"]["data"]["nodes"] == []
    assert results["relationship"]["data"]["edges"] == []

    payload = aggregate_stock_wiki_payload(
        question="宁德时代怎么看",
        symbol="300750",
        company_name="宁德时代",
        skill_results=results,
    )
    assert payload["metadata"]["execution_status"] == "success"
    assert payload["quality_status"] == "valid"
    assert payload["metadata"]["partial_release"] is True
    assert payload["metadata"]["relationship_pending"] is True


def test_relationship_finishes_within_timeout_no_placeholder() -> None:
    async def _fast_relationship(symbol: str, company_name: str) -> dict[str, Any]:
        await asyncio.sleep(0.03)
        return {
            "status": "valid",
            "data": {"summary": f"relationship:{symbol}:{company_name}", "pending": False, "nodes": [{"id": "CATL"}], "edges": []},
            "sources": [{"source": "relationship"}],
            "error": None,
        }

    runners = {
        "summary": _valid_runner("summary"),
        "entity_info": _valid_runner("entity_info"),
        "timeline": _valid_runner("timeline"),
        "watch_calendar": _valid_runner("watch_calendar"),
        "relationship": _fast_relationship,
    }

    results = asyncio.run(
        run_parallel_skills(
            symbol="300750",
            company_name="宁德时代",
            runners=runners,
            relationship_timeout_s=1.0,
        )
    )

    assert results["relationship"]["status"] == "valid"
    assert results["relationship"]["error"] is None
    assert results["relationship"]["data"]["pending"] is False

    payload = aggregate_stock_wiki_payload(
        question="宁德时代怎么看",
        symbol="300750",
        company_name="宁德时代",
        skill_results=results,
    )
    assert payload["metadata"]["execution_status"] == "success"
    assert payload["quality_status"] == "valid"
    assert payload["metadata"]["partial_release"] is False
    assert payload["metadata"]["relationship_pending"] is False


def test_timeline_timeout_does_not_block_all() -> None:
    async def _slow_timeline(_symbol: str, _company_name: str) -> dict[str, Any]:
        await asyncio.sleep(30.0)
        return {
            "status": "valid",
            "data": {"summary": "done", "series": [{"date": "2026-03-01", "close": 1.0}], "events": []},
            "sources": [],
            "error": None,
            "is_critical": True,
            "data_ready": True,
        }

    runners = {
        "summary": _valid_runner("summary"),
        "entity_info": _valid_runner("entity_info"),
        "timeline": _slow_timeline,
        "watch_calendar": _valid_runner("watch_calendar"),
        "relationship": _valid_runner("relationship"),
    }
    started = time.perf_counter()
    results = asyncio.run(
        run_parallel_skills(
            symbol="300750",
            company_name="宁德时代",
            runners=runners,
        )
    )
    elapsed = time.perf_counter() - started
    assert elapsed < 21.5
    assert results["timeline"]["status"] == "degraded"
    assert results["timeline"]["error"] == "timeout_soft_20s"
    payload = aggregate_stock_wiki_payload(
        question="宁德时代怎么看",
        symbol="300750",
        company_name="宁德时代",
        skill_results=results,
    )
    assert payload["metadata"]["execution_status"] == "failed"
    assert payload["metadata"]["failure_reason_code"] == "TIMELINE_TIMEOUT_UNRECOVERED"
    assert payload["metadata"]["failure_stage"] == "timeline"
    assert payload["quality_status"] == "error"


def test_timeline_timeout_preserves_phase_trace() -> None:
    async def _timeline_with_phase(_symbol: str, _company_name: str, event_handler=None) -> dict[str, Any]:
        if event_handler is not None:
            await event_handler(
                {
                    "type": "timeline_phase",
                    "phase": "price_series",
                    "status": "valid",
                    "latency_ms": 123,
                    "error": None,
                }
            )
            await event_handler(
                {
                    "type": "timeline_phase",
                    "phase": "events_json",
                    "status": "running",
                    "latency_ms": 456,
                    "error": None,
                }
            )
        await asyncio.sleep(30.0)
        return {
            "status": "valid",
            "data": {"summary": "done", "series": [{"date": "2026-03-01", "close": 1.0}], "events": [{"date": "2026-03-01", "title": "x"}]},
            "sources": [],
            "error": None,
            "is_critical": True,
            "data_ready": True,
        }

    runners = {
        "summary": _valid_runner("summary"),
        "entity_info": _valid_runner("entity_info"),
        "timeline": _timeline_with_phase,
        "watch_calendar": _valid_runner("watch_calendar"),
        "relationship": _valid_runner("relationship"),
    }
    results = asyncio.run(
        run_parallel_skills(
            symbol="300750",
            company_name="宁德时代",
            runners=runners,
        )
    )
    trace = results["timeline"]["data"]["trace"]
    assert results["timeline"]["status"] == "degraded"
    assert trace["phase_latency_ms"] == {"price_series": 123, "events_json": 456}
    assert trace["phase_status"] == {"price_series": "valid", "events_json": "running"}
    assert trace["phase_error"] == {"price_series": None, "events_json": None}


def test_timeout_window_is_per_skill_not_global_elapsed() -> None:
    async def _slow_summary(_symbol: str, _company_name: str) -> dict[str, Any]:
        await asyncio.sleep(15.0)
        return {
            "status": "valid",
            "data": {"summary": "summary done"},
            "sources": [],
            "error": None,
            "data_ready": True,
            "is_critical": True,
        }

    async def _medium_timeline(_symbol: str, _company_name: str) -> dict[str, Any]:
        await asyncio.sleep(10.0)
        return {
            "status": "valid",
            "data": {"summary": "timeline done", "series": [{"date": "2026-03-01", "close": 1.0}], "events": []},
            "sources": [],
            "error": None,
            "data_ready": True,
            "is_critical": True,
        }

    async def _fast_relationship(_symbol: str, _company_name: str) -> dict[str, Any]:
        await asyncio.sleep(1.0)
        return {
            "status": "valid",
            "data": {"summary": "relationship done", "pending": False, "nodes": [{"id": "CATL"}], "edges": []},
            "sources": [],
            "error": None,
            "data_ready": True,
            "is_critical": False,
        }

    runners = {
        "summary": _slow_summary,
        "entity_info": _valid_runner("entity_info"),
        "timeline": _medium_timeline,
        "watch_calendar": _valid_runner("watch_calendar"),
        "relationship": _fast_relationship,
    }
    started = time.perf_counter()
    results = asyncio.run(
        run_parallel_skills(
            symbol="300750",
            company_name="宁德时代",
            runners=runners,
        )
    )
    elapsed = time.perf_counter() - started
    assert elapsed < 16.5
    assert results["summary"]["status"] == "degraded"
    assert results["summary"]["error"] == "timeout_soft_12s"
    assert results["timeline"]["status"] == "valid"
    assert results["relationship"]["status"] == "valid"


def test_aggregate_summary_failure_is_noncritical_when_timeline_valid() -> None:
    skill_results = {
        "summary": {
            "skill": "summary",
            "status": "error",
            "latency_ms": 10,
            "data": {"summary": "失败"},
            "sources": [],
            "error": "price_fetch_failed",
            "error_category": "network",
            "data_ready": False,
            "is_critical": True,
        },
        "entity_info": {
            "skill": "entity_info",
            "status": "valid",
            "latency_ms": 10,
            "data": {"summary": "ok"},
            "sources": [],
            "error": None,
            "error_category": None,
            "data_ready": True,
            "is_critical": False,
        },
        "timeline": {
            "skill": "timeline",
            "status": "valid",
            "latency_ms": 10,
            "data": {"summary": "ok"},
            "sources": [],
            "error": None,
            "error_category": None,
            "data_ready": True,
            "is_critical": True,
        },
        "watch_calendar": {
            "skill": "watch_calendar",
            "status": "valid",
            "latency_ms": 10,
            "data": {"summary": "ok"},
            "sources": [],
            "error": None,
            "error_category": None,
            "data_ready": True,
            "is_critical": True,
        },
        "relationship": {
            "skill": "relationship",
            "status": "degraded",
            "latency_ms": 10,
            "data": {"summary": "pending", "pending": False, "nodes": [], "edges": []},
            "sources": [],
            "error": "relationship_no_tool_calls",
            "error_category": "tool",
            "data_ready": False,
            "is_critical": False,
        },
    }

    payload = aggregate_stock_wiki_payload(
        question="宁德时代怎么看",
        symbol="300750",
        company_name="宁德时代",
        skill_results=skill_results,
    )
    assert payload["metadata"]["strict_fail"] is False
    assert payload["metadata"]["failure_mask"] == {}
    assert payload["metadata"]["critical_failures"] == []
    assert payload["metadata"]["execution_status"] == "success"
    assert payload["metadata"]["failure_reason_code"] is None
    assert payload["metadata"]["failure_stage"] is None
    assert payload["quality_status"] == "valid"


def test_calendar_empty_not_strict_fail_when_noncritical() -> None:
    skill_results = {
        "summary": {
            "skill": "summary",
            "status": "valid",
            "latency_ms": 10,
            "data": {"summary": "ok"},
            "sources": [],
            "error": None,
            "error_category": None,
            "data_ready": True,
            "is_critical": True,
        },
        "entity_info": {
            "skill": "entity_info",
            "status": "valid",
            "latency_ms": 10,
            "data": {"summary": "ok"},
            "sources": [],
            "error": None,
            "error_category": None,
            "data_ready": True,
            "is_critical": False,
        },
        "timeline": {
            "skill": "timeline",
            "status": "valid",
            "latency_ms": 10,
            "data": {"summary": "ok"},
            "sources": [],
            "error": None,
            "error_category": None,
            "data_ready": True,
            "is_critical": True,
        },
        "watch_calendar": {
            "skill": "watch_calendar",
            "status": "degraded",
            "latency_ms": 10,
            "data": {"summary": "暂无节点", "items": []},
            "sources": [],
            "error": "calendar_empty",
            "error_category": "empty",
            "data_ready": False,
            "is_critical": False,
        },
        "relationship": {
            "skill": "relationship",
            "status": "degraded",
            "latency_ms": 10,
            "data": {"summary": "pending", "pending": False, "nodes": [], "edges": []},
            "sources": [],
            "error": "relationship_no_tool_calls",
            "error_category": "tool",
            "data_ready": False,
            "is_critical": False,
        },
    }
    payload = aggregate_stock_wiki_payload(
        question="宁德时代怎么看",
        symbol="300750",
        company_name="宁德时代",
        skill_results=skill_results,
    )
    assert payload["metadata"]["strict_fail"] is False
    assert "watch_calendar" not in payload["metadata"]["failure_mask"]
    assert payload["metadata"]["execution_status"] == "success"
    assert payload["quality_status"] == "valid"


def test_summary_failure_does_not_short_circuit_when_timeline_is_only_critical() -> None:
    async def _summary_fail(_symbol: str, _company_name: str) -> dict[str, Any]:
        await asyncio.sleep(0.1)
        return {
            "status": "error",
            "data": {
                "summary": "核心行情失败",
                "recovered": False,
                "unrecovered_reason_code": "AKSHARE_NETWORK_UNRECOVERED",
            },
            "sources": [],
            "error": "network_live_failed_cache_miss",
            "error_category": "network",
            "data_ready": False,
            "is_critical": True,
        }

    async def _timeline_fast(_symbol: str, _company_name: str) -> dict[str, Any]:
        await asyncio.sleep(0.05)
        return {
            "status": "valid",
            "data": {"summary": "timeline ok", "series": [{"date": "2026-03-01", "close": 1.0}], "events": []},
            "sources": [],
            "error": None,
            "data_ready": True,
            "is_critical": True,
        }

    async def _fast_noncritical(_symbol: str, _company_name: str) -> dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"status": "valid", "data": {"summary": "ok"}, "sources": [], "error": None, "data_ready": True}

    runners = {
        "summary": _summary_fail,
        "entity_info": _fast_noncritical,
        "timeline": _timeline_fast,
        "watch_calendar": _fast_noncritical,
        "relationship": _fast_noncritical,
    }

    async def _collect() -> tuple[dict[str, Any], list[dict[str, Any]], float]:
        events: list[dict[str, Any]] = []
        done_event: dict[str, Any] | None = None
        started = time.perf_counter()
        async for event in run_parallel_skills_stream(symbol="300750", company_name="宁德时代", runners=runners):
            events.append(event)
            if event.get("type") == "orchestrator_done":
                done_event = event
        elapsed = time.perf_counter() - started
        assert done_event is not None
        return done_event, events, elapsed

    done_event, events, elapsed = asyncio.run(_collect())
    assert elapsed < 1.5
    assert not any(event.get("type") == "orchestrator_short_circuit" for event in events)
    skill_results = dict(done_event.get("skill_results") or {})
    assert skill_results["summary"]["status"] == "error"
    assert skill_results["timeline"]["status"] == "valid"
    assert skill_results["entity_info"]["status"] == "valid"
    assert skill_results["watch_calendar"]["status"] == "valid"
    assert skill_results["relationship"]["status"] == "valid"
    assert done_event.get("short_circuit") is False
    assert done_event.get("cancelled_skills") == []

    payload = aggregate_stock_wiki_payload(
        question="宁德时代怎么看",
        symbol="300750",
        company_name="宁德时代",
        skill_results=skill_results,
        short_circuit=bool(done_event.get("short_circuit")),
        cancelled_skills=list(done_event.get("cancelled_skills") or []),
    )
    assert payload["metadata"]["execution_status"] == "success"
    assert payload["metadata"]["failure_reason_code"] is None
    assert payload["metadata"]["short_circuit"] is False
    assert payload["metadata"]["cancelled_skills"] == []


def test_runner_with_kwargs_receives_event_handler_for_timeline_phase() -> None:
    async def _timeline_runner(_symbol: str, _company_name: str, **kwargs) -> dict[str, Any]:
        event_handler = kwargs.get("event_handler")
        assert event_handler is not None
        await event_handler(
            {
                "type": "timeline_phase",
                "phase": "price_series",
                "status": "valid",
                "latency_ms": 12,
                "error": None,
            }
        )
        await asyncio.sleep(30.0)
        return {
            "status": "valid",
            "data": {"summary": "done", "series": [{"date": "2026-03-01", "close": 1.0}], "events": [{"date": "2026-03-01", "title": "x"}]},
            "sources": [],
            "error": None,
            "is_critical": True,
            "data_ready": True,
        }

    runners = {
        "summary": _valid_runner("summary"),
        "entity_info": _valid_runner("entity_info"),
        "timeline": _timeline_runner,
        "watch_calendar": _valid_runner("watch_calendar"),
        "relationship": _valid_runner("relationship"),
    }
    results = asyncio.run(
        run_parallel_skills(
            symbol="300750",
            company_name="宁德时代",
            runners=runners,
        )
    )
    trace = results["timeline"]["data"]["trace"]
    assert trace["phase_latency_ms"] == {"price_series": 12}
    assert trace["phase_status"] == {"price_series": "valid"}


def test_short_circuit_when_timeline_fails_cancels_noncritical() -> None:
    async def _summary_fast(_symbol: str, _company_name: str) -> dict[str, Any]:
        await asyncio.sleep(0.05)
        return {
            "status": "valid",
            "data": {"summary": "summary ok", "metrics": {"price_last": 1.0}},
            "sources": [],
            "error": None,
            "data_ready": True,
            "is_critical": True,
        }

    async def _timeline_fail(_symbol: str, _company_name: str) -> dict[str, Any]:
        await asyncio.sleep(0.1)
        return {
            "status": "error",
            "data": {
                "summary": "timeline timeout",
                "series": [],
                "events": [],
                "recovered": False,
                "unrecovered_reason_code": "TIMELINE_TIMEOUT_UNRECOVERED",
            },
            "sources": [],
            "error": "timeout_soft_20s",
            "error_category": "timeout",
            "data_ready": False,
            "is_critical": True,
        }

    async def _slow_noncritical(_symbol: str, _company_name: str) -> dict[str, Any]:
        await asyncio.sleep(20.0)
        return {"status": "valid", "data": {"summary": "slow ok"}, "sources": [], "error": None, "data_ready": True}

    runners = {
        "summary": _summary_fast,
        "entity_info": _slow_noncritical,
        "timeline": _timeline_fail,
        "watch_calendar": _slow_noncritical,
        "relationship": _slow_noncritical,
    }

    async def _collect() -> tuple[dict[str, Any], list[dict[str, Any]], float]:
        events: list[dict[str, Any]] = []
        done_event: dict[str, Any] | None = None
        started = time.perf_counter()
        async for event in run_parallel_skills_stream(symbol="300750", company_name="宁德时代", runners=runners):
            events.append(event)
            if event.get("type") == "orchestrator_done":
                done_event = event
        elapsed = time.perf_counter() - started
        assert done_event is not None
        return done_event, events, elapsed

    done_event, events, elapsed = asyncio.run(_collect())
    assert elapsed < 2.5
    assert any(event.get("type") == "orchestrator_short_circuit" for event in events)
    skill_results = dict(done_event.get("skill_results") or {})
    assert skill_results["timeline"]["status"] == "error"
    assert skill_results["entity_info"]["error"] == "cancelled_due_to_critical_failure"
    assert skill_results["watch_calendar"]["error"] == "cancelled_due_to_critical_failure"
    assert skill_results["relationship"]["error"] == "cancelled_due_to_critical_failure"
    assert done_event.get("short_circuit") is True
    cancelled = set(done_event.get("cancelled_skills") or [])
    assert {"entity_info", "watch_calendar", "relationship"}.issubset(cancelled)

    payload = aggregate_stock_wiki_payload(
        question="宁德时代怎么看",
        symbol="300750",
        company_name="宁德时代",
        skill_results=skill_results,
        short_circuit=bool(done_event.get("short_circuit")),
        cancelled_skills=list(done_event.get("cancelled_skills") or []),
    )
    assert payload["metadata"]["execution_status"] == "failed"
    assert payload["metadata"]["failure_reason_code"] == "TIMELINE_TIMEOUT_UNRECOVERED"
    assert payload["metadata"]["short_circuit"] is True
    assert set(payload["metadata"]["cancelled_skills"]) >= {"entity_info", "watch_calendar", "relationship"}


def test_execution_success_when_noncritical_skill_errors() -> None:
    skill_results = {
        "summary": {
            "skill": "summary",
            "status": "valid",
            "latency_ms": 12,
            "data": {"summary": "summary ok", "data_origin": "live", "metrics": {"price_last": 100.0}},
            "sources": [],
            "error": None,
            "error_category": None,
            "data_ready": True,
            "is_critical": True,
        },
        "entity_info": {
            "skill": "entity_info",
            "status": "error",
            "latency_ms": 20,
            "data": {"summary": "entity info failed"},
            "sources": [],
            "error": "stock_individual_info_em failed",
            "error_category": "network",
            "data_ready": False,
            "is_critical": False,
        },
        "timeline": {
            "skill": "timeline",
            "status": "valid",
            "latency_ms": 15,
            "data": {"summary": "timeline ok", "data_origin": "live", "series": [{"date": "2026-03-01", "close": 1.0}], "events": []},
            "sources": [],
            "error": None,
            "error_category": None,
            "data_ready": True,
            "is_critical": True,
        },
        "watch_calendar": {
            "skill": "watch_calendar",
            "status": "degraded",
            "latency_ms": 10,
            "data": {"summary": "calendar empty", "items": []},
            "sources": [],
            "error": "calendar_empty",
            "error_category": "empty",
            "data_ready": False,
            "is_critical": False,
        },
        "relationship": {
            "skill": "relationship",
            "status": "degraded",
            "latency_ms": 8,
            "data": {"summary": "pending", "pending": True, "nodes": [], "edges": []},
            "sources": [],
            "error": "timeout_soft_5s",
            "error_category": "timeout",
            "data_ready": False,
            "is_critical": False,
        },
    }

    payload = aggregate_stock_wiki_payload(
        question="宁德时代怎么看",
        symbol="300750",
        company_name="宁德时代",
        skill_results=skill_results,
    )
    assert payload["metadata"]["execution_status"] == "success"
    assert payload["quality_status"] == "valid"
    assert payload["metadata"]["failure_reason_code"] is None
