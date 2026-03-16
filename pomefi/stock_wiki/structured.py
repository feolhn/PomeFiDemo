from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from pomefi.config import KimiConfig
from pomefi.streaming.events import (
    EVENT_LLM_CONTENT_DELTA,
    EVENT_LLM_REASONING_DELTA,
    make_event,
)


async def stream_json_object(
    *,
    config: KimiConfig,
    system_prompt: str,
    user_prompt: str,
    event_scope: str,
    max_completion_tokens: int = 16000,
) -> AsyncIterator[dict[str, Any]]:
    client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)
    finish_reason = ""
    content_chunks: list[str] = []
    try:
        stream = await client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=config.temperature,
            max_completion_tokens=max_completion_tokens,
            stream=True,
        )
        async for chunk in stream:
            for choice in list(getattr(chunk, "choices", None) or []):
                reason = getattr(choice, "finish_reason", None)
                if reason:
                    finish_reason = str(reason)
                delta = getattr(choice, "delta", None)
                if delta is None:
                    continue

                reasoning_delta = getattr(delta, "reasoning_content", None)
                if reasoning_delta:
                    yield make_event(
                        EVENT_LLM_REASONING_DELTA,
                        scope=event_scope,
                        delta=str(reasoning_delta),
                    )

                content_delta = getattr(delta, "content", None)
                if content_delta:
                    text = str(content_delta)
                    content_chunks.append(text)
                    yield make_event(
                        EVENT_LLM_CONTENT_DELTA,
                        scope=event_scope,
                        delta=text,
                    )

        text = "".join(content_chunks).strip()
        if finish_reason == "length":
            raise RuntimeError("schema_truncated")
        loaded = json.loads(text)
        if not isinstance(loaded, dict):
            raise RuntimeError("json_object_expected")
        yield make_event("structured_json_done", scope=event_scope, content=text, json=loaded)
    finally:
        close_method = getattr(client, "close", None)
        if callable(close_method):
            await close_method()


async def json_object_once(
    *,
    config: KimiConfig,
    system_prompt: str,
    user_prompt: str,
    event_scope: str,
    max_completion_tokens: int = 16000,
) -> dict[str, Any]:
    json_object: dict[str, Any] | None = None
    async for event in stream_json_object(
        config=config,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        event_scope=event_scope,
        max_completion_tokens=max_completion_tokens,
    ):
        if event.get("type") == "structured_json_done":
            loaded = event.get("json")
            if isinstance(loaded, dict):
                json_object = loaded
    if json_object is None:
        raise RuntimeError("structured_json_missing")
    return json_object
