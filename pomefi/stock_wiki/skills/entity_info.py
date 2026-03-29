from __future__ import annotations

from typing import Any, Awaitable, Callable

from pomefi.budgets import BudgetLimits
from pomefi.config import KimiConfig
from pomefi.tools.formula import FormulaToolClient

from .common import classify_error, make_skill_result, run_tool_grounded_json_skill

ENTITY_INFO_TOOL_SYSTEM_PROMPT = """
你是资深证券分析师（Senior Equity Research Analyst）。
你的任务是先通过 web_search 获取目标公司的可验证公开信息，再生成“投资画像”。
禁止跳过工具调用，禁止直接凭记忆回答。
最多只允许 2 次 web_search。

检索重点：
- 公司主营业务与产业链位置
- 商业模式与核心收入来源
- 护城河与底层能力（技术、工艺、品牌、渠道、平台、供应链控制力）
- 二级市场常见标签（指数归属、资金风格、核心题材）
- 利润质量与业务结构（哪个业务更赚钱、哪个业务更重投入）

规则：
- 这是公司内部画像，不是外部关系图谱。
- 禁止把外部宏观风险、供应商、竞争对手动态写成主体内容。
- 搜到证据后，输出简短证据摘要，供下一步结构化。
""".strip()

ENTITY_INFO_JSON_SYSTEM_PROMPT = """
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
  "core_competencies": ["string"],
  "profit_analysis": {
    "revenue_structure": "string",
    "profit_tag": "string"
  },
  "investment_tags": ["string"]
}

规则：
- 核心定位：这是公司内部画像，不是外部关系图谱。
- 禁止讨论外部宏观风险、具体供应商名称、具体竞争对手动态；这些属于 relationship 卡片。
- 必须聚焦内部特征：核心技术实力、商业模式、毛利水平、品牌地位、工艺或平台能力。
- 三个字段必须逻辑互补，不得相互复述：
  - summary_100cn：只回答它是谁、在产业链哪一环、核心投资逻辑是什么。禁止写具体业务占比数字。
  - core_competencies：必须是支撑 summary 结论的底层护城河，如专利、工艺、供应链控制力、用户粘性、平台能力。给 1-2 个点，每个点 1-2 句话。
  - profit_analysis：必须解释收入/利润主要由什么业务驱动，哪个业务更赚钱、哪个业务更重投入。没有可靠数字时，只能写相对判断，禁止编具体比例。
- 行业适配：
  - 科技：侧重研发壁垒、专利矩阵、软硬一体化能力。
  - 制造：侧重一体化成本、产能规模、工艺领先性。
  - 消费：侧重品牌溢价、渠道密度、用户忠诚度。
  - 医药：侧重平台技术、管线深度、放量周期。
- 标签系统：
  - 资金/风格：如北向重仓、高股息、社保重仓。
  - 板块/题材：如AI产业链、出海、华为概念、低空经济。
  - investment_tags 强制提供标签。只写确定的标签，不要编造细节。
- profit_analysis.profit_tag 必须是一个短标签，例如：现金奶牛、周期弹性、高研发兑现型、重资本放量期。
- 禁止空话，如“前景广阔”“持续增长”“行业领先”。
- 只写你能确定的内容，不要编造精确数字或伪细节。
- summary_100cn 必须回答：它是什么公司、靠什么赚钱、核心壁垒是什么。
- summary_100cn 要像券商深度报告开篇第一段，冷峻、客观、高信息密度。
- summary_100cn 控制在 100 字内。
""".strip()


async def get_entity_info(
    symbol: str,
    company_name: str,
    *,
    config: KimiConfig,
    formula_client: FormulaToolClient,
    event_handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None = None,
) -> dict[str, Any]:
    target_name = company_name or symbol
    probe = await run_tool_grounded_json_skill(
        symbol=symbol,
        company_name=target_name,
        config=config,
        formula_client=formula_client,
        tool_system_prompt=ENTITY_INFO_TOOL_SYSTEM_PROMPT,
        tool_user_prompts=[
            (
                f"目标公司：{target_name}（{symbol}）。"
                "不要直接回答。先调用 web_search，检索主营业务、产业链位置、护城河、盈利模式与市场标签。"
                "若第一轮证据不足，可补 1 次更聚焦的搜索。"
                "拿到结果后输出简短证据摘要。"
            ),
            (
                f"目标公司：{target_name}（{symbol}）。"
                "不要直接回答。必须调用 web_search 至少一次、至多两次，再输出证据摘要；若未调用工具，本轮视为失败。"
            ),
        ],
        json_system_prompt=ENTITY_INFO_JSON_SYSTEM_PROMPT,
        json_user_prompt_builder=lambda evidence_text, _trace: (
            f"目标公司：{target_name}（{symbol}）。"
            "请按 schema 输出 company_name、industry、main_business、summary_100cn、core_competencies、profit_analysis、investment_tags。"
            "先判断公司的核心行业，再按内部护城河、盈利结构和市场身份标签生成投资画像。\n"
            f"{evidence_text}"
        ),
        event_scope="entity_info",
        required_tools={"web_search"},
        event_handler=event_handler,
        require_first_turn_tool_calls=True,
        disable_tool_thinking=True,
        tool_budget_limits=BudgetLimits(
            max_search_calls=2,
            max_tool_iterations=3,
            max_total_turns=4,
        ),
        json_max_completion_tokens=2048,
    )
    try:
        probe_error = str(probe.get("error") or "")
        if probe_error:
            raise RuntimeError(probe_error)
        payload = dict(probe.get("content_json") or {})
        if not payload:
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
            "core_competencies": [
                str(item).strip()
                for item in list(payload.get("core_competencies") or [])
                if str(item).strip()
            ][:2],
            "profit_analysis": {
                "revenue_structure": str(dict(payload.get("profit_analysis") or {}).get("revenue_structure") or "").strip(),
                "profit_tag": str(dict(payload.get("profit_analysis") or {}).get("profit_tag") or "").strip(),
            },
                "investment_tags": [
                str(item).strip()
                for item in list(payload.get("investment_tags") or [])
                if str(item).strip()
            ][:7],
        }
        sources = [dict(item) for item in list(probe.get("sources") or []) if isinstance(item, dict)]
        if not sources:
            sources = [{"source": "kimi", "kind": "llm", "title": "Entity Info", "published_at": "", "url": None}]
        return make_skill_result(
            status="valid",
            data=data,
            sources=sources,
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
                "core_competencies": [],
                "profit_analysis": {"revenue_structure": "", "profit_tag": ""},
                "investment_tags": [],
            },
            sources=[],
            error=str(exc),
            error_category=classify_error(str(exc)),
            data_ready=False,
            is_critical=False,
        )
