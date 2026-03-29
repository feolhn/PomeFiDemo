from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

CRITICAL_SKILLS = ("timeline",)

FAILURE_REASON_MESSAGES = {
    "ROUTING_UNRESOLVED": "路由失败：未解析到可分析的A股标的。",
    "AKSHARE_NETWORK_UNRECOVERED": "核心行情链路未恢复：AkShare 网络请求失败且无可用回退数据。",
    "TIMELINE_TIMEOUT_UNRECOVERED": "时间线链路未恢复：timeline 在超时后仍无可用序列。",
    "TIMELINE_EVENTS_UNRECOVERED": "时间线链路未恢复：过去事件支路未成功返回可用事件。",
    "KIMI_TIMEOUT_UNRECOVERED": "模型链路未恢复：Kimi 调用超时且未恢复。",
    "TOOL_CALL_MISSING_UNRECOVERED": "工具调用链路未恢复：必需 tool_call 缺失。",
    "UNKNOWN_UNRECOVERED": "链路未恢复：出现未知错误，请查看 failure_evidence。",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compute_failure_mask(skill_results: dict[str, dict[str, Any]]) -> tuple[dict[str, str], list[str]]:
    failure_mask: dict[str, str] = {}
    critical_failures: list[str] = []
    for skill, result in skill_results.items():
        item = dict(result or {})
        status = str(item.get("status") or "")
        data_ready = item.get("data_ready")
        if data_ready is None:
            data_ready = status == "valid"
        is_failure = status == "error" or data_ready is False
        if skill not in CRITICAL_SKILLS or not is_failure:
            continue
        data = dict(item.get("data") or {})
        data_origin = str(data.get("data_origin") or "")
        error_category = str(item.get("error_category") or "")
        if error_category == "network":
            reason = "network_live_failed_cache_hit" if data_origin == "cache_fallback" else "network_live_failed_cache_miss"
        else:
            reason = str(item.get("error") or error_category or status or "failed")
        failure_mask[skill] = reason
        critical_failures.append(skill)
    return failure_mask, critical_failures


def _map_failure_code(skill: str, result: dict[str, Any]) -> str:
    data = dict(result.get("data") or {})
    explicit = str(data.get("unrecovered_reason_code") or "").strip()
    if explicit:
        return explicit

    error = str(result.get("error") or "").strip().lower()
    error_category = str(result.get("error_category") or "").strip().lower()

    if "required_tool_call_missing" in error or error_category == "tool":
        return "TOOL_CALL_MISSING_UNRECOVERED"
    if "timeout_soft_" in error or error_category == "timeout":
        if skill == "timeline":
            return "TIMELINE_TIMEOUT_UNRECOVERED"
        return "KIMI_TIMEOUT_UNRECOVERED"
    if "network" in error or "proxyerror" in error or "httpsconnectionpool" in error:
        return "UNKNOWN_UNRECOVERED"
    return "UNKNOWN_UNRECOVERED"


def _build_failure_evidence(skill: str, result: dict[str, Any]) -> dict[str, Any]:
    data = dict(result.get("data") or {})
    trace = dict(data.get("trace") or {})
    return {
        "skill": skill,
        "status": str(result.get("status") or ""),
        "error": result.get("error"),
        "error_category": result.get("error_category"),
        "latency_ms": int(result.get("latency_ms") or 0),
        "data_ready": bool(result.get("data_ready")),
        "recovered": data.get("recovered"),
        "unrecovered_reason_code": data.get("unrecovered_reason_code"),
        "data_origin": data.get("data_origin"),
        "network_evidence": [dict(item) for item in list(data.get("network_evidence") or []) if isinstance(item, dict)],
        "akshare_calls": [dict(item) for item in list(data.get("akshare_calls") or []) if isinstance(item, dict)][:12],
        "phase_latency_ms": dict(trace.get("phase_latency_ms") or {}),
        "phase_status": dict(trace.get("phase_status") or {}),
        "phase_error": dict(trace.get("phase_error") or {}),
    }


def resolve_execution_outcome(skill_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    for skill in CRITICAL_SKILLS:
        result = dict(skill_results.get(skill) or {})
        data_ready = result.get("data_ready")
        if data_ready is None:
            data_ready = str(result.get("status") or "") == "valid"
        if bool(data_ready):
            continue

        reason_code = _map_failure_code(skill, result)
        return {
            "execution_status": "failed",
            "failure_reason_code": reason_code,
            "failure_reason_message": FAILURE_REASON_MESSAGES.get(reason_code, FAILURE_REASON_MESSAGES["UNKNOWN_UNRECOVERED"]),
            "failure_stage": skill,
            "failure_evidence": _build_failure_evidence(skill, result),
        }

    return {
        "execution_status": "success",
        "failure_reason_code": None,
        "failure_reason_message": None,
        "failure_stage": None,
        "failure_evidence": None,
    }


def aggregate_stock_wiki_payload(
    *,
    question: str,
    symbol: str,
    company_name: str,
    skill_results: dict[str, dict[str, Any]],
    trace_id: str | None = None,
) -> dict[str, Any]:
    relationship = dict(skill_results.get("relationship") or {})
    relationship_pending = bool((relationship.get("data") or {}).get("pending"))
    timeout_skills = [
        skill
        for skill, result in skill_results.items()
        if str((result or {}).get("error") or "").startswith("timeout_soft_")
    ]
    partial_release = relationship_pending or bool(timeout_skills)
    failure_mask, critical_failures = _compute_failure_mask(skill_results)
    completed_skills = [
        skill
        for skill, result in skill_results.items()
        if str((result or {}).get("status") or "") == "valid"
    ]
    failed_skills = [
        skill
        for skill, result in skill_results.items()
        if str((result or {}).get("status") or "") in {"error", "degraded"}
    ]
    pending_skills = [
        skill
        for skill, result in skill_results.items()
        if str((result or {}).get("status") or "") in {"pending", "running"}
    ]
    page_status = "partial" if failed_skills or pending_skills else "complete"

    per_skill_latency = {
        skill: int((result or {}).get("latency_ms") or 0)
        for skill, result in skill_results.items()
    }
    total_latency_ms = max(per_skill_latency.values()) if per_skill_latency else 0

    sources: list[dict[str, Any]] = []
    for result in skill_results.values():
        result_sources = result.get("sources")
        if isinstance(result_sources, list):
            sources.extend([dict(item) for item in result_sources if isinstance(item, dict)])

    data = {
        "question": question,
        "summary": dict(skill_results.get("summary") or {}).get("data") or {},
        "entity_info": dict(skill_results.get("entity_info") or {}).get("data") or {},
        "timeline": dict(skill_results.get("timeline") or {}).get("data") or {},
        "watch_calendar": dict(skill_results.get("watch_calendar") or {}).get("data") or {},
        "relationship": relationship.get("data") or {},
        "skills": skill_results,
    }
    metadata = {
        "generated_at": _iso_now(),
        "trace_id": trace_id or f"trace_{uuid4().hex[:12]}",
        "symbol": symbol,
        "company_name": company_name,
        "total_latency_ms": total_latency_ms,
        "per_skill_latency": per_skill_latency,
        "partial_release": partial_release,
        "relationship_pending": relationship_pending,
        "timeout_skills": timeout_skills,
        "strict_fail": False,
        "critical_failures": critical_failures,
        "failure_mask": failure_mask,
        "degrade_reason": None,
        "execution_status": None,
        "failure_reason_code": None,
        "failure_reason_message": None,
        "failure_stage": None,
        "failure_evidence": None,
        "page_status": page_status,
        "completed_skills": completed_skills,
        "failed_skills": failed_skills,
        "pending_skills": pending_skills,
    }

    return {
        "data": data,
        "metadata": metadata,
        "quality_status": "degraded" if page_status == "partial" else "valid",
        "sources": sources,
    }
