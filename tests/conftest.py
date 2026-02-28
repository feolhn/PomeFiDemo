from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)
if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_TEXT)


class FakeResponse:
    def __init__(self, payload: Any, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self) -> Any:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeAsyncClient:
    def __init__(
        self,
        *,
        get_payloads: dict[str, Any] | None = None,
        post_payloads: dict[str, Any] | None = None,
    ):
        self.get_payloads = dict(get_payloads or {})
        self.post_payloads = dict(post_payloads or {})
        self.get_calls: list[dict[str, Any]] = []
        self.post_calls: list[dict[str, Any]] = []
        self.closed = False

    async def get(self, path: str, **kwargs: Any) -> FakeResponse:
        self.get_calls.append({"path": path, "kwargs": kwargs})
        return FakeResponse(self.get_payloads[path])

    async def post(self, path: str, **kwargs: Any) -> FakeResponse:
        self.post_calls.append({"path": path, "kwargs": kwargs})
        return FakeResponse(self.post_payloads[path])

    async def aclose(self) -> None:
        self.closed = True


@pytest.fixture
def fake_async_client_cls():
    return FakeAsyncClient


@pytest.fixture
def sample_metrics_data() -> dict[str, Any]:
    return {
        "asof": "2026-02-27",
        "symbol": "300750",
        "resolved_name": "宁德时代",
        "metrics": {
            "price_last": 201.5,
            "ret_5d": 0.082,
            "vol_20d": 0.32,
            "max_drawdown_1y": -0.21,
            "pe_ttm": 18.2,
            "pb": 3.1,
            "profit_yoy": 0.14,
        },
        "notes": ["profit_yoy derived from financial indicators"],
    }


@pytest.fixture
def sample_local_context(sample_metrics_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "metrics_data": deepcopy(sample_metrics_data),
        "chart_index": [
            {
                "chart_id": "price_1y_line",
                "type": "line",
                "title": "价格走势（近一年）",
                "data_ref": "local://raw_bundle/price_history_1y",
                "x_key": "date",
                "y_keys": ["close"],
            }
        ],
        "raw_bundle": {
            "profile": {"company_name": "宁德时代"},
            "price_history_1y": [
                {"date": "2026-02-20", "close": 195.0},
                {"date": "2026-02-27", "close": 201.5},
            ],
            "valuation_5y": [
                {"date": "2025-02-27", "pe_ttm": 15.0, "pb": 2.6},
                {"date": "2026-02-27", "pe_ttm": 18.2, "pb": 3.1},
            ],
            "financial_indicators": [
                {"date": "2025-12-31", "revenue_yoy": 0.12, "profit_yoy": 0.14}
            ],
        },
    }


@pytest.fixture
def sample_trace(sample_local_context: dict[str, Any]) -> dict[str, Any]:
    return {
        "prompt": "宁德时代怎么看",
        "turns": [
            {"index": 0, "has_tool_calls": True, "tool_names": ["akshare_tool", "web_search"], "reasoning_present": True, "content_preview": ""},
            {"index": 1, "has_tool_calls": False, "tool_names": [], "reasoning_present": True, "content_preview": "先看估值和盈利斜率。"},
        ],
        "tool_events": [
            {
                "tool_name": "akshare_tool",
                "tool_call_id": "call_ak_1",
                "source": "local",
                "formula_uri": None,
                "arguments_text": '{"symbol":"300750","metrics":["price_last","pe_ttm"]}',
                "arguments_dict": {"symbol": "300750", "metrics": ["price_last", "pe_ttm"]},
                "jsonable_ok": True,
                "local_context_keys": ["chart_index", "metrics_data", "raw_bundle"],
                "tool_content": '{"metrics_data":{"symbol":"300750"}}',
                "tool_content_preview": '{"metrics_data":{"symbol":"300750"}}',
            },
            {
                "tool_name": "date",
                "tool_call_id": "call_date_1",
                "source": "formula",
                "formula_uri": "moonshot/date:latest",
                "arguments_text": "{}",
                "arguments_dict": {},
                "jsonable_ok": None,
                "local_context_keys": [],
                "tool_content": '{"date":"2026-02-27"}',
                "tool_content_preview": '{"date":"2026-02-27"}',
            },
            {
                "tool_name": "web_search",
                "tool_call_id": "call_web_1",
                "source": "formula",
                "formula_uri": "moonshot/web-search:latest",
                "arguments_text": '{"query":"宁德时代 最新 风险"}',
                "arguments_dict": {"query": "宁德时代 最新 风险"},
                "jsonable_ok": None,
                "local_context_keys": [],
                "tool_content": '[{"title":"电池行业新闻","source":"新华社","published_at":"2026-02-27T08:00:00+08:00","key_claim":"行业催化","url":"https://example.com"}]',
                "tool_content_preview": '[{"title":"电池行业新闻"}]',
            },
        ],
        "local_context": {"call_ak_1": deepcopy(sample_local_context)},
        "final_content": "先看估值和盈利斜率，再决定是否继续观察。",
        "usage": {"prompt_tokens": 100, "completion_tokens": 80, "total_tokens": 180},
        "degrade_reason": None,
        "events": [],
    }


@pytest.fixture
def sample_search_summary() -> dict[str, Any]:
    return {
        "title": "电池行业新闻",
        "source": "新华社",
        "published_at": "2026-02-27T08:00:00+08:00",
        "key_claim": "行业催化",
        "url": "https://example.com",
    }


@pytest.fixture
def sample_result_card_input(sample_trace: dict[str, Any], sample_search_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "question": "宁德时代怎么看",
        "answer": "先看估值和盈利斜率，再决定是否继续观察。",
        "model": "kimi-k2.5",
        "trace": deepcopy(sample_trace),
        "search_summaries": [deepcopy(sample_search_summary)],
        "date_value": "2026-02-27",
        "usage": {"prompt_tokens": 100, "completion_tokens": 80, "total_tokens": 180},
    }
