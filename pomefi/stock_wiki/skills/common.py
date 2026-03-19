from __future__ import annotations

import inspect
import json
import re
import time
from typing import Any

from pomefi.agent.loop import KimiAgentLoop
from pomefi.budgets import BudgetLimits, BudgetTracker
from pomefi.stock_wiki.structured import stream_json_object

def classify_error(error: str | None) -> str:
    text = str(error or "").lower()
    if not text:
        return "unknown"
    if any(token in text for token in ("proxyerror", "connection", "timed out", "timeout", "httpsconnectionpool")):
        return "network"
    if any(token in text for token in ("rate", "too many", "429", "forbidden", "blocked")):
        return "rate_limit"
    if "empty" in text or "not found" in text:
        return "empty"
    if "json" in text or "schema" in text or "parse" in text:
        return "schema"
    if "tool" in text:
        return "tool"
    return "unknown"


def make_skill_result(
    *,
    status: str,
    data: dict[str, Any] | None = None,
    sources: list[dict[str, Any]] | None = None,
    error: str | None = None,
    error_category: str | None = None,
    data_ready: bool | None = None,
    is_critical: bool = False,
) -> dict[str, Any]:
    if error_category is None and error:
        error_category = classify_error(error)
    return {
        "status": status,
        "data": dict(data or {}),
        "sources": list(sources or []),
        "error": error,
        "error_category": error_category,
        "data_ready": data_ready,
        "is_critical": bool(is_critical),
    }


def parse_formula_content(content: str) -> list[dict[str, Any]]:
    text = str(content or "").strip()
    if not text:
        return []
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        return []

    if isinstance(loaded, list):
        return [dict(item) for item in loaded if isinstance(item, dict)]

    if isinstance(loaded, dict):
        for key in ("items", "results", "data"):
            value = loaded.get(key)
            if isinstance(value, list):
                return [dict(item) for item in value if isinstance(item, dict)]
        return [loaded]

    return []


async def _emit_event(handler: Any, event: dict[str, Any]) -> None:
    if handler is None:
        return
    result = handler(event)
    if inspect.isawaitable(result):
        await result


def _has_required_tool_call(
    trace: dict[str, Any],
    *,
    required_tools: set[str],
    require_first_turn_tool_calls: bool,
) -> tuple[bool, bool, set[str]]:
    turns = list(trace.get("turns") or [])
    first_turn = turns[0] if turns else {}
    first_turn_has_tool_calls = bool(first_turn.get("has_tool_calls"))
    observed_tools = {
        str(item.get("tool_name") or "")
        for item in list(trace.get("tool_events") or [])
        if str(item.get("tool_name") or "")
    }
    required_hit = required_tools.issubset(observed_tools)
    if require_first_turn_tool_calls and not first_turn_has_tool_calls:
        return False, first_turn_has_tool_calls, observed_tools
    return required_hit, first_turn_has_tool_calls, observed_tools


def _extract_iso_date(text: str) -> str:
    match = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", str(text or ""))
    if not match:
        return ""
    y, m, d = match.group(1).split("-")
    return f"{y}-{m.zfill(2)}-{d.zfill(2)}"


def build_sources_from_tool_trace(trace: dict[str, Any], *, limit: int = 5) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for event in list(trace.get("tool_events") or []):
        if not isinstance(event, dict):
            continue
        tool_name = str(event.get("tool_name") or "")
        tool_content = str(event.get("tool_content") or "")
        if tool_name == "date":
            date_text = _extract_iso_date(tool_content)
            key = ("date", "date", date_text)
            if key in seen:
                continue
            seen.add(key)
            sources.append(
                {
                    "source": "date",
                    "kind": "date",
                    "title": "当前日期",
                    "published_at": date_text,
                    "url": None,
                }
            )
            continue

        if tool_name != "web_search":
            continue

        rows = parse_formula_content(tool_content)
        if rows:
            for row in rows[:3]:
                title = str(row.get("title") or row.get("key_claim") or "web_search result").strip()
                published_at = str(row.get("published_at") or row.get("date") or "").strip()
                source_name = str(row.get("source") or "web_search").strip()
                key = (tool_name, title, published_at)
                if key in seen:
                    continue
                seen.add(key)
                sources.append(
                    {
                        "source": source_name,
                        "kind": "web_search",
                        "title": title,
                        "published_at": published_at,
                        "url": row.get("url"),
                    }
                )
                if len(sources) >= limit:
                    return sources
        else:
            preview = str(event.get("tool_content_preview") or "").strip()
            key = (tool_name, preview[:80], "")
            if key in seen:
                continue
            seen.add(key)
            sources.append(
                {
                    "source": "web_search",
                    "kind": "web_search",
                    "title": "Web Search Evidence",
                    "published_at": "",
                    "url": None,
                }
            )
            if len(sources) >= limit:
                return sources
    return sources[:limit]


