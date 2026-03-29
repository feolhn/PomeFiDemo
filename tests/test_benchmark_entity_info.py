from __future__ import annotations

import asyncio

from scripts import benchmark_entity_info


def test_entity_info_benchmark_summary(monkeypatch) -> None:
    class _Config:
        api_key = "test"
        base_url = "https://api.moonshot.cn/v1"

    class _FakeFormulaClient:
        def __init__(self, *, base_url: str, api_key: str) -> None:
            self.base_url = base_url
            self.api_key = api_key

        async def load_tools(self, formula_uris) -> list[dict]:
            _ = formula_uris
            return []

        async def aclose(self) -> None:
            return None

    async def _fake_get_entity_info(symbol: str, company_name: str, *, config=None, formula_client=None, event_handler=None) -> dict:
        _ = symbol, config, formula_client, event_handler
        return {
            "status": "valid",
            "data": {
                "company_name": company_name,
                "industry": "光伏",
                "main_business": "光伏组件",
                "summary_100cn": "组件龙头，靠一体化成本与渠道能力赚钱。",
                "core_competencies": ["一体化制造降低成本波动。"],
                "profit_analysis": {
                    "revenue_structure": "组件仍是收入核心，电站与新业务贡献利润弹性。",
                    "profit_tag": "周期弹性",
                },
                "investment_tags": ["沪深300", "北向重仓", "光伏"],
            },
            "error": None,
        }

    monkeypatch.setattr(benchmark_entity_info, "resolve_kimi_config", lambda: _Config())
    monkeypatch.setattr(benchmark_entity_info, "FormulaToolClient", _FakeFormulaClient)
    monkeypatch.setattr(benchmark_entity_info, "get_entity_info", _fake_get_entity_info)

    payload = asyncio.run(benchmark_entity_info._run_benchmark("601012", "隆基绿能", 2))
    assert payload["skill"] == "entity_info_benchmark"
    assert payload["summary"]["runs"] == 2
    assert payload["summary"]["valid_runs"] == 2
    assert payload["summary"]["avg_tags"] == 3
    assert payload["runs"][0]["industry"] == "光伏"
    assert payload["runs"][0]["core_competencies"] == ["一体化制造降低成本波动。"]
    assert payload["runs"][0]["profit_analysis"]["profit_tag"] == "周期弹性"
    assert payload["runs"][0]["investment_tags"] == ["沪深300", "北向重仓", "光伏"]
