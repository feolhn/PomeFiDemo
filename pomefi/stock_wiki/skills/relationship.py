from __future__ import annotations

import json
from typing import Any, Awaitable, Callable

from pomefi.budgets import BudgetLimits
from pomefi.config import KimiConfig
from pomefi.tools.formula import FormulaToolClient

from .common import classify_error, make_skill_result, run_tool_grounded_json_skill

RELATIONSHIP_TOOL_SYSTEM_PROMPT = """
你是行业生态研究专家（Ecosystem Strategy Analyst）。
你的任务是为目标公司构建结构化关系图谱，揭示驱动公司的核心变量。
必须通过 tool_call 获取信息，不要凭空编造。
必须先调用 web_search，再输出证据摘要。
最多只允许 2 次 web_search。
不要为了补细节继续追加第 3 次或第 4 次搜索。

先判断公司的核心行业，再按以下四类关系组织搜索与证据：
- 上游 (supplier): 识别核心成本驱动力。制造类搜原材料/产能；科技类搜芯片/数据/人才；金融类搜资金来源/基准利率。
- 下游 (customer): 识别核心收入来源。B端看大客户集中度；C端看消费信心/渠道；平台类看流量入口。
- 竞争 (competitor): 识别直接对手或颠覆性替代品（如 AI 对传统软件）。
- 关键变量 (theme): 识别对股价影响最大的外部不可控因素。theme 可以是变量、政策、技术路线或关键外部约束，不要求一定是公司实体。
  - 医药：FDA 审批/医保谈判
  - 科技：技术标准/出口限制
  - 周期：大宗商品价格/利率周期
  - 消费：汇率/人口结构/品牌溢价
- theme 最多保留 2 个，只保留当前最影响预期的变量。

搜索时优先覆盖：
- 供应链/上游依赖
- 主要客户与收入集中度
- 竞争格局与市场份额
- 宏观变量与政策变量

只保留最重要、最能影响股价认知的关系，不要把图谱做成百科列表。
""".strip()

RELATIONSHIP_JSON_SYSTEM_PROMPT = """
你是行业生态研究专家（Ecosystem Strategy Analyst）。
必须输出 JSON object，schema:
{
  "summary": "一句话深度洞察",
  "nodes": [{"id":"实体或关键变量","role":"supplier|customer|competitor|theme"}],
  "edges": [{"from":"A","to":"B","relation":"具体的连接语义"}]
}

规则：
- 目标是构建“关系图谱”，不是写公司简介。
- nodes 最多保留 6 个核心节点，优先覆盖：上游、下游、竞争、关键变量。
- 必须包含目标公司本身。
- supplier/customer/competitor/theme 的定义按行业关系逻辑执行。
- Summary 镜像原则：Summary 中提到的任何关键影响因素（如“对华出口限制”“美联储降息”“减重药管线进度”），必须作为独立节点出现在 nodes 中，并通过 related 语义边连接至目标公司。
- Summary 必须回答：该公司的估值逻辑受哪几类关系主导（例如：成本敏感、政策驱动、技术垄断），以及当前最影响预期的单一变量。
- 语义化边：
  - 禁止使用模糊的“related”或“supplies”。
  - 必须使用 2-4 个字的精准动词或短语描述关系。
  - 确保 A -> B 的 relation 在语言上通顺。
- 只写证据支持的关系；不确定就跳过，不要编造市场份额、客户名单或供应链细节。
""".strip()

RELATIONSHIP_JSON_SCHEMA = """
你必须输出 JSON object，schema:
{
  "summary": "一句话深度洞察",
  "nodes": [{"id":"实体或关键变量","role":"supplier|customer|competitor|theme"}],
  "edges": [{"from":"A","to":"B","relation":"具体的连接语义"}]
}
""".strip()

RelationshipEventHandler = Callable[[dict[str, Any]], Any | Awaitable[Any]]


def _parse_final_json(content: str) -> dict[str, Any]:
    loaded = json.loads(str(content or "").strip() or "{}")
    if not isinstance(loaded, dict):
        raise RuntimeError("relationship_json_object_expected")
    return loaded


def _normalize_relation(text: Any) -> str:
    relation = str(text or "").strip()
    if not relation:
        return ""
    relation = relation.replace("->", "").replace("—", "").replace("-", "").strip()
    return relation[:8]


def _infer_role_from_relation(relation: str, *, source_is_company: bool) -> str:
    rel = relation.lower()
    if any(token in rel for token in ["供给", "供货", "供應", "原料", "代工", "降本", "成本", "唯一代工", "核心供给"]):
        return "customer" if source_is_company else "supplier"
    if any(token in rel for token in ["客户", "渠道", "覆盖", "出货", "放量", "贡献增量", "核心外包", "流量入口"]):
        return "customer"
    if any(token in rel for token in ["竞争", "蚕食", "混战", "替代", "压制", "威胁", "对手"]):
        return "competitor"
    return "theme"


