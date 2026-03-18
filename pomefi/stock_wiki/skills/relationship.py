from __future__ import annotations

import json
from typing import Any, Awaitable, Callable

from pomefi.config import KimiConfig
from pomefi.tools.formula import FormulaToolClient

from .common import classify_error, make_skill_result, run_tool_grounded_json_skill

RELATIONSHIP_TOOL_SYSTEM_PROMPT = """
你是产业链研究助手。必须通过 tool_call 获取信息，不要凭空编造。
必须先调用 web_search，再输出证据摘要。
""".strip()

RELATIONSHIP_JSON_SYSTEM_PROMPT = """
你是产业链研究助手。必须输出 JSON object，schema:
{
  "summary": "一句话总结",
  "nodes": [{"id":"公司或实体","role":"supplier|customer|competitor|theme"}],
  "edges": [{"from":"A","to":"B","relation":"supplies|competes|related"}]
}
""".strip()

RelationshipEventHandler = Callable[[dict[str, Any]], Any | Awaitable[Any]]

RELATIONSHIP_JSON_SCHEMA = """
你必须输出 JSON object，schema:
{
  "summary": "一句话总结",
  "nodes": [{"id":"公司或实体","role":"supplier|customer|competitor|theme"}],
  "edges": [{"from":"A","to":"B","relation":"supplies|competes|related"}]
}
""".strip()


def _parse_final_json(content: str) -> dict[str, Any]:
    loaded = json.loads(str(content or "").strip() or "{}")
    if not isinstance(loaded, dict):
        raise RuntimeError("relationship_json_object_expected")
    return loaded


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
                "不要直接回答。必须先调用 web_search 检索主要供应商、客户、竞争对手和产业主题，"
                "再输出证据摘要。"
            ),
            (
                f"标的：{target_name}({symbol})。"
                "不要直接回答。必须调用 web_search 至少一次后再输出摘要；"
                "若未调用工具，本轮视为失败。"
            ),
        ],
        json_system_prompt=RELATIONSHIP_JSON_SYSTEM_PROMPT,
        json_user_prompt_builder=lambda evidence_text, _trace: (
            f"标的：{target_name}({symbol})。\n"
            f"{RELATIONSHIP_JSON_SCHEMA}\n"
            "请基于下列 tool-grounded 证据摘要生成 JSON：\n"
            f"{evidence_text}"
        ),
        event_scope="relationship",
        required_tools={"web_search"},
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
