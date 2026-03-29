from __future__ import annotations

import asyncio

from pomefi.config import KimiConfig
from pomefi.stock_wiki import structured


class _FakeDelta:
    def __init__(self, *, content: str | None = None, reasoning_content: str | None = None):
        self.content = content
        self.reasoning_content = reasoning_content


class _FakeChoice:
    def __init__(self, delta: _FakeDelta, finish_reason: str | None = None):
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

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeStream(
            [
                _FakeChunk([_FakeChoice(_FakeDelta(reasoning_content="先思考"), finish_reason=None)]),
                _FakeChunk([_FakeChoice(_FakeDelta(content='{"company_name":"宁德时代",'), finish_reason=None)]),
                _FakeChunk([_FakeChoice(_FakeDelta(content='"summary_100cn":"电池龙头"}'), finish_reason="stop")]),
            ]
        )


class _FakeChat:
    def __init__(self):
        self.completions = _FakeCompletions()


class _FakeAsyncOpenAI:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.chat = _FakeChat()
        self.closed = False
        _FakeAsyncOpenAI.instances.append(self)

    async def close(self):
        self.closed = True


def test_json_object_once_enforces_json_mode(monkeypatch) -> None:
    _FakeAsyncOpenAI.instances.clear()
    monkeypatch.setattr(structured, "AsyncOpenAI", _FakeAsyncOpenAI)
    config = KimiConfig(
        api_key="test",
        base_url="https://api.test",
        model="kimi-k2.5",
        temperature=1.0,
        stream=True,
        debug=False,
    )

    payload = asyncio.run(
        structured.json_object_once(
            config=config,
            system_prompt="只输出 JSON",
            user_prompt="返回 company_name 和 summary_100cn",
            event_scope="entity_info",
        )
    )

    assert payload["company_name"] == "宁德时代"
    assert _FakeAsyncOpenAI.instances
    call = _FakeAsyncOpenAI.instances[0].chat.completions.calls[0]
    assert call["response_format"] == {"type": "json_object"}
    assert call["stream"] is True
    assert call["max_completion_tokens"] == 4096
    assert call["extra_body"] == {"thinking": {"type": "disabled"}}
    assert "temperature" not in call
