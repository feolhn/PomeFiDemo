from __future__ import annotations

import asyncio

from scripts import benchmark_relationship


def test_relationship_benchmark_summary(monkeypatch) -> None:
    class _Config:
        api_key = "test"
        base_url = "https://api.moonshot.cn/v1"

    class _FormulaClient:
        def __init__(self, **_: object) -> None:
            self.loaded: list[str] = []

        async def load_tools(self, uris: list[str]) -> None:
            self.loaded = list(uris)

        async def aclose(self) -> None:
            return None

    async def _fake_get_relationship(symbol: str, company_name: str, **_: object) -> dict:
        _ = symbol
        return {
            "status": "valid",
            "data": {
                "summary": f"{company_name} 受上游价格与政策变量共同驱动。",
                "nodes": [
                    {"id": company_name, "role": "theme"},
                    {"id": "硅料价格", "role": "theme"},
                ],
                "edges": [
                    {"from": "硅料价格", "to": company_name, "relation": "构成成本"},
                ],
                "trace": {
                    "tool_call_observed": True,
                    "observed_tools": ["web_search"],
                    "turns": [{"index": 0, "has_tool_calls": True, "tool_names": ["web_search"]}],
                },
            },
            "sources": [{"source": "行业媒体", "title": "价格跟踪"}],
            "error": None,
        }

    monkeypatch.setattr(benchmark_relationship, "resolve_kimi_config", lambda: _Config())
    monkeypatch.setattr(benchmark_relationship, "FormulaToolClient", _FormulaClient)
    monkeypatch.setattr(benchmark_relationship, "get_relationship", _fake_get_relationship)

    payload = asyncio.run(benchmark_relationship._run_benchmark("601012", "隆基绿能", 2))
    assert payload["skill"] == "relationship_benchmark"
    assert payload["summary"]["runs"] == 2
    assert payload["summary"]["valid_runs"] == 2
    assert payload["runs"][0]["node_ids"] == ["隆基绿能", "硅料价格"]
    assert payload["runs"][0]["edge_summaries"] == ["硅料价格 -> 构成成本 -> 隆基绿能"]
    assert payload["runs"][0]["trace"]["tool_call_observed"] is True
