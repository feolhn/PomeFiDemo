from __future__ import annotations

from pomefi.stock_wiki.aggregator import aggregate_stock_wiki_payload
from pomefi.stock_wiki.skills.timeline import get_timeline

import asyncio


def test_get_timeline_returns_price_series_when_live_fetch_succeeds(monkeypatch) -> None:
    def _fake_load_price_rows(symbol: str) -> dict[str, object]:
        _ = symbol
        return {
            "rows": [
                {"date": "2026-03-01", "close": 200.0, "event_desc": ""},
                {"date": "2026-03-05", "close": 202.0, "event_desc": ""},
            ],
            "asof": "2026-03-05",
            "data_origin": "live",
            "network_evidence": [],
            "akshare_calls": [],
            "error": None,
        }

    monkeypatch.setattr("pomefi.stock_wiki.skills.timeline._load_price_rows", _fake_load_price_rows)

    result = asyncio.run(
        get_timeline(
            "300750",
            "宁德时代",
        )
    )

    assert result["status"] == "valid"
    assert len(result["data"]["series"]) == 2
    assert result["data"]["events"] == []
    assert result["data"]["summary"] == "已抓取近三个月价格折线图；事件支路当前停用。"
    assert result["data"]["trace"]["phase_status"] == {"price_series": "valid", "events_json": "skipped"}
    assert result["data"]["trace"]["phase_error"]["events_json"] == "disabled_for_price_only"


def test_get_timeline_fails_when_price_series_unrecovered(monkeypatch) -> None:
    def _fake_load_price_rows(symbol: str) -> dict[str, object]:
        _ = symbol
        return {
            "rows": [],
            "asof": "",
            "data_origin": "partial",
            "network_evidence": [{"interface": "stock_zh_a_hist", "status": "error", "error": "proxy"}],
            "akshare_calls": [{"interface": "stock_zh_a_hist", "status": "error", "error": "proxy"}],
            "error": "price_fetch_failed: proxy",
        }

    monkeypatch.setattr("pomefi.stock_wiki.skills.timeline._load_price_rows", _fake_load_price_rows)

    result = asyncio.run(
        get_timeline(
            "300750",
            "宁德时代",
        )
    )

    assert result["status"] == "error"
    assert result["data"]["series"] == []
    assert result["data"]["events"] == []
    assert result["data"]["unrecovered_reason_code"] == "AKSHARE_NETWORK_UNRECOVERED"
    assert result["data"]["trace"]["phase_status"]["price_series"] == "error"
    assert result["data"]["trace"]["phase_status"]["events_json"] == "skipped"
    assert result["data"]["trace"]["phase_error"]["price_series"] == "price_fetch_failed: proxy"


def test_aggregate_exposes_timeline_phase_failure_evidence() -> None:
    payload = aggregate_stock_wiki_payload(
        question="宁德时代怎么看",
        symbol="300750",
        company_name="宁德时代",
        skill_results={
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
                "status": "error",
                "latency_ms": 20000,
                "data": {
                    "summary": "价格折线图抓取失败，timeline 无法生成。",
                    "series": [],
                    "events": [],
                    "trace": {
                        "phase_latency_ms": {"price_series": 122, "events_json": 0},
                        "phase_status": {"price_series": "error", "events_json": "skipped"},
                        "phase_error": {"price_series": "price_fetch_failed: proxy", "events_json": "disabled_for_price_only"},
                    },
                    "recovered": False,
                    "unrecovered_reason_code": "AKSHARE_NETWORK_UNRECOVERED",
                },
                "sources": [],
                "error": "price_fetch_failed: proxy",
                "error_category": "network",
                "data_ready": False,
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
                "is_critical": False,
            },
            "relationship": {
                "skill": "relationship",
                "status": "degraded",
                "latency_ms": 5000,
                "data": {"summary": "pending", "pending": True, "nodes": [], "edges": []},
                "sources": [],
                "error": "timeout_soft_5s",
                "error_category": "timeout",
                "data_ready": False,
                "is_critical": False,
            },
        },
    )

    evidence = payload["metadata"]["failure_evidence"]
    assert payload["metadata"]["failure_reason_code"] == "AKSHARE_NETWORK_UNRECOVERED"
    assert evidence["phase_latency_ms"] == {"price_series": 122, "events_json": 0}
    assert evidence["phase_status"] == {"price_series": "error", "events_json": "skipped"}
    assert evidence["phase_error"] == {"price_series": "price_fetch_failed: proxy", "events_json": "disabled_for_price_only"}
