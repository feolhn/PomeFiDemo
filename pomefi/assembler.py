from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pomefi.logging import EventLogger
from pomefi.protocol import fallback_response, make_block, make_reference, make_response

METRIC_LABELS = {
    "price_last": "最新价",
    "ret_1d": "近1日收益",
    "ret_5d": "近5日收益",
    "ret_20d": "近20日收益",
    "vol_20d": "20日年化波动",
    "max_drawdown_1y": "近1年最大回撤",
    "pe_ttm": "PE(TTM)",
    "pb": "PB",
    "ps_ttm": "PS(TTM)",
    "pe_quantile_5y": "PE五年分位",
    "pb_quantile_5y": "PB五年分位",
    "revenue_yoy": "营收同比",
    "profit_yoy": "利润同比",
}


def _parse_iso_timestamp(value: str | None) -> tuple[int, str]:
    text = str(value or "").strip()
    if not text:
        return (0, "")
    try:
        normalized = text.replace("Z", "+00:00")
        return (1, datetime.fromisoformat(normalized).isoformat())
    except ValueError:
        return (0, text)


def _source_priority(source: str, kind: str) -> int:
    text = f"{source} {kind}".lower()
    if any(token in text for token in ("公告", "监管", "exchange", "sec", "证监", "上交所", "深交所")):
        return 3
    if kind == "akshare":
        return 2
    if kind == "web_search":
        return 1
    return 0


