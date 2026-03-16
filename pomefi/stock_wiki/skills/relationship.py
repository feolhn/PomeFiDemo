from __future__ import annotations

import inspect
import json
from typing import Any, Awaitable, Callable

from pomefi.agent.loop import KimiAgentLoop
from pomefi.config import KimiConfig
from pomefi.streaming.events import EVENT_SESSION_DONE, EVENT_SESSION_ERROR, make_event
from pomefi.tools.formula import FormulaToolClient

from .common import classify_error, make_skill_result, parse_formula_content

RelationshipEventHandler = Callable[[dict[str, Any]], Any | Awaitable[Any]]

RELATIONSHIP_SYSTEM_PROMPT = """
你是产业链研究助手。你必须通过 tool_call 获取信息，不要凭空编造。
你必须输出 JSON object，schema:
{
  "summary": "一句话总结",
  "nodes": [{"id":"公司或实体","role":"supplier|customer|competitor|theme"}],
  "edges": [{"from":"A","to":"B","relation":"supplies|competes|related"}]
}
""".strip()


async def _maybe_emit(handler: RelationshipEventHandler | None, event: dict[str, Any]) -> None:
    if handler is None:
        return
    result = handler(event)
    if inspect.isawaitable(result):
        await result


def _extract_sources_from_trace(trace: dict[str, Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for event in list(trace.get("tool_events") or []):
        if str(event.get("tool_name") or "") != "web_search":
            continue
        rows = parse_formula_content(str(event.get("tool_content") or ""))
        for row in rows[:3]:
            sources.append(
                {
                    "source": str(row.get("source") or "web_search"),
                    "kind": "web_search",
                    "title": str(row.get("title") or row.get("key_claim") or ""),
                    "published_at": str(row.get("published_at") or ""),
                    "url": row.get("url"),
                }
            )
    return sources


def _parse_final_json(content: str) -> dict[str, Any]:
    loaded = json.loads(str(content or "").strip() or "{}")
    if not isinstance(loaded, dict):
        raise RuntimeError("relationship_json_object_expected")
    return loaded


def _has_required_tool_call(trace: dict[str, Any]) -> bool:
    turns = list(trace.get("turns") or [])
    first_turn = turns[0] if turns else {}
    if not bool(first_turn.get("has_tool_calls")):
        return False
    tool_events = list(trace.get("tool_events") or [])
    return any(str(item.get("tool_name") or "") == "web_search" for item in tool_events)


async def _run_relationship_attempt(
    *,
    symbol: str,
    target_name: str,
    config: KimiConfig,
    formula_client: FormulaToolClient,
    event_handler: RelationshipEventHandler | None,
    user_prompt: str,
    attempt: int,
) -> dict[str, Any]:
    agent = KimiAgentLoop(config=config, formula_client=formula_client)
    trace: dict[str, Any] | None = None
    try:
        async for event in agent.run_conversation_trace_stream(
            user_prompt=user_prompt,
            system_prompt=RELATIONSHIP_SYSTEM_PROMPT,
            response_format={"type": "json_object"},
            local_tools=[],
            local_tool_handlers={},
        ):
            await _maybe_emit(
                event_handler,
                make_event("relationship_event", attempt=attempt, event=event),
            )
            if event.get("type") == EVENT_SESSION_DONE:
                maybe_trace = event.get("trace")
                if isinstance(maybe_trace, dict):
                    trace = maybe_trace
            if event.get("type") == EVENT_SESSION_ERROR:
                raise RuntimeError(str(event.get("error") or "relationship_session_error"))
    finally:
        await agent.aclose()

    if trace is None:
        raise RuntimeError("relationship_trace_missing")
    return trace


async def get_relationship(
    symbol: str,
    company_name: str,
    *,
    config: KimiConfig,
    formula_client: FormulaToolClient,
    event_handler: RelationshipEventHandler | None = None,
) -> dict[str, Any]:
    target_name = company_name or symbol
    prompts = [
        (
            f"标的：{target_name}({symbol})。"
            "请先调用 web_search 检索其主要供应商、客户、竞争对手，并补一轮相关题材重合度，再输出 JSON。"
        ),
        (
            f"标的：{target_name}({symbol})。"
            "不要直接回答。必须先调用 web_search 工具至少一次，再输出 JSON。"
            "若未调用工具，本次回答视为失败。"
        ),
    ]

    trace: dict[str, Any] | None = None
    tool_call_observed = False
    retry_count = 0
    last_error = ""

    for attempt, prompt in enumerate(prompts, start=1):
        trace = await _run_relationship_attempt(
            symbol=symbol,
            target_name=target_name,
            config=config,
            formula_client=formula_client,
            event_handler=event_handler,
            user_prompt=prompt,
            attempt=attempt,
        )
        tool_call_observed = _has_required_tool_call(trace)
        if tool_call_observed:
            retry_count = attempt - 1
            break
        last_error = "relationship_no_tool_calls"
        retry_count = attempt
        if attempt < len(prompts):
            await _maybe_emit(
                event_handler,
                make_event(
                    "relationship_retry",
                    attempt=attempt + 1,
                    reason="first_attempt_missing_tool_call",
                ),
            )

    if trace is None:
        raise RuntimeError("relationship_trace_missing")

    if not tool_call_observed:
        data = {
            "symbol": symbol,
            "company_name": target_name,
            "summary": "关系链暂不可得（模型未触发必需工具调用）。",
            "pending": False,
            "nodes": [],
            "edges": [],
            "trace": {
                "tool_call_required": True,
                "tool_call_observed": False,
                "retry_count": retry_count,
                "turns": trace.get("turns") or [],
                "tool_events": trace.get("tool_events") or [],
                "degrade_reason": trace.get("degrade_reason"),
            },
        }
        return make_skill_result(
            status="degraded",
            data=data,
            sources=[],
            error=last_error,
            error_category="tool",
            data_ready=False,
            is_critical=False,
        )

    parsed = _parse_final_json(str(trace.get("final_content") or ""))
    nodes = [dict(item) for item in list(parsed.get("nodes") or []) if isinstance(item, dict)][:20]
    edges = [dict(item) for item in list(parsed.get("edges") or []) if isinstance(item, dict)][:30]
    summary = str(parsed.get("summary") or "").strip()
    if not summary:
        summary = f"{target_name} 的产业关系仍在补全，建议结合最新公告继续验证。"

    data = {
        "symbol": symbol,
        "company_name": target_name,
        "summary": summary,
        "pending": False,
        "nodes": nodes,
        "edges": edges,
        "trace": {
            "tool_call_required": True,
            "tool_call_observed": True,
            "retry_count": retry_count,
            "turns": trace.get("turns") or [],
            "tool_events": trace.get("tool_events") or [],
            "degrade_reason": trace.get("degrade_reason"),
        },
    }
    sources = _extract_sources_from_trace(trace)
    status = "valid" if data["nodes"] or data["edges"] else "degraded"
    error_text = str(trace.get("degrade_reason") or "") if trace.get("degrade_reason") else None
    return make_skill_result(
        status=status,
        data=data,
        sources=sources,
        error=error_text,
        error_category=classify_error(error_text) if error_text else None,
        data_ready=bool(data["nodes"] or data["edges"]),
        is_critical=False,
    )
