from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from .events import EVENT_SESSION_DONE


async def collect_stream_events(event_stream: AsyncIterator[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    events: list[dict[str, Any]] = []
    final_trace: dict[str, Any] | None = None
    async for event in event_stream:
        events.append(event)
        if event.get("type") == EVENT_SESSION_DONE:
            trace = event.get("trace")
            if isinstance(trace, dict):
                final_trace = trace
    return events, final_trace
