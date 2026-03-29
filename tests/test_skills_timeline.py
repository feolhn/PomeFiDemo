from __future__ import annotations

from datetime import datetime

from pomefi.stock_wiki.aggregator import aggregate_stock_wiki_payload
from pomefi.stock_wiki.skills.timeline import (
    _load_price_rows,
    _normalize_events,
    _parse_events_from_evidence_lines,
    _repair_event_year,
    get_timeline,
)

import asyncio


def test_repair_event_year_reanchors_previous_year_date_into_recent_window() -> None:
    repaired = _repair_event_year("2025-03-10", today=datetime(2026, 3, 18))
    assert repaired == "2026-03-10"


def test_normalize_events_repairs_window_external_year() -> None:
    items = _normalize_events(
        [
            {"date": "2025-03-10", "title": "宁德时代业绩说明会", "content": "披露了全年产能利用率和订单变化。"},
            {"date": "2025-03-10", "title": "宁德时代业绩说明会"},
        ],
        today=datetime(2026, 3, 18),
    )
    assert len(items) == 1
    assert items[0]["date"] == "2026-03-10"
    assert items[0]["event_date"] == "2026-03-10"
    assert items[0]["content"] == "披露了全年产能利用率和订单变化。"


def test_parse_events_from_evidence_lines_recovers_events() -> None:
    items = _parse_events_from_evidence_lines(
        "2026-03-10 | 发布年报 | 证券时报\n2026-03-15 | 获得大额订单 | 中证网",
        today=datetime(2026, 3, 18),
    )
    assert len(items) == 2
    assert items[0]["date"] == "2026-03-10"
    assert items[0]["title"] == "发布年报"
    assert items[1]["source"] == "中证网"


def test_load_price_rows_retries_until_success(monkeypatch) -> None:
    attempts = {"count": 0}

    def _fake_hist(**kwargs) -> object:
        _ = kwargs
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("RemoteDisconnected")

        class _Frame:
            empty = False

            def rename(self, columns):
                _ = columns
                return self

            def copy(self):
                return self

            def astype(self, _value):
                return self

            def __getitem__(self, _key):
                return self

            def to_dict(self, orient="records"):
                _ = orient
                return [{"date": "2026-03-01", "close": 200.0}]

            def __setitem__(self, _key, _value):
                return None

        return _Frame()

    monkeypatch.setattr("pomefi.stock_wiki.skills.timeline.ak.stock_zh_a_hist", _fake_hist)
    monkeypatch.setattr("pomefi.stock_wiki.skills.timeline.time.sleep", lambda _seconds: None)

    payload = _load_price_rows("300750")

    assert attempts["count"] == 3
    assert payload["rows"]
    assert payload["akshare_calls"][0]["status"] == "error"
    assert payload["akshare_calls"][1]["status"] == "error"
    assert payload["akshare_calls"][2]["status"] == "ok"
    assert payload["akshare_calls"][2]["retry_count"] == 2


def test_load_price_rows_falls_back_to_tx_when_em_fails(monkeypatch) -> None:
    def _fake_hist(**kwargs) -> object:
        _ = kwargs
        raise RuntimeError("eastmoney down")

    def _fake_hist_tx(**kwargs) -> object:
        assert kwargs["symbol"] == "sz300750"

        class _Frame:
            empty = False

            def rename(self, columns):
                _ = columns
                return self

            def copy(self):
                return self

            def to_dict(self, orient="records"):
                _ = orient
                return [{"date": "2026-03-01", "close": 188.8}]

        return _Frame()

    monkeypatch.setattr("pomefi.stock_wiki.skills.timeline.ak.stock_zh_a_hist", _fake_hist)
    monkeypatch.setattr("pomefi.stock_wiki.skills.timeline.ak.stock_zh_a_hist_tx", _fake_hist_tx)
    monkeypatch.setattr("pomefi.stock_wiki.skills.timeline.time.sleep", lambda _seconds: None)

    payload = _load_price_rows("300750")

    assert payload["rows"] == [{"date": "2026-03-01", "close": 188.8, "event_desc": ""}]
    assert payload["akshare_calls"][-1]["interface"] == "stock_zh_a_hist_tx"
    assert payload["akshare_calls"][-1]["status"] == "ok"


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
    monkeypatch.setattr(
        "pomefi.stock_wiki.skills.timeline._load_events_branch",
        lambda *args, **kwargs: asyncio.sleep(
            0,
            result={
                "payload": {
                    "summary": "过去三个月共提取2个关键事件。",
                    "events": [
                        {"date": "2026-03-01", "event_date": "2026-03-02", "title": "发布年报", "content": "收入与利润低于市场预期。", "source": "web_search", "url": None},
                        {"date": "2026-03-05", "event_date": "2026-03-06", "title": "签订大单", "content": "新订单改善了全年产能消化预期。", "source": "web_search", "url": None},
                    ],
                    "trace": {
                        "tool_call_required": True,
                        "tool_call_observed": True,
                        "retry_count": 0,
                        "observed_tools": ["web_search"],
                        "turns": [],
                        "tool_events": [],
                        "degrade_reason": None,
                    },
                    "sources": [{"source": "web_search", "kind": "web_search", "title": "事件A", "published_at": "2026-03-02", "url": None}],
                    "error": None,
                },
                "status": "valid",
                "latency_ms": 120,
                "error": None,
            },
        ),
    )

    result = asyncio.run(
        get_timeline(
            "300750",
            "宁德时代",
        )
    )

    assert result["status"] == "valid"
    assert len(result["data"]["series"]) == 2
    assert len(result["data"]["events"]) == 2
    assert result["data"]["summary"] == "过去三个月共提取2个关键事件。"
    assert result["data"]["trace"]["phase_status"] == {"price_series": "valid", "events_json": "valid"}
    assert result["data"]["trace"]["phase_error"]["events_json"] is None
    assert result["data"]["events"][0]["date"] == "2026-03-01"
    assert result["data"]["events"][0]["content"] == "收入与利润低于市场预期。"
    assert result["data"]["series"][0]["event_desc"] == "发布年报"


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
    monkeypatch.setattr(
        "pomefi.stock_wiki.skills.timeline._load_events_branch",
        lambda *args, **kwargs: asyncio.sleep(
            0,
            result={
                "payload": {
                    "summary": "过去三个月共提取1个关键事件。",
                    "events": [{"date": "2026-03-01", "event_date": "2026-03-01", "title": "年报披露", "source": "web_search", "url": None}],
                    "trace": {},
                    "sources": [],
                    "error": None,
                },
                "status": "valid",
                "latency_ms": 80,
                "error": None,
            },
        ),
    )

    result = asyncio.run(
        get_timeline(
            "300750",
            "宁德时代",
        )
    )

    assert result["status"] == "error"
    assert result["data"]["series"] == []
    assert len(result["data"]["events"]) == 1
    assert result["data"]["unrecovered_reason_code"] == "AKSHARE_NETWORK_UNRECOVERED"
    assert result["data"]["trace"]["phase_status"]["price_series"] == "error"
    assert result["data"]["trace"]["phase_status"]["events_json"] == "valid"
    assert result["data"]["trace"]["phase_error"]["price_series"] == "price_fetch_failed: proxy"


