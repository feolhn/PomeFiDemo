from __future__ import annotations

import asyncio
import json

import pandas as pd

from pomefi.config import KimiConfig
from pomefi.stock_wiki.skills.timeline import get_timeline


class _FakeFormulaClient:
    async def call_tool(self, formula_uri, function_payload):
        assert formula_uri == "moonshot/web-search:latest"
        _ = function_payload
        return {
            "content": json.dumps(
                [
                    {"title": "2026-03-01 电池新技术发布", "published_at": "2026-03-01", "source": "新华社", "url": "https://example.com/1"},
                    {"title": "2026-03-05 产业政策更新", "published_at": "2026-03-05", "source": "证券时报", "url": "https://example.com/2"},
                ],
                ensure_ascii=False,
            )
        }


def test_get_timeline_merges_price_and_events(monkeypatch) -> None:
    history_df = pd.DataFrame(
        {
            "日期": ["2026-03-01", "2026-03-05", "2026-03-10"],
            "收盘": [200.0, 202.0, 203.5],
        }
    )
    monkeypatch.setattr("pomefi.stock_wiki.skills.timeline.get_cached_price_history", lambda symbol: history_df)
    async def _fake_stream_json_object(**kwargs):
        _ = kwargs
        yield {
            "type": "structured_json_done",
            "json": {
                "summary": "近三个月有两条关键事件。",
                "events": [
                    {"date": "2026-03-01", "title": "电池新技术发布", "source": "新华社", "url": "https://example.com/1"},
                    {"date": "2026-03-05", "title": "产业政策更新", "source": "证券时报", "url": "https://example.com/2"},
                ],
                "merge_notes": "按日期合并",
            },
        }
    monkeypatch.setattr("pomefi.stock_wiki.skills.timeline.stream_json_object", _fake_stream_json_object)
    config = KimiConfig(
        api_key="test",
        base_url="https://api.test",
        model="kimi-k2.5",
        temperature=1.0,
        stream=True,
        debug=False,
    )

    result = asyncio.run(
        get_timeline(
            "300750",
            "宁德时代",
            config=config,
            formula_client=_FakeFormulaClient(),
        )
    )

    assert result["status"] in {"valid", "degraded"}
    assert len(result["data"]["series"]) == 3
    assert any(row.get("event_desc") for row in result["data"]["series"])
