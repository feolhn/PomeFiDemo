from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

QUALITY_VALID = "valid"
QUALITY_DEGRADED = "degraded"
QUALITY_ERROR = "error"

BLOCK_TYPES = (
    "soil",
    "flowering",
    "yields",
    "fertilizer",
    "pests",
    "roots",
    "pruning",
)

REQUIRED_BLOCK_TYPES = ("yields", "pests", "pruning")

REFERENCE_KINDS = ("web_search", "date", "akshare")

DEGRADE_REASONS = (
    "unsupported_scope",
    "symbol_unresolved",
    "tool_error",
    "formula_error",
    "budget_exceeded",
    "search_budget_exceeded",
    "retry_exhausted",
    "parse_error",
    "assembler_error",
    "no_message_progress",
)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_trace_id(trace_id: str | None = None) -> str:
    return trace_id or f"trace_{uuid4().hex[:12]}"


def normalize_usage(usage: dict[str, Any] | None = None) -> dict[str, int]:
    usage = dict(usage or {})
    return {
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
    }


def make_block(
    *,
    block_id: str,
    block_type: str,
    title: str,
    summary: str,
    bullets: list[str],
    metric_refs: list[str] | None = None,
    reference_ids: list[str] | None = None,
    chart_ids: list[str] | None = None,
) -> dict[str, Any]:
    if block_type not in BLOCK_TYPES:
        raise ValueError(f"Unsupported block_type: {block_type}")
    return {
        "id": block_id,
        "type": block_type,
        "title": title,
        "summary": summary.strip(),
        "bullets": [str(item).strip() for item in bullets if str(item).strip()],
        "metric_refs": [str(item) for item in list(metric_refs or []) if str(item).strip()],
        "reference_ids": [str(item) for item in list(reference_ids or []) if str(item).strip()],
        "chart_ids": [str(item) for item in list(chart_ids or []) if str(item).strip()],
    }


def make_reference(
    *,
    reference_id: str,
    title: str,
    source: str,
    published_at: str | None,
    kind: str,
    url: str | None = None,
) -> dict[str, Any]:
    if kind not in REFERENCE_KINDS:
        raise ValueError(f"Unsupported reference kind: {kind}")
    return {
        "id": reference_id,
        "title": str(title or "").strip(),
        "source": str(source or "").strip(),
        "published_at": str(published_at or "").strip(),
        "url": None if not url else str(url).strip(),
        "kind": kind,
    }


def infer_quality_status(*, blocks: list[dict[str, Any]], answer: str, degrade_reason: str | None) -> str:
    if degrade_reason:
        if blocks or answer.strip():
            return QUALITY_DEGRADED
        return QUALITY_ERROR
    if blocks and answer.strip():
        return QUALITY_VALID
    return QUALITY_ERROR


def ensure_required_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    block_map = {str(block.get("type") or ""): block for block in blocks}
    for block_type in REQUIRED_BLOCK_TYPES:
        if block_type not in block_map:
            block_map[block_type] = make_block(
                block_id=f"{block_type}_fallback",
                block_type=block_type,
                title=block_type.title(),
                summary="当前结构化信息不足，保留最小展示壳。",
                bullets=["需要补充更多工具结果后再做判断。"],
            )
    ordered_blocks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for block_type in ("soil", "flowering", "yields", "fertilizer", "pests", "roots", "pruning"):
        if block_type in block_map:
            ordered_blocks.append(block_map[block_type])
            seen.add(block_type)
    for block in blocks:
        block_type = str(block.get("type") or "")
        if block_type not in seen:
            ordered_blocks.append(block)
    return ordered_blocks


def make_response(
    *,
    question: str,
    answer: str,
    blocks: list[dict[str, Any]],
    chart_index: list[dict[str, Any]],
    references: list[dict[str, Any]],
    model: str,
    used_tools: list[str],
    sources: list[str],
    usage: dict[str, Any] | None = None,
    degrade_reason: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    normalized_blocks = ensure_required_blocks(blocks)
    return {
        "data": {
            "question": str(question or "").strip(),
            "answer": str(answer or "").strip(),
            "blocks": normalized_blocks,
            "chart_index": list(chart_index or []),
            "references": list(references or []),
        },
        "metadata": {
            "generated_at": iso_now(),
            "trace_id": ensure_trace_id(trace_id),
            "model": str(model or "").strip(),
            "used_tools": [str(item) for item in used_tools if str(item).strip()],
            "sources": [str(item) for item in sources if str(item).strip()],
            "usage": normalize_usage(usage),
            "degrade_reason": degrade_reason,
        },
        "quality_status": infer_quality_status(
            blocks=normalized_blocks,
            answer=str(answer or ""),
            degrade_reason=degrade_reason,
        ),
    }


def fallback_response(
    *,
    question: str,
    model: str,
    answer: str = "",
    degrade_reason: str = "assembler_error",
    trace_id: str | None = None,
    used_tools: list[str] | None = None,
    sources: list[str] | None = None,
    usage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fallback_answer = answer.strip() or "当前结果不足以生成完整卡片，已返回降级结果。"
    return make_response(
        question=question,
        answer=fallback_answer,
        blocks=[],
        chart_index=[],
        references=[],
        model=model,
        used_tools=list(used_tools or []),
        sources=list(sources or []),
        usage=usage,
        degrade_reason=degrade_reason,
        trace_id=trace_id,
    )
