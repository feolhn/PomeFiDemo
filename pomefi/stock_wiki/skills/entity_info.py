from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable

from pomefi.config import KimiConfig
from pomefi.stock_wiki.structured import stream_json_object

from .common import classify_error, make_skill_result

ENTITY_INFO_SYSTEM_PROMPT = """
你是A股公司研究助手。必须只输出一个 JSON object，不允许输出 markdown。
schema:
{
  "company_name": "string",
  "summary_100cn": "string, 不超过100字",
  "industry": "string",
  "main_business": "string"
}
""".strip()

async def _emit_event(
    handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None,
    event: dict[str, Any],
) -> None:
    if handler is None:
        return
    result = handler(event)
    if inspect.isawaitable(result):
        await result


async def get_entity_info(
    symbol: str,
    company_name: str,
    *,
    config: KimiConfig,
    event_handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None = None,
) -> dict[str, Any]:
    target_name = company_name or symbol
    prompt = (
        f"目标公司：{target_name}（{symbol}）。"
        "请按 schema 输出公司名、行业、主营业务和100字以内摘要。"
    )
    try:
        payload: dict[str, Any] | None = None
        async for event in stream_json_object(
            config=config,
            system_prompt=ENTITY_INFO_SYSTEM_PROMPT,
            user_prompt=prompt,
            event_scope="entity_info",
        ):
            await _emit_event(event_handler, event)
            if event.get("type") == "structured_json_done":
                maybe_payload = event.get("json")
                if isinstance(maybe_payload, dict):
                    payload = maybe_payload
        if payload is None:
            raise RuntimeError("entity_info_json_missing")
        normalized_name = str(payload.get("company_name") or target_name).strip() or target_name
        summary = str(payload.get("summary_100cn") or "").strip()
        if not summary:
            summary = f"{normalized_name} 是 A 股上市公司，当前未获取到更完整实体介绍。"
        data = {
            "symbol": symbol,
            "company_name": normalized_name,
            "industry": str(payload.get("industry") or "").strip(),
            "main_business": str(payload.get("main_business") or "").strip(),
            "summary_100cn": summary,
            "summary": summary,
        }
        return make_skill_result(
            status="valid",
            data=data,
            sources=[{"source": "kimi", "kind": "llm", "title": "Entity Info", "published_at": "", "url": None}],
            error=None,
            data_ready=True,
            is_critical=False,
        )
    except Exception as exc:
        return make_skill_result(
            status="degraded",
            data={
                "symbol": symbol,
                "company_name": target_name,
                "industry": "",
                "main_business": "",
                "summary_100cn": f"{target_name} 是 A 股上市公司，当前未获取到更完整实体介绍。",
                "summary": f"{target_name} 是 A 股上市公司，当前未获取到更完整实体介绍。",
            },
            sources=[],
            error=str(exc),
            error_category=classify_error(str(exc)),
            data_ready=False,
            is_critical=False,
        )
