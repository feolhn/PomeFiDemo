from __future__ import annotations

import asyncio
import time
from typing import Any

from pomefi.stock_wiki.aggregator import aggregate_stock_wiki_payload
from pomefi.stock_wiki.orchestrator import run_parallel_skills


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
    assert results["relationship"]["data"] == {
        "summary": "正在深度分析中...",
        "pending": True,
        "nodes": [],
        "edges": [],
    }

    payload = aggregate_stock_wiki_payload(
        question="宁德时代怎么看",
        symbol="300750",
        company_name="宁德时代",
        skill_results=results,
    )
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
    assert payload["metadata"]["partial_release"] is False
    assert payload["metadata"]["relationship_pending"] is False


def test_aggregate_marks_strict_fail_for_critical_failure() -> None:
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
    assert payload["metadata"]["strict_fail"] is True
    assert payload["metadata"]["failure_mask"]["summary"] == "price_fetch_failed"
    assert "summary" in payload["metadata"]["critical_failures"]
    assert payload["quality_status"] == "error"