def build_tool_grounded_evidence(trace: dict[str, Any]) -> str:
    parts: list[str] = []
    final_content = str(trace.get("final_content") or "").strip()
    if final_content:
        parts.append(f"assistant_summary: {final_content}")
    for event in list(trace.get("tool_events") or [])[:6]:
        if not isinstance(event, dict):
            continue
        name = str(event.get("tool_name") or "")
        preview = str(event.get("tool_content_preview") or "").strip()
        if not name:
            continue
        if preview.startswith("----MOONSHOT ENCRYPTED BEGIN----"):
            parts.append(f"tool={name}")
        elif preview:
            parts.append(f"tool={name} preview={preview}")
        else:
            parts.append(f"tool={name}")
    return "\n".join(parts).strip()


async def run_tool_grounded_json_skill(
    *,
    symbol: str,
    company_name: str,
    config: Any,
    formula_client: Any,
    tool_system_prompt: str,
    tool_user_prompts: list[str],
    json_system_prompt: str,
    json_user_prompt_builder: Any,
    event_scope: str,
    required_tools: set[str],
    event_handler: Any = None,
    require_first_turn_tool_calls: bool = True,
    disable_tool_thinking: bool = False,
    tool_budget_limits: BudgetLimits | None = None,
    json_max_completion_tokens: int = 4096,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace: dict[str, Any] | None = None
    tool_call_observed = False
    observed_tools: set[str] = set()
    retry_count = 0
    last_error = ""

    prompts = [str(item or "").strip() for item in tool_user_prompts if str(item or "").strip()]
    if not prompts:
        raise RuntimeError("tool_user_prompts is empty")

    for attempt, prompt in enumerate(prompts, start=1):
        trace = None
        agent = KimiAgentLoop(config=config, formula_client=formula_client)
        budget_tracker = BudgetTracker(tool_budget_limits) if tool_budget_limits is not None else None
        try:
            async for event in agent.run_conversation_trace_stream(
                user_prompt=prompt,
                system_prompt=tool_system_prompt,
                local_tools=[],
                local_tool_handlers={},
                disable_thinking=disable_tool_thinking,
                budget_tracker=budget_tracker,
            ):
                await _emit_event(event_handler, event)
                event_type = str(event.get("type") or "")
                if event_type == "session_done":
                    maybe_trace = event.get("trace")
                    if isinstance(maybe_trace, dict):
                        trace = maybe_trace
                elif event_type == "session_error":
                    raise RuntimeError(str(event.get("error") or f"{event_scope}_session_error"))
        finally:
            await agent.aclose()

        if trace is None:
            last_error = f"{event_scope}_trace_missing"
            retry_count = attempt
        else:
            tool_call_observed, _first_turn, observed_tools = _has_required_tool_call(
                trace,
                required_tools=required_tools,
                require_first_turn_tool_calls=require_first_turn_tool_calls,
            )
            if tool_call_observed:
                retry_count = attempt - 1
                break
            last_error = f"{event_scope}_required_tool_call_missing"
            retry_count = attempt

        if attempt < len(prompts):
            await _emit_event(
                event_handler,
                {
                    "type": "tool_grounded_retry",
                    "scope": event_scope,
                    "attempt": attempt + 1,
                    "reason": last_error,
                },
            )

    latency_ms = max(int((time.perf_counter() - started) * 1000), 0)
    if trace is None:
        return {
            "content_json": None,
            "tool_trace": {},
            "sources": [],
            "error": last_error or f"{event_scope}_trace_missing",
            "latency_ms": latency_ms,
            "retry_count": retry_count,
            "tool_call_observed": False,
            "observed_tools": [],
        }
    if not tool_call_observed:
        return {
            "content_json": None,
            "tool_trace": trace,
            "sources": build_sources_from_tool_trace(trace),
            "error": last_error or f"{event_scope}_required_tool_call_missing",
            "latency_ms": latency_ms,
            "retry_count": retry_count,
            "tool_call_observed": False,
            "observed_tools": sorted(observed_tools),
        }

    evidence_text = build_tool_grounded_evidence(trace)
    if not evidence_text:
        evidence_text = f"{company_name or symbol} tool evidence unavailable."
    user_prompt = json_user_prompt_builder(evidence_text, trace)

    structured_payload: dict[str, Any] | None = None
    try:
        async for event in stream_json_object(
            config=config,
            system_prompt=json_system_prompt,
            user_prompt=user_prompt,
            event_scope=f"{event_scope}_json",
            max_completion_tokens=json_max_completion_tokens,
        ):
            await _emit_event(event_handler, event)
            if event.get("type") == "structured_json_done":
                maybe_payload = event.get("json")
                if isinstance(maybe_payload, dict):
                    structured_payload = maybe_payload
    except Exception as exc:
        return {
            "content_json": None,
            "tool_trace": trace,
            "sources": build_sources_from_tool_trace(trace),
            "error": str(exc),
            "latency_ms": latency_ms,
            "retry_count": retry_count,
            "tool_call_observed": True,
            "observed_tools": sorted(observed_tools),
        }

    if structured_payload is None:
        return {
            "content_json": None,
            "tool_trace": trace,
            "sources": build_sources_from_tool_trace(trace),
            "error": f"{event_scope}_json_missing",
            "latency_ms": latency_ms,
            "retry_count": retry_count,
            "tool_call_observed": True,
            "observed_tools": sorted(observed_tools),
        }

    return {
        "content_json": structured_payload,
        "tool_trace": trace,
        "sources": build_sources_from_tool_trace(trace),
        "error": None,
        "latency_ms": latency_ms,
        "retry_count": retry_count,
        "tool_call_observed": True,
        "observed_tools": sorted(observed_tools),
    }


async def run_tool_grounded_json_direct(
    *,
    symbol: str,
    company_name: str,
    config: Any,
    formula_client: Any,
    tool_system_prompt: str,
    tool_user_prompts: list[str],
    event_scope: str,
    required_tools: set[str],
    event_handler: Any = None,
    require_first_turn_tool_calls: bool = True,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace: dict[str, Any] | None = None
    content_json: dict[str, Any] | None = None
    tool_call_observed = False
    observed_tools: set[str] = set()
    retry_count = 0
    last_error = ""

    prompts = [str(item or "").strip() for item in tool_user_prompts if str(item or "").strip()]
    if not prompts:
        raise RuntimeError("tool_user_prompts is empty")

    for attempt, prompt in enumerate(prompts, start=1):
        trace = None
        content_json = None
        agent = KimiAgentLoop(config=config, formula_client=formula_client)
        try:
            async for event in agent.run_conversation_trace_stream(
                user_prompt=prompt,
                system_prompt=tool_system_prompt,
                response_format={"type": "json_object"},
                local_tools=[],
                local_tool_handlers={},
            ):
                await _emit_event(event_handler, event)
                event_type = str(event.get("type") or "")
                if event_type == "session_done":
                    maybe_trace = event.get("trace")
                    if isinstance(maybe_trace, dict):
                        trace = maybe_trace
                elif event_type == "session_error":
                    raise RuntimeError(str(event.get("error") or f"{event_scope}_session_error"))
        finally:
            await agent.aclose()

        if trace is None:
            last_error = f"{event_scope}_trace_missing"
            retry_count = attempt
        else:
            tool_call_observed, _first_turn, observed_tools = _has_required_tool_call(
                trace,
                required_tools=required_tools,
                require_first_turn_tool_calls=require_first_turn_tool_calls,
            )
            if not tool_call_observed:
                last_error = f"{event_scope}_required_tool_call_missing"
                retry_count = attempt
            else:
                final_content = str(trace.get("final_content") or "").strip()
                if not final_content:
                    last_error = f"{event_scope}_json_missing"
                    retry_count = attempt
                else:
                    try:
                        loaded = json.loads(final_content)
                    except json.JSONDecodeError:
                        last_error = f"{event_scope}_json_parse_failed"
                        retry_count = attempt
                    else:
                        if not isinstance(loaded, dict):
                            last_error = f"{event_scope}_json_object_expected"
                            retry_count = attempt
                        else:
                            content_json = loaded
                            retry_count = attempt - 1
                            break

        if attempt < len(prompts):
            await _emit_event(
                event_handler,
                {
                    "type": "tool_grounded_retry",
                    "scope": event_scope,
                    "attempt": attempt + 1,
                    "reason": last_error,
                },
            )

    latency_ms = max(int((time.perf_counter() - started) * 1000), 0)
    if trace is None:
        return {
            "content_json": None,
            "tool_trace": {},
            "sources": [],
            "error": last_error or f"{event_scope}_trace_missing",
            "latency_ms": latency_ms,
            "retry_count": retry_count,
            "tool_call_observed": False,
            "observed_tools": [],
        }
    if not tool_call_observed:
        return {
            "content_json": None,
            "tool_trace": trace,
            "sources": build_sources_from_tool_trace(trace),
            "error": last_error or f"{event_scope}_required_tool_call_missing",
            "latency_ms": latency_ms,
            "retry_count": retry_count,
            "tool_call_observed": False,
            "observed_tools": sorted(observed_tools),
        }
    if content_json is None:
        return {
            "content_json": None,
            "tool_trace": trace,
            "sources": build_sources_from_tool_trace(trace),
            "error": last_error or f"{event_scope}_json_missing",
            "latency_ms": latency_ms,
            "retry_count": retry_count,
            "tool_call_observed": True,
            "observed_tools": sorted(observed_tools),
        }

    return {
        "content_json": content_json,
        "tool_trace": trace,
        "sources": build_sources_from_tool_trace(trace),
        "error": None,
        "latency_ms": latency_ms,
        "retry_count": retry_count,
        "tool_call_observed": True,
        "observed_tools": sorted(observed_tools),
    }
