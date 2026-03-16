from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compute_strict_fail(skill_results: dict[str, dict[str, Any]]) -> tuple[bool, dict[str, str], list[str]]:
    failure_mask: dict[str, str] = {}
    critical_failures: list[str] = []
    for skill, result in skill_results.items():
        item = dict(result or {})
        is_critical = bool(item.get("is_critical"))
        status = str(item.get("status") or "")
        data_ready = item.get("data_ready")
        if data_ready is None:
            data_ready = status == "valid"
        is_failure = status == "error" or data_ready is False
        if is_critical and is_failure:
            reason = str(item.get("error") or item.get("error_category") or status or "failed")
            failure_mask[skill] = reason
            critical_failures.append(skill)
    return bool(critical_failures), failure_mask, critical_failures


def _infer_quality_status(skill_results: dict[str, dict[str, Any]], *, strict_fail: bool) -> str:
    if strict_fail:
        return "error"
    statuses = [str(item.get("status") or "error") for item in skill_results.values()]
    if statuses and all(status == "valid" for status in statuses):
        return "valid"
    if any(status in {"valid", "degraded"} for status in statuses):
        return "degraded"
    return "error"


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
    partial_release = relationship_pending
    strict_fail, failure_mask, critical_failures = _compute_strict_fail(skill_results)

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
        "strict_fail": strict_fail,
        "critical_failures": critical_failures,
        "failure_mask": failure_mask,
        "degrade_reason": "strict_fail" if strict_fail else None,
    }

    return {
        "data": data,
        "metadata": metadata,
        "quality_status": _infer_quality_status(skill_results, strict_fail=strict_fail),
        "sources": sources,
    }
