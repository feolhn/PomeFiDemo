from __future__ import annotations

import asyncio

from scripts import benchmark_timeline


def test_timeline_benchmark_summary(monkeypatch) -> None:
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

    calls = {"count": 0}

    async def _fake_load_events_branch(symbol: str, company_name: str, **_: object) -> dict:
        calls["count"] += 1
        return {
            "status": "valid",
            "payload": {
                "summary": f"{company_name}-{calls['count']}",
                "events": [
                    {
                        "date": "2026-03-01",
                        "title": "签订大单",
                        "content": "订单落地强化了全年收入兑现预期。",
                        "sentiment": "positive",
                    }
                ],
                "sources": [{"source": "行业媒体", "title": "订单快讯"}],
                "trace": {"tool_call_observed": True, "final_content": "证据摘要"},
            },
            "error": None,
        }

    monkeypatch.setattr(benchmark_timeline, "resolve_kimi_config", lambda: _Config())
    monkeypatch.setattr(benchmark_timeline, "FormulaToolClient", _FormulaClient)
    monkeypatch.setattr(benchmark_timeline, "_load_events_branch", _fake_load_events_branch)

    payload = asyncio.run(benchmark_timeline._run_benchmark("300750", "宁德时代", 2))
    assert payload["skill"] == "timeline_kimi_benchmark"
    assert payload["summary"]["runs"] == 2
    assert payload["summary"]["valid_runs"] == 2
    assert len(payload["runs"]) == 2
    assert payload["runs"][0]["event_summaries"] == ["2026-03-01 | 签订大单 | 订单落地强化了全年收入兑现预期。 | positive"]
    assert payload["runs"][0]["sources"] == [{"source": "行业媒体", "title": "订单快讯"}]
    assert payload["runs"][0]["trace"]["tool_call_observed"] is True
    assert payload["runs"][0]["trace"]["evidence_preview"] == "证据摘要"
