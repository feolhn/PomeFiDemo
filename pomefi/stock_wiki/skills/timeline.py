from __future__ import annotations

import asyncio
import inspect
import json
import re
from typing import Any, Awaitable, Callable

from pomefi.config import KimiConfig
from pomefi.stock_wiki.structured import stream_json_object
from pomefi.tools.akshare_tool import get_cached_price_history

from .common import classify_error, make_skill_result

TIMELINE_SYSTEM_PROMPT = """
你是A股事件抽取助手。必须输出 JSON object，不要 markdown。
schema:
{
  "summary": "string",
  "events": [
    {"date":"YYYY-MM-DD","title":"string","source":"string","url":"string"}
  ],
  "merge_notes": "string"
}
""".strip()


def _load_price_rows(symbol: str) -> list[dict[str, Any]]:
    history_df = get_cached_price_history(symbol)
    if history_df.empty:
        return []
    history_df = history_df.rename(columns={"日期": "date", "收盘": "close"})
    history_df["date"] = history_df["date"].astype(str)
    rows: list[dict[str, Any]] = []
    for row in history_df[["date", "close"]].to_dict(orient="records"):
        rows.append({"date": str(row.get("date") or ""), "close": row.get("close"), "event_desc": ""})
    return rows[-90:]


def _extract_date_text(text: str) -> str:
    raw = str(text or "")
    match = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", raw)
    if match:
        y, m, d = match.group(1).split("-")
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    return ""


def _normalize_events(events: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for event in list(events or [])[:10]:
        if not isinstance(event, dict):
            continue
        title = str(event.get("title") or "").strip()
        if not title:
            continue
        date_text = _extract_date_text(str(event.get("date") or ""))
        normalized.append(
            {
                "date": date_text,
                "title": title,
                "source": str(event.get("source") or "web_search"),
                "url": event.get("url"),
            }
        )
    return normalized


def _merge_events(price_rows: list[dict[str, Any]], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not price_rows or not events:
        return price_rows
    event_map: dict[str, list[str]] = {}
    for item in events[:8]:
        title = str(item.get("title") or "").strip()
        date_text = _extract_date_text(str(item.get("date") or ""))
        if not title or not date_text:
            continue
        event_map.setdefault(date_text, []).append(title)

    merged: list[dict[str, Any]] = []
    for row in price_rows:
        date_text = str(row.get("date") or "")
        normalized = _extract_date_text(date_text) or date_text[:10]
        descriptions = event_map.get(normalized, [])
        merged.append(
            {
                "date": date_text[:10],
                "close": row.get("close"),
                "event_desc": "；".join(descriptions[:2]),
            }
        )
    return merged


async def get_timeline(
    symbol: str,
    company_name: str,
    *,
    config: KimiConfig,
    formula_client: Any,
    event_handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None = None,
) -> dict[str, Any]:
    source_name = company_name or symbol
    try:
        price_rows = await asyncio.to_thread(_load_price_rows, symbol)
    except Exception as exc:
        return make_skill_result(
            status="error",
            data={"symbol": symbol, "company_name": company_name, "series": [], "events": []},
            sources=[],
            error=f"price_fetch_failed: {exc}",
            error_category=classify_error(str(exc)),
            data_ready=False,
            is_critical=True,
        )

    sources: list[dict[str, Any]] = [
        {"source": "AkShare", "kind": "akshare", "title": f"{symbol} 近三个月K线", "published_at": "", "url": None}
    ]
    events: list[dict[str, Any]] = []
    merge_notes = ""
    summary = "已将近三个月价格序列与公开事件做日期叠加。"
    try:
        search_result = await formula_client.call_tool(
            "moonshot/web-search:latest",
            {
                "name": "web_search",
                "arguments": json.dumps(
                    {"query": f"{source_name} 近三个月 重大事件 公告"},
                    ensure_ascii=False,
                ),
            },
        )
        raw_search_content = str(search_result.get("content") or "")
        payload: dict[str, Any] | None = None
        async for event in stream_json_object(
            config=config,
            system_prompt=TIMELINE_SYSTEM_PROMPT,
            user_prompt=(
                f"标的：{source_name}({symbol})。"
                "基于以下检索结果抽取时间线事件，保证 events 的 date 字段尽量是 YYYY-MM-DD：\n"
                f"{raw_search_content}"
            ),
            event_scope="timeline",
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
            raise RuntimeError("timeline_json_missing")
        events = _normalize_events(payload.get("events"))
        summary = str(payload.get("summary") or summary).strip() or summary
        merge_notes = str(payload.get("merge_notes") or "").strip()
    except Exception as exc:
        return make_skill_result(
            status="degraded",
            data={
                "symbol": symbol,
                "company_name": company_name,
                "series": price_rows,
                "events": [],
                "summary": "未能完成事件抽取，先返回价格序列。",
                "merge_notes": "",
            },
            sources=sources,
            error=str(exc),
            error_category=classify_error(str(exc)),
            data_ready=bool(price_rows),
            is_critical=True,
        )

    for item in events[:5]:
        sources.append(
            {
                "source": item.get("source") or "web_search",
                "kind": "web_search",
                "title": item.get("title") or "",
                "published_at": item.get("date") or "",
                "url": item.get("url"),
            }
        )

    merged_rows = _merge_events(price_rows, events)
    status = "valid" if merged_rows else "degraded"
    return make_skill_result(
        status=status,
        data={
            "symbol": symbol,
            "company_name": company_name,
            "series": merged_rows,
            "events": events[:8],
            "summary": summary,
            "merge_notes": merge_notes,
        },
        sources=sources,
        error=None if merged_rows else "timeline_empty",
        error_category="empty" if not merged_rows else None,
        data_ready=bool(merged_rows),
        is_critical=True,
    )
