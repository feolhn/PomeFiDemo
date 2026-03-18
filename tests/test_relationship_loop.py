from __future__ import annotations

import asyncio

from pomefi.config import KimiConfig
from pomefi.stock_wiki.skills import relationship


class _FakeFormulaClient:
    pass


def test_relationship_returns_structured_json(monkeypatch) -> None:
    async def _fake_probe(**kwargs):
        _ = kwargs
        return {
            "content_json": {
                "summary": "产业链集中在材料与整车两端。",
                "nodes": [{"id": "宁德时代", "role": "theme"}],
                "edges": [],
            },
            "tool_trace": {
                "turns": [{"index": 0, "has_tool_calls": True}],
                "tool_events": [{"tool_name": "web_search", "tool_content_preview": "ok"}],
                "degrade_reason": None,
            },
            "sources": [{"source": "新华社", "kind": "web_search", "title": "上游材料企业A", "published_at": "2026-03-01"}],
            "error": None,
            "retry_count": 0,
            "tool_call_observed": True,
            "observed_tools": ["web_search"],
        }

    monkeypatch.setattr(relationship, "run_tool_grounded_json_skill", _fake_probe)
    config = KimiConfig(
        api_key="test",
        base_url="https://api.test",
        model="kimi-k2.5",
        temperature=1.0,
        stream=True,
        debug=False,
    )
    result = asyncio.run(
        relationship.get_relationship(
            "300750",
            "宁德时代",
            config=config,
            formula_client=_FakeFormulaClient(),
        )
    )
    assert result["status"] == "valid"
    assert result["data"]["pending"] is False
    assert result["data"]["nodes"][0]["id"] == "宁德时代"


def test_relationship_retries_when_no_tool_call(monkeypatch) -> None:
    async def _fake_no_tool_probe(**kwargs):
        _ = kwargs
        return {
            "content_json": None,
            "tool_trace": {
                "turns": [{"index": 0, "has_tool_calls": False}],
                "tool_events": [],
                "degrade_reason": None,
            },
            "sources": [],
            "error": "relationship_required_tool_call_missing",
            "retry_count": 2,
            "tool_call_observed": False,
            "observed_tools": [],
        }

    monkeypatch.setattr(relationship, "run_tool_grounded_json_skill", _fake_no_tool_probe)
    config = KimiConfig(
        api_key="test",
        base_url="https://api.test",
        model="kimi-k2.5",
        temperature=1.0,
        stream=True,
        debug=False,
    )
    result = asyncio.run(
        relationship.get_relationship(
            "300750",
            "宁德时代",
            config=config,
            formula_client=_FakeFormulaClient(),
        )
    )
    assert result["status"] == "degraded"
    assert result["error"] == "relationship_no_tool_calls"
    assert result["data"]["trace"]["tool_call_observed"] is False
    assert result["data"]["trace"]["retry_count"] == 2