def _unique_strings(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out


def _format_metric(metric_name: str, value: Any) -> str:
    label = METRIC_LABELS.get(metric_name, metric_name)
    if value is None:
        return f"{label}: 暂缺"
    if metric_name in {"price_last", "pe_ttm", "pb", "ps_ttm"}:
        return f"{label}: {float(value):.2f}"
    if metric_name in {"ret_1d", "ret_5d", "ret_20d", "vol_20d", "max_drawdown_1y", "pe_quantile_5y", "pb_quantile_5y", "revenue_yoy", "profit_yoy"}:
        return f"{label}: {float(value) * 100:.1f}%"
    return f"{label}: {value}"


def _extract_primary_local_context(trace: dict[str, Any]) -> dict[str, Any]:
    local_context = dict(trace.get("local_context") or {})
    for value in local_context.values():
        if isinstance(value, dict) and "metrics_data" in value:
            return value
    return {}


def _extract_degrade_reason(trace: dict[str, Any], explicit_reason: str | None = None) -> str | None:
    if explicit_reason:
        return explicit_reason
    for event in list(trace.get("tool_events") or []):
        preview = str(event.get("tool_content_preview") or "").lower()
        if "\"error\"" in preview or preview.startswith("{\"error\""):
            if str(event.get("source") or "") == "formula":
                return "formula_error"
            return "tool_error"
        if event.get("jsonable_ok") is False:
            return "parse_error"
    return None


def _build_reference_candidates(
    *,
    metrics_data: dict[str, Any],
    trace: dict[str, Any],
    search_summaries: list[dict[str, Any]] | None,
    date_value: str | None,
) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    symbol = str(metrics_data.get("symbol") or "").strip()
    resolved_name = str(metrics_data.get("resolved_name") or "").strip()
    if symbol or resolved_name:
        references.append(
            make_reference(
                reference_id="ref_akshare_primary",
                title=f"{resolved_name or symbol} 指标快照",
                source="AkShare",
                published_at=str(metrics_data.get("asof") or ""),
                kind="akshare",
                url=None,
            )
        )

    if date_value:
        references.append(
            make_reference(
                reference_id="ref_date_primary",
                title=f"日期对齐：{date_value}",
                source="moonshot/date:latest",
                published_at=str(date_value),
                kind="date",
                url=None,
            )
        )

    for index, item in enumerate(list(search_summaries or [])[:5], start=1):
        references.append(
            make_reference(
                reference_id=f"ref_search_{index}",
                title=str(item.get("title") or item.get("key_claim") or f"Search result {index}"),
                source=str(item.get("source") or "web_search"),
                published_at=str(item.get("published_at") or ""),
                kind="web_search",
                url=item.get("url"),
            )
        )

    if not search_summaries:
        for index, event in enumerate(list(trace.get("tool_events") or []), start=1):
            if str(event.get("tool_name") or "") != "web_search":
                continue
            preview = str(event.get("tool_content_preview") or "").strip()
            if not preview:
                continue
            references.append(
                make_reference(
                    reference_id=f"ref_search_preview_{index}",
                    title=preview,
                    source="moonshot/web-search:latest",
                    published_at="",
                    kind="web_search",
                    url=None,
                )
            )

    return references


def arbitrate_references(
    references: list[dict[str, Any]],
    *,
    logger: EventLogger | None = None,
) -> list[dict[str, Any]]:
    decorated = []
    for reference in references:
        time_flag, normalized_time = _parse_iso_timestamp(reference.get("published_at"))
        decorated.append(
            (
                time_flag,
                normalized_time,
                _source_priority(str(reference.get("source") or ""), str(reference.get("kind") or "")),
                reference,
            )
        )
    decorated.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    ordered = [item[3] for item in decorated]
    if ordered and logger is not None:
        logger.emit(
            "ARBITRATION_DECISION",
            winner_reference_id=ordered[0]["id"],
            winner_source=ordered[0]["source"],
            winner_published_at=ordered[0]["published_at"],
            candidate_count=len(ordered),
        )
    return ordered


def _build_yields_block(metrics_data: dict[str, Any], reference_ids: list[str]) -> dict[str, Any]:
    metrics = dict(metrics_data.get("metrics") or {})
    metric_refs = [key for key, value in metrics.items() if value is not None][:6]
    bullets = [_format_metric(metric_name, metrics.get(metric_name)) for metric_name in list(metrics.keys())[:6]]
    summary = "核心指标已经结构化整理，可直接用于后续判断。"
    if metrics_data.get("resolved_name"):
        summary = f"{metrics_data['resolved_name']} 的关键指标已完成归集。"
    return make_block(
        block_id="yields_core",
        block_type="yields",
        title="果实",
        summary=summary,
        bullets=bullets or ["当前无可展示指标。"],
        metric_refs=metric_refs,
        reference_ids=reference_ids[:1],
    )


def _build_pests_block(
    metrics_data: dict[str, Any],
    *,
    degrade_reason: str | None,
    trace: dict[str, Any],
    reference_ids: list[str],
) -> dict[str, Any]:
    metrics = dict(metrics_data.get("metrics") or {})
    notes = [str(item).strip() for item in list(metrics_data.get("notes") or []) if str(item).strip()]
    bullets: list[str] = []
    if metrics.get("max_drawdown_1y") is not None and float(metrics["max_drawdown_1y"]) <= -0.3:
        bullets.append("近一年最大回撤偏深，价格路径承压。")
    if metrics.get("vol_20d") is not None and float(metrics["vol_20d"]) >= 0.4:
        bullets.append("短期波动率偏高，仓位管理要更克制。")
    if metrics.get("ret_20d") is not None and float(metrics["ret_20d"]) <= -0.1:
        bullets.append("近20日收益明显转弱，趋势尚未修复。")
    for note in notes[:3]:
        bullets.append(note)
    if degrade_reason:
        bullets.append(f"当前结果存在降级原因：{degrade_reason}。")
    if not bullets:
        bullets.append("暂未发现新的结构化风险信号，但仍需核对公告与财报。")
    summary = "风险侧需要结合价格路径、数据缺口和工具稳定性一起看。"
    if trace.get("tool_events"):
        summary = "风险项已结合工具返回状态与指标缺口做最小归纳。"
    return make_block(
        block_id="pests_core",
        block_type="pests",
        title="害虫",
        summary=summary,
        bullets=bullets[:5],
        metric_refs=[key for key in ("vol_20d", "max_drawdown_1y", "ret_20d") if metrics.get(key) is not None],
        reference_ids=reference_ids[:2],
    )


def _build_pruning_block(
    *,
    answer: str,
    metrics_data: dict[str, Any],
    reference_ids: list[str],
) -> dict[str, Any]:
    metrics = dict(metrics_data.get("metrics") or {})
    bullets: list[str] = []
    if metrics.get("price_last") is not None:
        bullets.append("先锚定价格与估值位置，再决定是否继续观察。")
    if metrics.get("vol_20d") is not None:
        bullets.append("若波动率继续抬升，优先控制仓位和节奏。")
    if metrics.get("profit_yoy") is not None or metrics.get("revenue_yoy") is not None:
        bullets.append("后续重点核对下一期财报，确认基本面斜率是否延续。")
    if not bullets:
        bullets.append("当前建议先补齐结构化数据，再做动作判断。")
    summary = answer.strip() or "当前建议以信息补全和风险控制为先。"
    return make_block(
        block_id="pruning_core",
        block_type="pruning",
        title="修剪建议",
        summary=summary,
        bullets=bullets[:4],
        metric_refs=[key for key in ("price_last", "vol_20d", "revenue_yoy", "profit_yoy") if metrics.get(key) is not None],
        reference_ids=reference_ids[:2],
    )


def _build_soil_block(references: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not references:
        return None
    web_refs = [item for item in references if item.get("kind") == "web_search"]
    date_refs = [item for item in references if item.get("kind") == "date"]
    if not web_refs and not date_refs:
        return None
    bullets: list[str] = []
    if date_refs:
        bullets.append(f"时间锚点：{date_refs[0]['published_at'] or date_refs[0]['title']}")
    for ref in web_refs[:2]:
        bullets.append(ref["title"])
    return make_block(
        block_id="soil_context",
        block_type="soil",
        title="土壤",
        summary="近期公开信息和时间锚点已纳入上下文，用于解释环境变化。",
        bullets=bullets[:3] or ["当前缺少可用的环境信息。"],
        reference_ids=[item["id"] for item in (date_refs[:1] + web_refs[:2])],
    )


def _build_flowering_block(chart_index: list[dict[str, Any]], reference_ids: list[str]) -> dict[str, Any] | None:
    if not chart_index:
        return None
    chart_ids = [str(item.get("chart_id") or "") for item in chart_index if str(item.get("chart_id") or "").strip()]
    return make_block(
        block_id="flowering_trend",
        block_type="flowering",
        title="花期",
        summary="价格与估值走势已经分离到本地图表层展示，不再塞进模型上下文。",
        bullets=["优先看近一年价格走势，再看五年估值区间位置。"],
        reference_ids=reference_ids[:1],
        chart_ids=chart_ids,
    )


def assemble_garden_card(
    *,
    question: str,
    answer: str,
    model: str,
    trace: dict[str, Any],
    search_summaries: list[dict[str, Any]] | None = None,
    date_value: str | None = None,
    usage: dict[str, Any] | None = None,
    degrade_reason: str | None = None,
    trace_id: str | None = None,
    logger: EventLogger | None = None,
) -> dict[str, Any]:
    logger = logger or EventLogger(debug=False)
    try:
        local_context = _extract_primary_local_context(trace)
        metrics_data = dict(local_context.get("metrics_data") or {})
        chart_index = list(local_context.get("chart_index") or [])
        references = _build_reference_candidates(
            metrics_data=metrics_data,
            trace=trace,
            search_summaries=search_summaries,
            date_value=date_value,
        )
        ordered_references = arbitrate_references(references, logger=logger)
        reference_ids = [item["id"] for item in ordered_references]

        effective_degrade_reason = _extract_degrade_reason(trace, explicit_reason=degrade_reason)
        if effective_degrade_reason:
            logger.emit("DEGRADE", reason=effective_degrade_reason)

        blocks: list[dict[str, Any]] = []
        soil_block = _build_soil_block(ordered_references)
        if soil_block is not None:
            blocks.append(soil_block)

        flowering_block = _build_flowering_block(chart_index, reference_ids)
        if flowering_block is not None:
            blocks.append(flowering_block)

        blocks.append(_build_yields_block(metrics_data, reference_ids))
        blocks.append(
            _build_pests_block(
                metrics_data,
                degrade_reason=effective_degrade_reason,
                trace=trace,
                reference_ids=reference_ids,
            )
        )
        blocks.append(
            _build_pruning_block(
                answer=answer,
                metrics_data=metrics_data,
                reference_ids=reference_ids,
            )
        )

        used_tools = _unique_strings([str(item.get("tool_name") or "") for item in list(trace.get("tool_events") or [])])
        sources = _unique_strings([str(item.get("source") or "") for item in ordered_references])
        final_answer = answer.strip()
        if not final_answer:
            final_answer = "当前已返回结构化卡片，可先从果实、害虫和修剪建议三个块开始阅读。"

        return make_response(
            question=question,
            answer=final_answer,
            blocks=blocks,
            chart_index=chart_index,
            references=ordered_references,
            model=model,
            used_tools=used_tools,
            sources=sources,
            usage=usage,
            degrade_reason=effective_degrade_reason,
            trace_id=trace_id,
        )
    except Exception as exc:
        logger.emit("DEGRADE", reason="assembler_error", detail=str(exc))
        return fallback_response(
            question=question,
            model=model,
            answer=answer,
            degrade_reason="assembler_error",
            trace_id=trace_id,
            used_tools=[str(item.get("tool_name") or "") for item in list(trace.get("tool_events") or [])],
            sources=[],
            usage=usage,
        )


def parse_search_summaries(value: str | list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [dict(item) for item in value if isinstance(item, dict)]
    if not value:
        return []
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(loaded, list):
        return []
    return [dict(item) for item in loaded if isinstance(item, dict)]
