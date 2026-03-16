from __future__ import annotations

import asyncio

from pomefi.agent.loop import KimiAgentLoop
from pomefi.config import KimiConfig


class _FakeFunctionDelta:
    def __init__(self, *, name=None, arguments=None):
        self.name = name
        self.arguments = arguments


class _FakeToolCallDelta:
    def __init__(self, *, index, id=None, type=None, function=None):
        self.index = index
        self.id = id
        self.type = type
        self.function = function


class _FakeDelta:
    def __init__(self, *, role=None, content=None, reasoning_content=None, tool_calls=None):
        self.role = role
        self.content = content
        self.reasoning_content = reasoning_content
        self.tool_calls = tool_calls


class _FakeChoice:
    def __init__(self, *, delta, finish_reason=None):
        self.delta = delta
        self.finish_reason = finish_reason


class _FakeChunk:
    def __init__(self, choices):
        self.choices = choices
        self.usage = None


class _FakeStream:
    def __init__(self, chunks):
        self._chunks = list(chunks)

    def __aiter__(self):
        self._index = 0
        return self

    async def __anext__(self):
        if self._index >= len(self._chunks):
            raise StopAsyncIteration
        chunk = self._chunks[self._index]
        self._index += 1
        return chunk


class _FakeCompletions:
    def __init__(self):
        self.calls = []
        self._call_index = 0

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        self._call_index += 1
        if self._call_index == 1:
            return _FakeStream(
                [
                    _FakeChunk(
                        [
                            _FakeChoice(
                                delta=_FakeDelta(
                                    role="assistant",
                                    reasoning_content="先查新闻",
                                    content="先调用工具",
                                    tool_calls=[
                                        _FakeToolCallDelta(
                                            index=0,
                                            id="call_web_1",
                                            type="function",
                                            function=_FakeFunctionDelta(name="web_search", arguments='{"query":"宁德'),
                                        )
                                    ],
                                ),
                                finish_reason=None,
                            )
                        ]
                    ),
                    _FakeChunk(
                        [
                            _FakeChoice(
                                delta=_FakeDelta(
                                    tool_calls=[
                                        _FakeToolCallDelta(
                                            index=0,
                                            function=_FakeFunctionDelta(arguments='时代"}'),
                                        )
                                    ]
                                ),
                                finish_reason="tool_calls",
                            )
                        ]
                    ),
                ]
            )
        return _FakeStream(
            [
                _FakeChunk([_FakeChoice(delta=_FakeDelta(role="assistant", content="最终结论"), finish_reason="stop")]),
            ]
        )


class _FakeChat:
    def __init__(self):
        self.completions = _FakeCompletions()


class _FakeOpenAI:
    def __init__(self):
        self.chat = _FakeChat()

    async def close(self):
        return None


class _FakeFormulaClient:
    def __init__(self):
        self.remote_tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
                },
            }
        ]
        self.calls = []

    def get_formula_uri(self, tool_name: str):
        if tool_name == "web_search":
            return "moonshot/web-search:latest"
        return None

    async def call_tool(self, formula_uri: str, function_payload: dict):
        self.calls.append((formula_uri, function_payload))
        return {"fiber": {}, "content": "[]"}


def test_agent_loop_stream_tool_call_assembly() -> None:
    config = KimiConfig(
        api_key="test",
        base_url="https://api.test",
        model="kimi-k2.5",
        temperature=1.0,
        stream=True,
        debug=False,
    )
    formula_client = _FakeFormulaClient()
    agent = KimiAgentLoop(config=config, formula_client=formula_client)
    agent.openai = _FakeOpenAI()

    trace = asyncio.run(
        agent.run_conversation_trace(
            user_prompt="宁德时代怎么看",
            system_prompt="你是助手",
        )
    )

    assert trace["turns"][0]["has_tool_calls"] is True
    assert trace["tool_events"][0]["tool_name"] == "web_search"
    assert trace["tool_events"][0]["arguments_text"] == '{"query":"宁德时代"}'
    assert trace["final_content"] == "最终结论"
    assert formula_client.calls
    formula_uri, function_payload = formula_client.calls[0]
    assert formula_uri == "moonshot/web-search:latest"
    assert function_payload["arguments"] == '{"query":"宁德时代"}'

    second_request_messages = agent.openai.chat.completions.calls[1]["messages"]
    assistant_message = second_request_messages[2]
    assert assistant_message["reasoning_content"] == "先查新闻"
    assert assistant_message["tool_calls"][0]["id"] == "call_web_1"
    assert second_request_messages[3]["role"] == "tool"
    assert second_request_messages[3]["tool_call_id"] == "call_web_1"
