from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# 这是结构化事件日志层。
# 它服务于 debug / 验收，不直接参与业务判断。

EVENT_TYPES = (
    "LLM_REQUEST",
    "LLM_RESPONSE",
    "RAW_TOOL_REQUEST",
    "RAW_TOOL_RESPONSE",
    "ARBITRATION_DECISION",
    "BUDGET_BREAKER",
    "DEGRADE",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EventLogger:
    # EventLogger 只收集事件，不解释事件。
    def __init__(self, *, debug: bool = False):
        self.debug = debug
        self._events: list[dict[str, Any]] = []

    def emit(self, event: str, **payload: Any) -> dict[str, Any]:
        if event not in EVENT_TYPES:
            raise ValueError(f"Unsupported event type: {event}")
        entry = {
            "event": event,
            "timestamp": _now_iso(),
            "payload": payload,
        }
        self._events.append(entry)
        if self.debug:
            print(f"[{event}]", payload)
        return entry

    def snapshot(self) -> list[dict[str, Any]]:
        return list(self._events)

    def filter(self, event: str) -> list[dict[str, Any]]:
        return [item for item in self._events if item["event"] == event]
