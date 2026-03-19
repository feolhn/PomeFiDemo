from __future__ import annotations

import asyncio

import pytest

from scripts import debug_skill


def test_debug_skill_runs_summary(monkeypatch) -> None:
    async def _fake_summary(symbol: str, company_name: str) -> dict:
        return {
            "status": "valid",
            "data": {"summary": f"{symbol}:{company_name}"},
            "sources": [],
            "error": None,
            "data_ready": True,
            "is_critical": False,
        }

    monkeypatch.setattr(debug_skill, "get_stock_summary", _fake_summary)
    payload = asyncio.run(debug_skill._run_skill("summary", "300750", "宁德时代"))
    assert payload["skill"] == "summary"
    assert payload["result"]["status"] == "valid"
    assert payload["result"]["data"]["summary"] == "300750:宁德时代"


def test_debug_skill_requires_api_key_for_entity_info(monkeypatch) -> None:
    class _Config:
        api_key = ""
        base_url = "https://api.moonshot.cn/v1"
        model = "kimi-k2.5"
        temperature = 1.0
        stream = True
        debug = False

    monkeypatch.setattr(debug_skill, "resolve_kimi_config", lambda: _Config())
    with pytest.raises(RuntimeError, match="entity_info requires KIMI_API_KEY"):
        asyncio.run(debug_skill._run_skill("entity_info", "300750", "宁德时代"))


def test_timeline_bundle_contains_split_branches(monkeypatch) -> None:
    async def _fake_bundle(symbol: str, company_name: str, *, event_handler=None) -> dict:
        if event_handler is not None:
            await event_handler({"type": "timeline_phase", "phase": "price_series", "status": "valid"})
        return {
            "merged": {"status": "valid", "data": {"symbol": symbol}, "sources": [], "error": None, "data_ready": True, "is_critical": True},
            "akshare": {"status": "valid", "data": {"series": [1]}, "sources": [], "error": None, "data_ready": True, "is_critical": True},
            "kimi": {"status": "valid", "data": {"events": [1]}, "sources": [], "error": None, "data_ready": True, "is_critical": True},
        }

    monkeypatch.setattr(debug_skill, "get_timeline_debug_bundle", _fake_bundle)
    payload = asyncio.run(debug_skill._run_timeline_bundle("300750", "宁德时代"))
    assert payload["skill"] == "timeline"
    assert payload["result"]["status"] == "valid"
    assert payload["branches"]["akshare"]["data"]["series"] == [1]
    assert payload["branches"]["kimi"]["data"]["events"] == [1]
    assert "runtime" in payload
