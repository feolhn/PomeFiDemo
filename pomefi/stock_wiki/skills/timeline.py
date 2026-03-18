from __future__ import annotations

import asyncio
from datetime import datetime
import inspect
import time
from typing import Any, Awaitable, Callable

import akshare as ak

from pomefi.tools.akshare_tool import extract_network_evidence

from .common import classify_error, make_skill_result

TIMELINE_PRICE_START_DATE = "20250101"
TIMELINE_PRICE_TIMEOUT_SECONDS = 8.0


def _load_price_rows(symbol: str) -> dict[str, Any]:
    call_logs: list[dict[str, Any]] = []
    started = time.perf_counter()
    try:
        history_df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=TIMELINE_PRICE_START_DATE,
            end_date=datetime.now().strftime("%Y%m%d"),
            adjust="qfq",
            timeout=TIMELINE_PRICE_TIMEOUT_SECONDS,
        )
        call_logs.append(
            {
                "interface": "stock_zh_a_hist",
                "symbol": symbol,
                "latency_ms": max(int((time.perf_counter() - started) * 1000), 0),
                "status": "ok",
                "error": "",
                "attempt": 1,
                "retry_count": 0,
                "dedup_hit": False,
            }
        )
    except Exception as exc:
        call_logs.append(
            {
                "interface": "stock_zh_a_hist",
                "symbol": symbol,
                "latency_ms": max(int((time.perf_counter() - started) * 1000), 0),
                "status": "error",
                "error": str(exc),
                "attempt": 1,
                "retry_count": 0,
                "dedup_hit": False,
            }
        )
        return {
            "rows": [],
            "asof": "",
            "data_origin": "partial",
            "network_evidence": extract_network_evidence(call_logs),
            "akshare_calls": call_logs,
            "error": f"price_fetch_failed: {exc}",
        }
    if history_df.empty:
        return {
            "rows": [],
            "asof": "",
            "data_origin": "partial",
            "network_evidence": extract_network_evidence(call_logs),
            "akshare_calls": call_logs,
            "error": "price_history_empty",
        }

    history_df = history_df.rename(columns={"日期": "date", "收盘": "close"}).copy()
    history_df["date"] = history_df["date"].astype(str)
    rows = [
        {"date": str(row.get("date") or "")[:10], "close": row.get("close"), "event_desc": ""}
        for row in history_df[["date", "close"]].to_dict(orient="records")
    ]
    return {
        "rows": rows[-90:],
        "asof": str(rows[-1].get("date") or "")[:10] if rows else "",
        "data_origin": "live",
        "network_evidence": extract_network_evidence(call_logs),
        "akshare_calls": call_logs,
        "error": None,
    }


async def _emit_timeline_phase(
    event_handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None,
    *,
    phase: str,
    status: str,
    latency_ms: int,
    error: str | None = None,
) -> None:
    if event_handler is None:
        return
    result = event_handler(
        {
            "type": "timeline_phase",
            "phase": phase,
            "status": status,
            "latency_ms": latency_ms,
            "error": error,
        }
    )
    if inspect.isawaitable(result):
        await result


async def _load_price_branch(
    symbol: str,
    *,
    event_handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        payload = await asyncio.to_thread(_load_price_rows, symbol)
    except Exception as exc:
        latency_ms = max(int((time.perf_counter() - started) * 1000), 0)
        error_text = f"price_fetch_failed: {exc}"
        await _emit_timeline_phase(
            event_handler,
            phase="price_series",
            status="error",
            latency_ms=latency_ms,
            error=error_text,
        )
        return {
            "payload": {
                "rows": [],
                "asof": "",
                "data_origin": "partial",
                "network_evidence": [],
                "akshare_calls": [],
                "error": error_text,
            },
            "status": "error",
            "latency_ms": latency_ms,
            "error": error_text,
        }

    latency_ms = max(int((time.perf_counter() - started) * 1000), 0)
    payload_error = str(payload.get("error") or "").strip() or None
    status = "valid" if list(payload.get("rows") or []) else "error"
    await _emit_timeline_phase(
        event_handler,
        phase="price_series",
        status=status,
        latency_ms=latency_ms,
        error=payload_error,
    )
    await _emit_timeline_phase(
        event_handler,
        phase="events_json",
        status="skipped",
        latency_ms=0,
        error="disabled_for_price_only",
    )
    return {
        "payload": payload,
        "status": status,
        "latency_ms": latency_ms,
        "error": payload_error,
    }


async def get_timeline(
    symbol: str,
    company_name: str,
    *,
    config: Any = None,
    formula_client: Any = None,
    event_handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None = None,
) -> dict[str, Any]:
    _ = (config, formula_client)
    price_branch = await _load_price_branch(symbol, event_handler=event_handler)

    price_payload = dict(price_branch.get("payload") or {})
    price_rows = [dict(item) for item in list(price_payload.get("rows") or []) if isinstance(item, dict)]
    data_origin = str(price_payload.get("data_origin") or "partial")
    network_evidence = [dict(item) for item in list(price_payload.get("network_evidence") or []) if isinstance(item, dict)]
    akshare_calls = [dict(item) for item in list(price_payload.get("akshare_calls") or []) if isinstance(item, dict)]
    price_error = str(price_payload.get("error") or "").strip()
    asof = str(price_payload.get("asof") or "")
    sources: list[dict[str, Any]] = [
        {"source": "AkShare", "kind": "akshare", "title": f"{symbol} 近三个月K线", "published_at": asof, "url": None}
    ]
    trace_payload = {
        "tool_call_required": False,
        "tool_call_observed": False,
        "retry_count": 0,
        "observed_tools": [],
        "turns": [],
        "tool_events": [],
        "degrade_reason": None,
        "phase_latency_ms": {
            "price_series": int(price_branch.get("latency_ms") or 0),
            "events_json": 0,
        },
        "phase_status": {
            "price_series": str(price_branch.get("status") or "unknown"),
            "events_json": "skipped",
        },
        "phase_error": {
            "price_series": price_branch.get("error"),
            "events_json": "disabled_for_price_only",
        },
    }

    if not price_rows:
        error_text = price_error or str(price_branch.get("error") or "price_fetch_failed")
        error_category = classify_error(error_text)
        unrecovered_reason_code = "AKSHARE_NETWORK_UNRECOVERED" if network_evidence or error_category in {"network", "rate_limit"} else "UNKNOWN_UNRECOVERED"
        return make_skill_result(
            status="error",
            data={
                "symbol": symbol,
                "company_name": company_name,
                "series": [],
                "events": [],
                "summary": "价格折线图抓取失败，timeline 无法生成。",
                "data_origin": data_origin,
                "network_evidence": network_evidence,
                "akshare_calls": akshare_calls,
                "trace": trace_payload,
                "recovered": False,
                "unrecovered_reason_code": unrecovered_reason_code,
            },
            sources=sources,
            error=error_text,
            error_category=error_category,
            data_ready=False,
            is_critical=True,
        )

    return make_skill_result(
        status="valid",
        data={
            "symbol": symbol,
            "company_name": company_name,
            "series": price_rows,
            "events": [],
            "summary": "已抓取近三个月价格折线图；事件支路当前停用。",
            "data_origin": data_origin,
            "network_evidence": network_evidence,
            "akshare_calls": akshare_calls,
            "trace": trace_payload,
            "recovered": True,
            "unrecovered_reason_code": None,
        },
        sources=sources,
        error=None,
        error_category=None,
        data_ready=True,
        is_critical=True,
    )
