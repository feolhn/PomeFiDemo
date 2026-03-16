from __future__ import annotations

import inspect
import json
import re
from typing import Any, Awaitable, Callable

from pomefi.config import KimiConfig
from pomefi.stock_wiki.structured import stream_json_object

from .common import classify_error, make_skill_result

WATCH_CALENDAR_SYSTEM_PROMPT = """
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
    today_text = ""
    try:
        date_result = await formula_client.call_tool(
            "moonshot/date:latest",
            {"name": "date", "arguments": "{}"},
        )
        today_text = _normalize_date(str(date_result.get("content") or ""))
    except Exception:
        today_text = ""

    try:
        search_result = await formula_client.call_tool(
            "moonshot/web-search:latest",
            {
                "name": "web_search",
                "arguments": json.dumps(
                    {"query": f"{query_name} 财报 发布会 股东大会 未来一个月"},
                    ensure_ascii=False,
                ),
            },
        )
        raw_search_content = str(search_result.get("content") or "")
        payload: dict[str, Any] | None = None
        async for event in stream_json_object(
            config=config,
            system_prompt=WATCH_CALENDAR_SYSTEM_PROMPT,
            user_prompt=(
                f"标的：{query_name}({symbol})。今天：{today_text or '未知'}。"
                "根据下列检索结果抽取未来一个月的重要日历事件：\n"
                f"{raw_search_content}"
            ),
            event_scope="watch_calendar",
        ):
            if event_handler is not None:
                maybe_result = event_handler(event)
                if inspect.isawaitable(maybe_result):
                    await maybe_result
            if event.get("type") == "structured_json_done":
                maybe_payload = event.get("json")
                if isinstance(maybe_payload, dict):
                    payload = maybe_payload
        if payload is None:
            raise RuntimeError("watch_calendar_json_missing")
        items = _normalize_items(payload.get("items"))
        summary = str(payload.get("summary") or "").strip()
        today_from_llm = _normalize_date(str(payload.get("today") or ""))
        if today_from_llm:
            today_text = today_from_llm
    except Exception as exc:
        return make_skill_result(
            status="error",
            data={"symbol": symbol, "company_name": company_name, "today": today_text, "items": [], "summary": ""},
            sources=[],
            error=str(exc),
            error_category=classify_error(str(exc)),
            data_ready=False,
            is_critical=True,
        )

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
        },
        sources=[
            {
                "source": item.get("source") or "web_search",
                "kind": "web_search",
                "title": item.get("event") or "",
                "published_at": item.get("date") or "",
                "url": item.get("url"),
            }
            for item in items
        ],
        error=None if items else "calendar_empty",
        error_category=None if items else "empty",
        data_ready=bool(items),
        is_critical=True,
    )