def test_get_timeline_fails_when_events_unrecovered(monkeypatch) -> None:
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
    monkeypatch.setattr(
        "pomefi.stock_wiki.skills.timeline._load_events_branch",
        lambda *args, **kwargs: asyncio.sleep(
            0,
            result={
                "payload": {
                    "summary": "",
                    "events": [],
                    "trace": {
                        "tool_call_required": True,
                        "tool_call_observed": False,
                        "retry_count": 1,
                        "observed_tools": [],
                        "turns": [],
                        "tool_events": [],
                        "degrade_reason": None,
                    },
                    "sources": [],
                    "error": "timeline_required_tool_call_missing",
                },
                "status": "error",
                "latency_ms": 300,
                "error": "timeline_required_tool_call_missing",
            },
        ),
    )

    result = asyncio.run(get_timeline("300750", "宁德时代"))

    assert result["status"] == "error"
    assert len(result["data"]["series"]) == 2
    assert result["data"]["events"] == []
    assert result["data"]["unrecovered_reason_code"] == "TIMELINE_EVENTS_UNRECOVERED"
    assert result["data"]["trace"]["phase_status"] == {"price_series": "valid", "events_json": "error"}
    assert result["error"] == "timeline_required_tool_call_missing"


def test_get_timeline_recovers_events_from_final_content_when_json_events_empty(monkeypatch) -> None:
    def _fake_load_price_rows(symbol: str) -> dict[str, object]:
        _ = symbol
        return {
            "rows": [
                {"date": "2026-03-10", "close": 200.0, "event_desc": ""},
                {"date": "2026-03-15", "close": 202.0, "event_desc": ""},
            ],
            "asof": "2026-03-15",
            "data_origin": "live",
            "network_evidence": [],
            "akshare_calls": [],
            "error": None,
        }

    monkeypatch.setattr("pomefi.stock_wiki.skills.timeline._load_price_rows", _fake_load_price_rows)
    monkeypatch.setattr(
        "pomefi.stock_wiki.skills.timeline._load_events_branch",
        lambda *args, **kwargs: asyncio.sleep(
            0,
            result={
                "payload": {
                    "summary": "过去三个月共提取2个关键事件。",
                    "events": [],
                    "trace": {
                        "tool_call_required": True,
                        "tool_call_observed": True,
                        "retry_count": 0,
                        "observed_tools": ["web_search"],
                        "turns": [],
                        "tool_events": [],
                        "degrade_reason": None,
                        "final_content": "2026-03-10 | 发布年报 | 证券时报\n2026-03-15 | 获得大额订单 | 中证网",
                    },
                    "sources": [],
                    "error": None,
                },
                "status": "error",
                "latency_ms": 180,
                "error": "timeline_events_empty",
            },
        ),
    )

    result = asyncio.run(get_timeline("300750", "宁德时代"))

    assert result["status"] == "valid"
    assert len(result["data"]["events"]) == 2
    assert result["data"]["series"][0]["event_desc"] == "发布年报"
    assert result["data"]["trace"]["phase_status"] == {"price_series": "valid", "events_json": "error"}


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
                        "phase_status": {"price_series": "error", "events_json": "error"},
                        "phase_error": {"price_series": "price_fetch_failed: proxy", "events_json": "timeline_required_tool_call_missing"},
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

    timeline = payload["data"]["skills"]["timeline"]
    evidence = timeline["data"]["trace"]
    assert payload["metadata"]["page_status"] == "partial"
    assert "timeline" in payload["metadata"]["failed_skills"]
    assert evidence["phase_latency_ms"] == {"price_series": 122, "events_json": 0}
    assert evidence["phase_status"] == {"price_series": "error", "events_json": "error"}
    assert evidence["phase_error"] == {"price_series": "price_fetch_failed: proxy", "events_json": "timeline_required_tool_call_missing"}
