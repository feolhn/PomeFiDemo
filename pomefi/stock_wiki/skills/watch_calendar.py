from __future__ import annotations

import re
from typing import Any, Awaitable, Callable

from pomefi.config import KimiConfig

from .common import classify_error, make_skill_result, run_tool_grounded_json_skill

WATCH_CALENDAR_TOOL_SYSTEM_PROMPT = """
你是A股日历研究助手。必须先调用 date 再调用 web_search。
必须先完成 tool_call，再输出证据摘要。
禁止跳过工具调用。
""".strip()

WATCH_CALENDAR_JSON_SYSTEM_PROMPT = """
你是A股日历抽取助手。必须输出 JSON object，不要 markdown。
schema:
{
  "today": "YYYY-MM-DD",
  "summary": "string",
  "items": [
    {
      "date": "YYYY-MM-DD",
      "event": "string",
      "source": "string",
      "url": "string",
      "certainty": "high|medium|low"
    }
  ]
}
""".strip()


def _normalize_date(text: str) -> str:
    match = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", str(text or ""))
    if not match:
        return ""
    y, m, d = match.group(1).split("-")
    return f"{y}-{m.zfill(2)}-{d.zfill(2)}"


def _normalize_items(items: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in list(items or [])[:8]:
        if not isinstance(item, dict):
            continue
        event = str(item.get("event") or "").strip()
        if not event:
            continue
        certainty = str(item.get("certainty") or "medium").lower()
        if certainty not in {"high", "medium", "low"}:
            certainty = "medium"
        normalized.append(
            {
                "date": _normalize_date(str(item.get("date") or "")),
                "event": event,
                "source": str(item.get("source") or "web_search"),
                "url": item.get("url"),
                "certainty": certainty,
            }
        )
    return normalized[:5]


async def get_watch_calendar(
    symbol: str,
    company_name: str,
    *,
    config: KimiConfig,
    formula_client: Any,
    event_handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None = None,
) -> dict[str, Any]:
    query_name = company_name or symbol
    probe = await run_tool_grounded_json_skill(
        symbol=symbol,
        company_name=query_name,
        config=config,
        formula_client=formula_client,
        tool_system_prompt=WATCH_CALENDAR_TOOL_SYSTEM_PROMPT,
        tool_user_prompts=[
            (
                f"标的：{query_name}({symbol})。"
                "不要直接回答。必须先调用 date 获取今天日期，再调用 web_search 检索未来一个月财报/发布会/股东大会，"
                "最后输出证据摘要。"
            ),
            (
                f"标的：{query_name}({symbol})。"
                "不要直接回答。必须先后调用 date 和 web_search，再输出摘要；"
                "若未调用工具，本轮视为失败。"
            ),
        ],
        json_system_prompt=WATCH_CALENDAR_JSON_SYSTEM_PROMPT,
        json_user_prompt_builder=lambda evidence_text, _trace: (
            f"标的：{query_name}({symbol})。"
            "基于下列 tool-grounded 证据摘要，抽取未来一个月日历 JSON：\n"
            f"{evidence_text}"
        ),
        event_scope="watch_calendar",
        required_tools={"date", "web_search"},
        event_handler=event_handler,
    )

    trace = dict(probe.get("tool_trace") or {})
    trace_payload = {
        "tool_call_required": True,
        "tool_call_observed": bool(probe.get("tool_call_observed")),
        "retry_count": int(probe.get("retry_count") or 0),
        "observed_tools": list(probe.get("observed_tools") or []),
        "turns": list(trace.get("turns") or []),
        "tool_events": list(trace.get("tool_events") or []),
        "degrade_reason": trace.get("degrade_reason"),
    }
    sources = [dict(item) for item in list(probe.get("sources") or []) if isinstance(item, dict)]

    if probe.get("error"):
        return make_skill_result(
            status="degraded",
            data={
                "symbol": symbol,
                "company_name": company_name,
                "today": "",
                "items": [],
                "summary": "暂未抓到可靠的近期节点。",
                "trace": trace_payload,
            },
            sources=sources,
            error=str(probe.get("error") or "watch_calendar_tool_grounding_failed"),
            error_category=classify_error(str(probe.get("error") or "")),
            data_ready=False,
            is_critical=False,
        )

    payload = dict(probe.get("content_json") or {})
    items = _normalize_items(payload.get("items"))
    summary = str(payload.get("summary") or "").strip()
    today_text = _normalize_date(str(payload.get("today") or ""))
    summary_text = summary or "已提取近期可能影响价格的关键时间点。"
    if not items:
        summary_text = "暂未抓到可靠的近期节点。"

    return make_skill_result(
        status="valid" if items else "degraded",
        data={
            "symbol": symbol,
            "company_name": company_name,
            "today": today_text,
            "items": items,
            "summary": summary_text,
            "trace": trace_payload,
        },
        sources=sources,
        error=None if items else "calendar_empty",
        error_category=None if items else "empty",
        data_ready=bool(items),
        is_critical=False,
    )
