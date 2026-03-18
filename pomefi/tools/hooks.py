from __future__ import annotations

from typing import Any

# 这是最关键的数据分层层。
# metrics_data -> LLM，chart_index -> frontend。
# raw_bundle 只留本地，不进入模型上下文。


def _iso_date(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return str(value)


def build_chart_index(raw_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    # 这里只生成图表索引。
    # 它描述怎么画图，不负责生成叙事文本。
    chart_index: list[dict[str, Any]] = []

    price_history = raw_bundle.get("price_history_1y")
    if isinstance(price_history, list) and price_history:
        chart_index.append(
            {
                "chart_id": "price_1y_line",
                "type": "line",
                "title": "价格走势（近一年）",
                "data_ref": "local://raw_bundle/price_history_1y",
                "x_key": "date",
                "y_keys": ["close"],
            }
        )

    valuation_history = raw_bundle.get("valuation_5y")
    if isinstance(valuation_history, list) and valuation_history:
        y_keys = [key for key in ("pe_ttm", "pb") if any(item.get(key) is not None for item in valuation_history)]
        if y_keys:
            chart_index.append(
                {
                    "chart_id": "valuation_5y_line",
                    "type": "line",
                    "title": "估值走势（近五年）",
                    "data_ref": "local://raw_bundle/valuation_5y",
                    "x_key": "date",
                    "y_keys": y_keys,
                }
            )

    return chart_index


def build_hook_payload(
    *,
    symbol: str,
    resolved_name: str | None,
    asof: str | None,
    metrics: dict[str, Any],
    notes: list[str],
    raw_bundle: dict[str, Any],
    akshare_calls: list[dict[str, Any]] | None = None,
    data_origin: str = "partial",
    network_evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    # 这里定义本地工具的三层输出结构。
    # metrics_data 给 LLM，chart_index 给前端，raw_bundle 留本地。
    metrics_data = {
        "asof": asof,
        "symbol": symbol,
        "resolved_name": resolved_name or "",
        "metrics": metrics,
        "notes": notes,
        "akshare_calls": list(akshare_calls or []),
        "data_origin": str(data_origin or "partial"),
        "network_evidence": [dict(item) for item in list(network_evidence or []) if isinstance(item, dict)],
    }
    chart_index = build_chart_index(raw_bundle)
    return {
        "metrics_data": metrics_data,
        "chart_index": chart_index,
        "raw_bundle": raw_bundle,
    }


def to_local_tool_result(hook_payload: dict[str, Any]) -> dict[str, Any]:
    # 这是 agent loop 和本地工具之间的桥接协议。
    # 这里决定什么能回给模型，什么只能留在 local_context。
    return {
        "__pomefi_local_tool_result__": True,
        "tool_content": {
            "metrics_data": hook_payload["metrics_data"],
        },
        "local_context": {
            "metrics_data": hook_payload["metrics_data"],
            "chart_index": hook_payload["chart_index"],
            "raw_bundle": hook_payload["raw_bundle"],
        },
    }


def normalize_price_history_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "date": _iso_date(row.get("date")),
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close"),
                "volume": row.get("volume"),
                "amount": row.get("amount"),
            }
        )
    return out


def normalize_valuation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "date": _iso_date(row.get("date")),
                "pe_ttm": row.get("pe_ttm"),
                "pb": row.get("pb"),
            }
        )
    return out


def normalize_financial_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "date": _iso_date(row.get("date")),
                "revenue_yoy": row.get("revenue_yoy"),
                "profit_yoy": row.get("profit_yoy"),
            }
        )
    return out
