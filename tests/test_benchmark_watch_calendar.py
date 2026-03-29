from __future__ import annotations

import asyncio

from scripts import benchmark_watch_calendar


def test_watch_calendar_benchmark_summary(monkeypatch) -> None:
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

    async def _fake_get_watch_calendar(symbol: str, company_name: str, **_: object) -> dict:
        calls["count"] += 1
        return {
            "status": "valid",
            "data": {
                "summary": f"{company_name}-{calls['count']}",
                "items": [
                    {
                        "date": "2026年4月",
                        "event": "年度股东大会",
                        "source": "公司公告",
                    }
                ],
                "trace": {"tool_call_observed": True},
            },
            "sources": [{"source": "公司公告", "title": "年度股东大会通知"}],
            "error": None,
        }

    monkeypatch.setattr(benchmark_watch_calendar, "resolve_kimi_config", lambda: _Config())
    monkeypatch.setattr(benchmark_watch_calendar, "FormulaToolClient", _FormulaClient)
    monkeypatch.setattr(benchmark_watch_calendar, "get_watch_calendar", _fake_get_watch_calendar)

    payload = asyncio.run(benchmark_watch_calendar._run_benchmark("300750", "宁德时代", 2))
    assert payload["skill"] == "watch_calendar_benchmark"
    assert payload["summary"]["runs"] == 2
    assert payload["summary"]["valid_runs"] == 2
    assert len(payload["runs"]) == 2
    assert payload["runs"][0]["item_summaries"] == ["2026年4月 | 年度股东大会 | 公司公告"]
    assert payload["runs"][0]["sources"] == [{"source": "公司公告", "title": "年度股东大会通知"}]
    assert payload["runs"][0]["trace"]["tool_call_observed"] is True
    assert payload["runs"][0]["trace"]["evidence_preview"] == ""
