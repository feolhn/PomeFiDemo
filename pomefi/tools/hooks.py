from __future__ import annotations

from typing import Any


def _iso_date(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return str(value)


def build_chart_index(raw_bundle: dict[str, Any]) -> list[dict[str, Any]]:
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
) -> dict[str, Any]:
    metrics_data = {
        "asof": asof,
        "symbol": symbol,
        "resolved_name": resolved_name or "",
        "metrics": metrics,
        "notes": notes,
    }
    chart_index = build_chart_index(raw_bundle)
    return {
        "metrics_data": metrics_data,
        "chart_index": chart_index,
        "raw_bundle": raw_bundle,
    }


def to_local_tool_result(hook_payload: dict[str, Any]) -> dict[str, Any]:
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
