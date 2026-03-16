from __future__ import annotations

from typing import Any

EVENT_SESSION_START = "session_start"
EVENT_SESSION_DONE = "session_done"
EVENT_SESSION_ERROR = "session_error"
EVENT_SKILL_START = "skill_start"
EVENT_SKILL_DONE = "skill_done"
EVENT_LLM_REASONING_DELTA = "llm_reasoning_delta"
EVENT_LLM_CONTENT_DELTA = "llm_content_delta"
EVENT_TOOL_CALL = "tool_call"
EVENT_TOOL_RESULT = "tool_result"


def make_event(event_type: str, **payload: Any) -> dict[str, Any]:
    return {"type": event_type, **payload}
