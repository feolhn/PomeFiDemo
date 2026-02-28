from __future__ import annotations

import asyncio
import json

from pomefi.tools.formula import FormulaToolClient


def test_load_tools_maps_function_to_uri(fake_async_client_cls) -> None:
    client = FormulaToolClient(base_url="https://api.test", api_key="token")
    client.http = fake_async_client_cls(
        get_payloads={
            "/formulas/moonshot/web-search:latest/tools": {
                "tools": [
                    {"type": "function", "function": {"name": "web_search"}},
                    {"type": "builtin_function", "builtin_function": {"name": "moonshot/web-search:latest"}},
                ]
            }
        }
    )

    tools = asyncio.run(client.load_tools(["moonshot/web-search:latest"]))

    assert len(tools) == 2
    assert client.get_formula_uri("web_search") == "moonshot/web-search:latest"


def test_call_tool_posts_official_body_and_uses_output(fake_async_client_cls) -> None:
    client = FormulaToolClient(base_url="https://api.test", api_key="token")
    fake_http = fake_async_client_cls(
        post_payloads={
            "/formulas/moonshot/web-search:latest/fibers": {
                "status": "completed",
                "context": {"output": "result text"},
            }
        }
    )
    client.http = fake_http

    result = asyncio.run(
        client.call_tool(
            "moonshot/web-search:latest",
            {"name": "web_search", "arguments": '{"query":"宁德时代"}'},
        )
    )

    assert result["content"] == "result text"
    assert fake_http.post_calls[0]["path"] == "/formulas/moonshot/web-search:latest/fibers"
    assert fake_http.post_calls[0]["kwargs"]["json"] == {
        "name": "web_search",
        "arguments": '{"query":"宁德时代"}',
    }


def test_call_tool_falls_back_to_encrypted_output(fake_async_client_cls) -> None:
    client = FormulaToolClient(base_url="https://api.test", api_key="token")
    client.http = fake_async_client_cls(
        post_payloads={
            "/formulas/moonshot/date:latest/fibers": {
                "status": "completed",
                "context": {"encrypted_output": "encrypted text"},
            }
        }
    )

    result = asyncio.run(client.call_tool("moonshot/date:latest", {"name": "date", "arguments": "{}"}))

    assert result["content"] == "encrypted text"


def test_call_tool_returns_error_payload_when_no_output(fake_async_client_cls) -> None:
    client = FormulaToolClient(base_url="https://api.test", api_key="token")
    client.http = fake_async_client_cls(
        post_payloads={
            "/formulas/moonshot/date:latest/fibers": {
                "status": "failed",
                "context": {},
            }
        }
    )

    result = asyncio.run(client.call_tool("moonshot/date:latest", {"name": "date", "arguments": "{}"}))
    payload = json.loads(result["content"])

    assert payload["fiber_status"] == "failed"
    assert "error" in payload


def test_call_tool_stringifies_dict_arguments(fake_async_client_cls) -> None:
    client = FormulaToolClient(base_url="https://api.test", api_key="token")
    fake_http = fake_async_client_cls(
        post_payloads={
            "/formulas/moonshot/web-search:latest/fibers": {
                "status": "completed",
                "context": {"output": {"items": []}},
            }
        }
    )
    client.http = fake_http

    result = asyncio.run(
        client.call_tool(
            "moonshot/web-search:latest",
            {"name": "web_search", "arguments": {"query": "AI 新闻"}},
        )
    )

    assert json.loads(fake_http.post_calls[0]["kwargs"]["json"]["arguments"]) == {"query": "AI 新闻"}
    assert json.loads(result["content"]) == {"items": []}
