from __future__ import annotations

import asyncio
from typing import Any

from pomefi.tools import execute_akshare_tool

from .common import classify_error, make_skill_result

SUMMARY_METRICS = [
    "price_last",
    "ret_1d",
    "ret_5d",
    "ret_20d",
    "pe_ttm",
    "pb",
    "ps_ttm",
    "vol_20d",
    "max_drawdown_1y",
]


def _run_akshare_summary(symbol: str) -> dict[str, Any]:
    return execute_akshare_tool({"symbol": symbol, "metrics": SUMMARY_METRICS})


async def get_stock_summary(symbol: str, company_name: str) -> dict[str, Any]:
    try:
        tool_result = await asyncio.to_thread(_run_akshare_summary, symbol)
        metrics_data = (
            dict(tool_result.get("tool_content") or {}).get("metrics_data")
            if isinstance(tool_result, dict)
            else {}
        )
        metrics_data = dict(metrics_data or {})
        source_name = "AkShare"
        asof = str(metrics_data.get("asof") or "")
        raw_metrics = dict(metrics_data.get("metrics") or {})
        available_metrics = {key: value for key, value in raw_metrics.items() if value is not None}
        missing_metrics = [key for key, value in raw_metrics.items() if value is None]
        notes = [str(item) for item in list(metrics_data.get("notes") or [])]
        core_keys = ("price_last", "ret_1d", "ret_5d", "ret_20d")
        core_ready = any(raw_metrics.get(key) is not None for key in core_keys)
        error_message = None if core_ready else "summary_core_metrics_unavailable"
        status = "valid" if core_ready and not missing_metrics else "degraded" if core_ready else "error"
        payload = {
            "symbol": symbol,
            "company_name": str(metrics_data.get("resolved_name") or company_name or ""),
            "asof": asof,
            "metrics": available_metrics,
            "metrics_missing": missing_metrics,
            "notes": notes,
            "summary": "已输出核心行情与估值指标。" if core_ready else "核心行情数据暂不可达，请稍后重试。",
        }
        return make_skill_result(
            status=status,
            data=payload,
            sources=[
                {
                    "source": source_name,
                    "kind": "akshare",
                    "published_at": asof,
                    "title": f"{symbol} 实时行情与估值",
                    "url": None,
                }
            ],
            error=error_message,
            error_category=classify_error(" ".join(notes)) if error_message else None,
            data_ready=core_ready,
            is_critical=True,
        )
    except Exception as exc:
        return make_skill_result(
            status="error",
            data={"symbol": symbol, "company_name": company_name, "metrics": {}},
            sources=[],
            error=str(exc),
            error_category=classify_error(str(exc)),
            data_ready=False,
            is_critical=True,
        )
