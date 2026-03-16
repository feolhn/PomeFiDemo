from __future__ import annotations

import asyncio
import json

from pomefi.config import KimiConfig
from pomefi.stock_wiki.skills import relationship


class _FakeAgentLoop:
    def __init__(self, *, config, formula_client):
        _ = config
        _ = formula_client

    async def run_conversation_trace(self, **kwargs):
        _ = kwargs
        return {
            "turns": [{"index": 0, "has_tool_calls": True}],
            "tool_events": [
                {
                    "tool_name": "web_search",
                    "tool_content": json.dumps(
                        [{"title": "上游材料企业A", "published_at": "2026-03-01", "source": "新华社"}],
                        ensure_ascii=False,
                    ),
                }
            ],
            "final_content": json.dumps(
                {
                    "summary": "产业链集中在材料与整车两端。",
                    "nodes": [{"id": "宁德时代", "role": "theme"}],
                    "edges": [],
                },
                ensure_ascii=False,
            ),
            "degrade_reason": None,
        }

    async def run_conversation_trace_stream(self, **kwargs):
        trace = await self.run_conversation_trace(**kwargs)
        yield {"type": "session_done", "trace": trace}

    async def aclose(self):
        return None


class _FakeFormulaClient:
    pass


def test_relationship_returns_structured_json(monkeypatch) -> None:
    monkeypatch.setattr(relationship, "KimiAgentLoop", _FakeAgentLoop)
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
    class _NoToolAgentLoop(_FakeAgentLoop):
        def __init__(self, *, config, formula_client):
            super().__init__(config=config, formula_client=formula_client)
            self.calls = 0

        async def run_conversation_trace(self, **kwargs):
            _ = kwargs
            self.calls += 1
            return {
                "turns": [{"index": 0, "has_tool_calls": False}],
                "tool_events": [],
                "final_content": json.dumps(
                    {"summary": "空结果", "nodes": [], "edges": []},
                    ensure_ascii=False,
                ),
                "degrade_reason": None,
            }

    monkeypatch.setattr(relationship, "KimiAgentLoop", _NoToolAgentLoop)
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
