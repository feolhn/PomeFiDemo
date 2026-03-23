from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable

from pomefi.config import KimiConfig
from pomefi.stock_wiki.structured import stream_json_object

from .common import classify_error, make_skill_result

ENTITY_INFO_SYSTEM_PROMPT = """
你是资深证券分析师（Senior Equity Research Analyst）。
你的任务是为目标公司生成一份“投资画像”。
重点展示公司的内部护城河、业务本质及在二级市场的身份标签。
必须只输出一个 JSON object，不允许输出 markdown。
schema:
{
  "company_name": "string",
  "industry": "string",
  "main_business": "string",
  "summary_100cn": "string, 不超过100字",
  "investment_tags": ["string"]
}

规则：
- 核心定位：这是公司内部画像，不是外部关系图谱。
- 禁止讨论外部宏观风险、具体供应商名称、具体竞争对手动态；这些属于 relationship 卡片。
- 必须聚焦内部特征：核心技术实力、商业模式、毛利水平、品牌地位、工艺或平台能力。
- 行业适配：
  - 科技：侧重研发壁垒、专利矩阵、软硬一体化能力。
  - 制造：侧重一体化成本、产能规模、工艺领先性。
  - 消费：侧重品牌溢价、渠道密度、用户忠诚度。
  - 医药：侧重平台技术、管线深度、放量周期。
- 标签系统：
  - 指数/身份：如沪深300、上证50、纳指100、标普500。
  - 资金/风格：如北向重仓、高股息、破净股、社保重仓、现金牛。
  - 板块/题材：如BC电池、新质生产力、出海领军、华为链、低空经济。
  - investment_tags 强制提供 4-7 个标签；只写确定标签，不确定就跳过。
- 禁止空话，如“前景广阔”“持续增长”“行业领先”。
- 只写你能确定的内容；不确定就跳过，不要编造精确数字或伪细节。
- summary_100cn 必须回答：它是什么公司、靠什么赚钱、核心壁垒是什么。
- summary_100cn 要像券商深度报告开篇第一段，冷峻、客观、高信息密度。
- summary_100cn 控制在 100 字内。
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
        "请按 schema 输出 company_name、industry、main_business、summary_100cn、investment_tags。"
        "先判断该公司的核心行业，再按内部护城河与市场身份标签生成投资画像。"
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
            "investment_tags": [
                str(item).strip()
                for item in list(payload.get("investment_tags") or [])
                if str(item).strip()
            ][:7],
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
                "investment_tags": [],
            },
            sources=[],
            error=str(exc),
            error_category=classify_error(str(exc)),
            data_ready=False,
            is_critical=False,
        )