def _normalize_graph(
    *,
    company_name: str,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    allowed_roles = {"supplier", "customer", "competitor", "theme"}
    theme_id = str(company_name or "").strip()
    node_map: dict[str, dict[str, Any]] = {}

    for item in nodes:
        node_id = str(item.get("id") or "").strip()
        if not node_id:
            continue
        role = str(item.get("role") or "theme").strip().lower()
        if role not in allowed_roles:
            role = "theme"
        if theme_id and node_id == theme_id:
            role = "theme"
        node_map[node_id] = {"id": node_id, "role": role}

    if theme_id and theme_id not in node_map:
        node_map[theme_id] = {"id": theme_id, "role": "theme"}

    normalized_edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str]] = set()
    for item in edges:
        source_id = str(item.get("from") or "").strip()
        target_id = str(item.get("to") or "").strip()
        relation = _normalize_relation(item.get("relation"))
        if not source_id or not target_id or not relation:
            continue

        if source_id not in node_map:
            node_map[source_id] = {
                "id": source_id,
                "role": _infer_role_from_relation(relation, source_is_company=source_id == theme_id),
            }
        if target_id not in node_map:
            node_map[target_id] = {
                "id": target_id,
                "role": _infer_role_from_relation(relation, source_is_company=source_id == theme_id),
            }
        if theme_id and source_id == theme_id:
            node_map[source_id]["role"] = "theme"
        if theme_id and target_id == theme_id:
            node_map[target_id]["role"] = "theme"

        edge_key = (source_id, target_id, relation)
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)
        normalized_edges.append({"from": source_id, "to": target_id, "relation": relation})

    normalized_nodes = list(node_map.values())[:30]
    allowed_node_ids = {item["id"] for item in normalized_nodes}
    normalized_edges = [
        item
        for item in normalized_edges
        if item["from"] in allowed_node_ids and item["to"] in allowed_node_ids
    ][:40]
    return normalized_nodes, normalized_edges


async def get_relationship(
    symbol: str,
    company_name: str,
    *,
    config: KimiConfig,
    formula_client: FormulaToolClient,
    event_handler: RelationshipEventHandler | None = None,
) -> dict[str, Any]:
    target_name = company_name or symbol
    probe = await run_tool_grounded_json_skill(
        symbol=symbol,
        company_name=target_name,
        config=config,
        formula_client=formula_client,
        tool_system_prompt=RELATIONSHIP_TOOL_SYSTEM_PROMPT,
        tool_user_prompts=[
            (
                f"标的：{target_name}({symbol})。"
                "不要直接回答。必须先判断它的核心行业，再调用 web_search 检索：上游依赖、主要客户/渠道、竞争对手/替代威胁、以及会影响股价的宏观或政策变量。"
                "最多只允许 2 次 web_search，优先把供应链/客户/竞争格局合并进 1-2 次查询里。"
                "拿到搜索结果后立刻输出证据摘要。"
            ),
            (
                f"标的：{target_name}({symbol})。"
                "不要直接回答。必须调用 web_search 至少一次，且最多两次后再输出摘要；若未调用工具，本轮视为失败。不要把结果做成泛泛行业分析。"
            ),
        ],
        json_system_prompt=RELATIONSHIP_JSON_SYSTEM_PROMPT,
        json_user_prompt_builder=lambda evidence_text, _trace: (
            f"标的：{target_name}({symbol})。\n"
            f"{RELATIONSHIP_JSON_SCHEMA}\n"
            "请基于下列 tool-grounded 证据生成 JSON。\n"
            "优先抽取 6 个以内最重要节点，并覆盖：上游、下游、竞争、关键变量。\n"
            "Summary 中提到的关键影响因素必须同步进入 nodes，并通过语义化边连接到目标公司。\n"
            f"{evidence_text}"
        ),
        event_scope="relationship",
        required_tools={"web_search"},
        event_handler=event_handler,
        disable_tool_thinking=True,
        tool_budget_limits=BudgetLimits(
            max_search_calls=2,
            max_tool_iterations=2,
            max_total_turns=3,
        ),
        json_max_completion_tokens=2048,
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
    probe_error = str(probe.get("error") or "")
    if probe_error:
        mapped_error = "relationship_no_tool_calls" if "required_tool_call_missing" in probe_error else probe_error
        data = {
            "symbol": symbol,
            "company_name": target_name,
            "summary": "关系链暂不可得（模型未触发必需工具调用）。",
            "pending": False,
            "nodes": [],
            "edges": [],
            "trace": trace_payload,
        }
        return make_skill_result(
            status="degraded",
            data=data,
            sources=[dict(item) for item in list(probe.get("sources") or []) if isinstance(item, dict)],
            error=mapped_error,
            error_category=classify_error(mapped_error),
            data_ready=False,
            is_critical=False,
        )

    parsed = _parse_final_json(json.dumps(probe.get("content_json") or {}, ensure_ascii=False))
    nodes, edges = _normalize_graph(
        company_name=target_name,
        nodes=[dict(item) for item in list(parsed.get("nodes") or []) if isinstance(item, dict)],
        edges=[dict(item) for item in list(parsed.get("edges") or []) if isinstance(item, dict)],
    )
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
        "trace": trace_payload,
    }
    sources = [dict(item) for item in list(probe.get("sources") or []) if isinstance(item, dict)]
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
