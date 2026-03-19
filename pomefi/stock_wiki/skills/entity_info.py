from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable

from pomefi.config import KimiConfig
from pomefi.stock_wiki.structured import stream_json_object

from .common import classify_error, make_skill_result

ENTITY_INFO_SYSTEM_PROMPT = """
你是资深商业分析师（Equity Research Analyst）。
你的任务是为目标公司生成一份极简、高浓缩的“企业本质”描述。
必须只输出一个 JSON object，不允许输出 markdown。
schema:
{
  "company_name": "string",
  "summary_100cn": "string, 不超过100字",
  "industry": "string",
  "main_business": "string"
}

规则：
- 先判断公司的核心行业，再按行业切换描述重点。
- 高科技/半导体/AI：优先描述核心技术、研发强度、关键客户或应用场景。
- 传统制造/汽车：优先描述生产规模、全球布局、成本/毛利优势、供应链控制力。
- 医药/生物技术：优先描述核心产品或管线、市场地位、关键研发或审批节点。
- 消费/零售：优先描述品牌力、渠道力、用户运营能力、门店或销售网络。
- 金融/银行：优先描述资产规模、资本实力、主要利润来源、业务结构。
- 禁止空话，如“前景广阔”“持续增长”“行业领先”。
- 只写你能确定的内容；不确定就跳过，不要编造精确数字或伪细节。
- summary_100cn 必须回答：它是什么公司、靠什么赚钱、核心壁垒是什么。
- summary_100cn 控制在 2-4 句、100 字内，语气像股票研究摘要，不像百科简介。
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
        "请按 schema 输出 company_name、industry、main_business、summary_100cn。"
        "先判断该公司的核心行业，再按行业叙事维度生成极简企业本质描述。"
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
