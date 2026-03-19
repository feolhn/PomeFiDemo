from __future__ import annotations

from datetime import datetime, timedelta
from dataclasses import dataclass, field
import inspect
from math import sqrt
import sys
from pathlib import Path
import threading
import time
from typing import Any

import akshare as ak
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)
if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_TEXT)

from pomefi.tools.hooks import (
    build_hook_payload,
    normalize_financial_rows,
    normalize_price_history_rows,
    normalize_valuation_rows,
    to_local_tool_result,
)
from pomefi.tools.metrics import AKSHARE_METRICS, AKSHARE_RATE_METRICS, get_akshare_tool_schema

# 这是当前唯一金融数值工具。
# 所有数值型判断都应源于这里，而不是让 LLM 补数字。
# 这里的输出还要继续经过 hook 分层。

REVENUE_YOY_CANDIDATES = [
    "营业总收入同比增长率(%)",
    "营业总收入增长率(%)",
    "营业收入同比增长率(%)",
    "营业收入增长率(%)",
    "主营业务收入增长率(%)",
]
PROFIT_YOY_CANDIDATES = [
    "净利润同比增长率(%)",
    "净利润增长率(%)",
    "扣除非经常性损益后的净利润同比增长率(%)",
    "扣非净利润同比增长率(%)",
]

AKSHARE_TIMEOUT_SECONDS = 8.0
PRICE_HISTORY_LOOKBACK_DAYS = 420
_PRICE_HISTORY_CACHE: dict[tuple[str, str, str], pd.DataFrame] = {}
_PRICE_HISTORY_LOCK = threading.Lock()
PRICE_HISTORY_MAX_RETRIES = 2
PRICE_HISTORY_RETRY_BACKOFF_SECONDS = 0.2
NETWORK_ERROR_TOKENS = (
    "proxyerror",
    "httpsconnectionpool",
    "remote end closed connection",
    "unable to connect to proxy",
    "connection aborted",
    "connection reset",
    "timed out",
    "timeout",
)
PRICE_METRICS = {"price_last", "ret_1d", "ret_5d", "ret_20d", "vol_20d", "max_drawdown_1y"}
PE_METRICS = {"pe_ttm", "pe_quantile_5y"}
PB_METRICS = {"pb", "pb_quantile_5y"}
FINANCIAL_METRICS = {"revenue_yoy", "profit_yoy"}


@dataclass
class _PriceInflightState:
    event: threading.Event = field(default_factory=threading.Event)
    frame: pd.DataFrame | None = None
    error: Exception | None = None
    source_status: str = ""
    retry_count: int = 0


_PRICE_HISTORY_INFLIGHT: dict[tuple[str, str, str], _PriceInflightState] = {}


def _xq_symbol(symbol: str) -> str:
    if symbol.startswith(("6", "9")):
        return f"SH{symbol}"
    if symbol.startswith(("4", "8")):
        return f"BJ{symbol}"
    return f"SZ{symbol}"


def _tx_symbol(symbol: str) -> str:
    if symbol.startswith(("6", "9")):
        return f"sh{symbol}"
    if symbol.startswith(("4", "8")):
        return f"bj{symbol}"
    return f"sz{symbol}"


def _call_ak(func: Any, **kwargs: Any) -> Any:
    signature = inspect.signature(func)
    if "timeout" in signature.parameters and "timeout" not in kwargs:
        kwargs["timeout"] = AKSHARE_TIMEOUT_SECONDS
    return func(**kwargs)


def _call_ak_with_diag(
    *,
    func: Any,
    interface: str,
    symbol_code: str,
    call_logs: list[dict[str, Any]],
    attempt: int = 1,
    retry_count: int = 0,
    dedup_hit: bool = False,
    **kwargs: Any,
) -> Any:
    started = time.perf_counter()
    try:
        result = _call_ak(func, **kwargs)
        call_logs.append(
            {
                "interface": interface,
                "symbol": symbol_code,
                "latency_ms": max(int((time.perf_counter() - started) * 1000), 0),
                "status": "ok",
                "error": "",
                "attempt": attempt,
                "retry_count": retry_count,
                "dedup_hit": dedup_hit,
            }
        )
        return result
    except Exception as exc:
        call_logs.append(
            {
                "interface": interface,
                "symbol": symbol_code,
                "latency_ms": max(int((time.perf_counter() - started) * 1000), 0),
                "status": "error",
                "error": str(exc),
                "attempt": attempt,
                "retry_count": retry_count,
                "dedup_hit": dedup_hit,
            }
        )
        raise


def _is_network_error_text(error_text: str) -> bool:
    text = str(error_text or "").lower()
    return any(token in text for token in NETWORK_ERROR_TOKENS)


def infer_price_data_origin(call_logs: list[dict[str, Any]]) -> str:
    statuses = [
        str(item.get("status") or "")
        for item in call_logs
        if str(item.get("interface") or "") in {"stock_zh_a_hist", "stock_zh_a_hist_tx"}
    ]
    if "ok" in statuses:
        return "live"
    if "cache_fallback" in statuses:
        return "cache_fallback"
    if "cache_hit" in statuses:
        return "live"
    return "partial"


def extract_network_evidence(call_logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for item in call_logs:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "")
        error_text = str(item.get("error") or "").strip()
        if status == "cache_fallback":
            evidence.append(
                {
                    "interface": str(item.get("interface") or ""),
                    "status": status,
                    "latency_ms": int(item.get("latency_ms") or 0),
                    "error": error_text,
                    "retry_count": int(item.get("retry_count") or 0),
                    "dedup_hit": bool(item.get("dedup_hit")),
                }
            )
            continue
        if not error_text or not _is_network_error_text(error_text):
            continue
        evidence.append(
                {
                    "interface": str(item.get("interface") or ""),
                    "status": status or "error",
                    "latency_ms": int(item.get("latency_ms") or 0),
                    "error": error_text,
                    "retry_count": int(item.get("retry_count") or 0),
                    "dedup_hit": bool(item.get("dedup_hit")),
                }
            )
    return evidence


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "").replace("%", "")
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _to_rate(value: Any) -> float | None:
    raw = _to_float(value)
    if raw is None:
        return None
    return raw / 100.0 if abs(raw) > 1.0 else raw


def _table_to_item_value_map(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {}
    columns = [str(col) for col in list(df.columns)]
    pair_candidates = [
        ("item", "value"),
        ("项目", "值"),
        ("项目", "value"),
        ("item", "值"),
        ("指标", "数值"),
        ("key", "value"),
    ]
    for key_col, value_col in pair_candidates:
        if key_col in columns and value_col in columns:
            out: dict[str, Any] = {}
            for row in df[[key_col, value_col]].to_dict(orient="records"):
                key = str(row.get(key_col) or "").strip()
                if key:
                    out[key] = row.get(value_col)
            if out:
                return out

    if len(columns) >= 2:
        key_col, value_col = columns[0], columns[1]
        out: dict[str, Any] = {}
        for row in df[[key_col, value_col]].to_dict(orient="records"):
            key = str(row.get(key_col) or "").strip()
            if key:
                out[key] = row.get(value_col)
        return out
    return {}


def _normalize_spot_snapshot(spot_df: pd.DataFrame) -> dict[str, Any]:
    if spot_df.empty:
        return {}
    spot_map: dict[str, Any] = {}
    if {"item", "value"}.issubset(set(spot_df.columns)):
        for row in spot_df[["item", "value"]].to_dict(orient="records"):
            item = str(row.get("item") or "").strip()
            if item:
                spot_map[item] = row.get("value")
        if spot_map:
            return spot_map

    if "data" in spot_df.columns:
        for row in spot_df.to_dict(orient="records"):
            data = row.get("data")
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        key = str(item.get("item") or "").strip()
                        if key:
                            spot_map[key] = item.get("value")
            elif isinstance(data, dict):
                if isinstance(data.get("quote"), dict):
                    for key, value in data["quote"].items():
                        if value is not None:
                            spot_map[str(key)] = value
                if "item" in data and "value" in data:
                    key = str(data.get("item") or "").strip()
                    if key:
                        spot_map[key] = data.get("value")
                for key, value in data.items():
                    if key != "quote" and value is not None:
                        spot_map[str(key)] = value
        if spot_map:
            return spot_map

    if len(spot_df.index) > 0:
        row = dict(spot_df.iloc[0].to_dict())
        for key, value in row.items():
            if value is not None:
                spot_map[str(key)] = value
    return spot_map


def _spot_price_last(spot_map: dict[str, Any]) -> float | None:
    for key in ("现价", "最新价", "最新", "close", "current", "last", "last_close"):
        value = _to_float(spot_map.get(key))
        if value is not None:
            return value
    return None


def _spot_ret_1d(spot_map: dict[str, Any], price_last: float | None) -> float | None:
    for key in ("涨跌幅", "涨幅", "change_percent", "pct_chg"):
        rate = _to_rate(spot_map.get(key))
        if rate is not None:
            return rate
    prev_close = None
    for key in ("昨收", "昨收价", "昨收盘", "prev_close", "pre_close"):
        prev_close = _to_float(spot_map.get(key))
        if prev_close is not None:
            break
    if prev_close is not None and prev_close != 0 and price_last is not None:
        return float(price_last / prev_close - 1.0)
    return None


def _quantile_from_series(series: pd.Series) -> float | None:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return None
    latest = float(clean.iloc[-1])
    return float((clean <= latest).mean())


def _latest_float(series: pd.Series) -> float | None:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return None
    return float(clean.iloc[-1])


def _rate_value(value: float | None) -> float | None:
    if value is None:
        return None
    return float(value) / 100.0


def _safe_stock_profile(symbol: str, notes: list[str], call_logs: list[dict[str, Any]]) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "company_name": "",
        "industry": "",
        "listed_at": None,
        "latest_price": None,
        "ps_ttm": None,
    }
    try:
        info_df = _call_ak_with_diag(
            func=ak.stock_individual_info_em,
            interface="stock_individual_info_em",
            symbol_code=symbol,
            call_logs=call_logs,
            symbol=symbol,
        )
    except Exception as exc:
        notes.append(f"stock_individual_info_em failed: {exc}")
        return profile

    if info_df.empty:
        notes.append("stock_individual_info_em returned empty dataframe")
        return profile

    info_map = _table_to_item_value_map(info_df)
    if not info_map:
        notes.append(f"stock_individual_info_em schema_unexpected: columns={list(info_df.columns)}")
        return profile
    profile["company_name"] = str(info_map.get("股票简称", "") or "")
    profile["industry"] = str(info_map.get("行业", "") or "")
    for key in ("最新", "最新价", "现价", "收盘"):
        maybe = _to_float(info_map.get(key))
        if maybe is not None:
            profile["latest_price"] = maybe
            break
    for key in ("市销率", "市销率(TTM)", "PS", "PS(TTM)"):
        maybe = _to_float(info_map.get(key))
        if maybe is not None:
            profile["ps_ttm"] = maybe
            break
    listed_at = info_map.get("上市时间")
    if listed_at:
        listed_at_text = str(listed_at)
        if len(listed_at_text) == 8 and listed_at_text.isdigit():
            profile["listed_at"] = f"{listed_at_text[:4]}-{listed_at_text[4:6]}-{listed_at_text[6:]}"
        else:
            profile["listed_at"] = listed_at_text
    return profile


def _fetch_price_history_live(
    *,
    symbol: str,
    start_date: str,
    end_date: str,
    call_logs: list[dict[str, Any]] | None,
) -> tuple[pd.DataFrame, int]:
    last_error: Exception | None = None
    total_attempts = PRICE_HISTORY_MAX_RETRIES + 1
    fetchers = (
        (
            "stock_zh_a_hist",
            ak.stock_zh_a_hist,
            {
                "symbol": symbol,
                "period": "daily",
                "start_date": start_date,
                "end_date": end_date,
                "adjust": "qfq",
            },
        ),
        (
            "stock_zh_a_hist_tx",
            ak.stock_zh_a_hist_tx,
            {
                "symbol": _tx_symbol(symbol),
                "start_date": start_date,
                "end_date": end_date,
                "adjust": "qfq",
            },
        ),
    )
    for interface, func, kwargs in fetchers:
        for attempt in range(1, total_attempts + 1):
            try:
                if call_logs is None:
                    history_df = _call_ak(func, **kwargs)
                else:
                    history_df = _call_ak_with_diag(
                        func=func,
                        interface=interface,
                        symbol_code=symbol,
                        call_logs=call_logs,
                        attempt=attempt,
                        retry_count=attempt - 1,
                        dedup_hit=False,
                        **kwargs,
                    )
                return history_df, attempt - 1
            except Exception as exc:
                last_error = exc
                if attempt >= total_attempts or not _is_network_error_text(str(exc)):
                    break
                time.sleep(PRICE_HISTORY_RETRY_BACKOFF_SECONDS * attempt)
    assert last_error is not None
    raise last_error


def _append_price_call_log(
    call_logs: list[dict[str, Any]] | None,
    *,
    symbol: str,
    status: str,
    error: str,
    retry_count: int,
    dedup_hit: bool,
    fallback_key: str | None = None,
) -> None:
    if call_logs is None:
        return
    row: dict[str, Any] = {
        "interface": "stock_zh_a_hist",
        "symbol": symbol,
        "latency_ms": 0,
        "status": status,
        "error": error,
        "retry_count": retry_count,
        "dedup_hit": dedup_hit,
    }
    if fallback_key:
        row["fallback_key"] = fallback_key
    call_logs.append(row)


def get_cached_price_history(
    symbol: str,
    *,
    lookback_days: int = PRICE_HISTORY_LOOKBACK_DAYS,
    call_logs: list[dict[str, Any]] | None = None,
) -> pd.DataFrame:
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y%m%d")
    cache_key = (symbol, start_date, end_date)
    with _PRICE_HISTORY_LOCK:
        cached = _PRICE_HISTORY_CACHE.get(cache_key)
        if cached is not None:
            _append_price_call_log(
                call_logs,
                symbol=symbol,
                status="cache_hit",
                error="",
                retry_count=0,
                dedup_hit=False,
            )
            return cached.copy()
        inflight = _PRICE_HISTORY_INFLIGHT.get(cache_key)
        if inflight is None:
            inflight = _PriceInflightState()
            _PRICE_HISTORY_INFLIGHT[cache_key] = inflight
            is_owner = True
        else:
            is_owner = False

    if not is_owner:
        inflight.event.wait(timeout=AKSHARE_TIMEOUT_SECONDS * 4)
        if inflight.frame is not None:
            _append_price_call_log(
                call_logs,
                symbol=symbol,
                status=inflight.source_status or "ok",
                error="",
                retry_count=inflight.retry_count,
                dedup_hit=True,
            )
            return inflight.frame.copy()
        if inflight.error is not None:
            _append_price_call_log(
                call_logs,
                symbol=symbol,
                status="error",
                error=str(inflight.error),
                retry_count=inflight.retry_count,
                dedup_hit=True,
            )
            raise inflight.error
        raise RuntimeError("stock_zh_a_hist singleflight waiter timeout")

    try:
        history_df, retry_count = _fetch_price_history_live(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            call_logs=call_logs,
        )
        with _PRICE_HISTORY_LOCK:
            _PRICE_HISTORY_CACHE[cache_key] = history_df.copy()
            inflight.frame = history_df.copy()
            inflight.retry_count = retry_count
            inflight.source_status = "ok"
        return history_df
    except Exception as exc:
        with _PRICE_HISTORY_LOCK:
            fallback_candidates = [
                (key, frame)
                for key, frame in _PRICE_HISTORY_CACHE.items()
                if isinstance(key, tuple) and len(key) == 3 and key[0] == symbol
            ]
            if fallback_candidates:
                fallback_key, fallback_df = sorted(fallback_candidates, key=lambda item: item[0][2], reverse=True)[0]
                retry_count = max(
                    [int(item.get("retry_count") or 0) for item in (call_logs or []) if item.get("interface") == "stock_zh_a_hist"],
                    default=0,
                )
                _append_price_call_log(
                    call_logs,
                    symbol=symbol,
                    status="cache_fallback",
                    error=str(exc),
                    retry_count=retry_count,
                    dedup_hit=False,
                    fallback_key=f"{fallback_key[1]}:{fallback_key[2]}",
                )
                inflight.frame = fallback_df.copy()
                inflight.retry_count = retry_count
                inflight.source_status = "cache_fallback"
                return fallback_df.copy()
            inflight.error = exc
            inflight.retry_count = max(
                [int(item.get("retry_count") or 0) for item in (call_logs or []) if item.get("interface") == "stock_zh_a_hist"],
                default=0,
            )
            raise
    finally:
        with _PRICE_HISTORY_LOCK:
            inflight.event.set()
            _PRICE_HISTORY_INFLIGHT.pop(cache_key, None)


def get_live_price_history(
    symbol: str,
    *,
    lookback_days: int = PRICE_HISTORY_LOOKBACK_DAYS,
    call_logs: list[dict[str, Any]] | None = None,
) -> pd.DataFrame:
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y%m%d")
    history_df, _retry_count = _fetch_price_history_live(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        call_logs=call_logs,
    )
    return history_df


def _safe_price_history(symbol: str, notes: list[str], call_logs: list[dict[str, Any]]) -> pd.DataFrame:
    try:
        history_df = get_cached_price_history(symbol, call_logs=call_logs)
    except Exception as exc:
        notes.append(f"stock_zh_a_hist failed: {exc}")
        return pd.DataFrame()

    if history_df.empty:
        notes.append("stock_zh_a_hist returned empty dataframe")
        return history_df

    history_df = history_df.rename(
        columns={
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
        }
    ).copy()
    for column in ("open", "close", "high", "low", "volume", "amount"):
        if column in history_df.columns:
            history_df[column] = pd.to_numeric(history_df[column], errors="coerce")
    history_df["date"] = pd.to_datetime(history_df["date"], errors="coerce")
    history_df = history_df.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)
    return history_df


def _safe_valuation_series(symbol: str, notes: list[str], indicator: str, call_logs: list[dict[str, Any]]) -> pd.DataFrame:
    try:
        valuation_df = _call_ak_with_diag(
            func=ak.stock_zh_valuation_baidu,
            interface="stock_zh_valuation_baidu",
            symbol_code=symbol,
            call_logs=call_logs,
            symbol=symbol,
            indicator=indicator,
            period="近五年",
        )
    except Exception as exc:
        notes.append(f"stock_zh_valuation_baidu({indicator}) failed: {exc}")
        return pd.DataFrame()

    if valuation_df.empty:
        notes.append(f"stock_zh_valuation_baidu({indicator}) returned empty dataframe")
        return valuation_df

    valuation_df = valuation_df.rename(columns={"date": "date", "value": "value"}).copy()
    valuation_df["date"] = pd.to_datetime(valuation_df["date"], errors="coerce")
    valuation_df["value"] = pd.to_numeric(valuation_df["value"], errors="coerce")
    valuation_df = valuation_df.dropna(subset=["date", "value"]).sort_values("date").reset_index(drop=True)
    return valuation_df


def _safe_spot_snapshot(symbol: str, notes: list[str], call_logs: list[dict[str, Any]]) -> pd.DataFrame:
    try:
        spot_df = _call_ak_with_diag(
            func=ak.stock_individual_spot_xq,
            interface="stock_individual_spot_xq",
            symbol_code=symbol,
            call_logs=call_logs,
            symbol=_xq_symbol(symbol),
        )
    except Exception as exc:
        notes.append(f"stock_individual_spot_xq failed: {exc}")
        return pd.DataFrame()

    if spot_df.empty:
        notes.append("stock_individual_spot_xq returned empty dataframe")
    return spot_df


def _safe_financial_indicators(symbol: str, notes: list[str], call_logs: list[dict[str, Any]]) -> pd.DataFrame:
    start_year = str(max(datetime.now().year - 5, 2018))
    try:
        financial_df = _call_ak_with_diag(
            func=ak.stock_financial_analysis_indicator,
            interface="stock_financial_analysis_indicator",
            symbol_code=symbol,
            call_logs=call_logs,
            symbol=symbol,
            start_year=start_year,
        )
    except Exception as exc:
        notes.append(f"stock_financial_analysis_indicator failed: {exc}")
        return pd.DataFrame()

    if financial_df.empty:
        notes.append("stock_financial_analysis_indicator returned empty dataframe")
        return financial_df

    financial_df = financial_df.copy()
    if "日期" in financial_df.columns:
        financial_df = financial_df.rename(columns={"日期": "date"})
    financial_df["date"] = pd.to_datetime(financial_df.get("date"), errors="coerce")
    financial_df = financial_df.sort_values("date").reset_index(drop=True)
    return financial_df


def _extract_named_rate(financial_df: pd.DataFrame, candidates: list[str]) -> float | None:
    if financial_df.empty:
        return None

    for candidate in candidates:
        if candidate in financial_df.columns:
            return _rate_value(_latest_float(financial_df[candidate]))

    for column in financial_df.columns:
        text = str(column)
        if any(candidate.replace("(%)", "") in text for candidate in candidates):
            return _rate_value(_latest_float(financial_df[column]))
    return None


def _requested(symbol: str, metrics: list[str]) -> tuple[str, list[str]]:
    clean_symbol = str(symbol or "").strip()
    clean_metrics = [str(metric).strip() for metric in metrics if str(metric).strip()]
    return clean_symbol, clean_metrics


def execute(arguments: dict[str, Any]) -> dict[str, Any]:
    # 这里负责抓数据、算指标、再交给 hook 分层。
    # 输出不会直接整包进前端，也不会直接整包回给 LLM。
    symbol, metrics = _requested(arguments.get("symbol", ""), list(arguments.get("metrics") or []))
    if not symbol:
        raise RuntimeError("akshare_tool requires a non-empty symbol")
    if not metrics:
        raise RuntimeError("akshare_tool requires at least one metric")

    invalid_metrics = [metric for metric in metrics if metric not in AKSHARE_METRICS]
    if invalid_metrics:
        raise RuntimeError(f"Unsupported metrics requested: {invalid_metrics}")

    notes: list[str] = ["rate-like metrics are normalized to decimal fractions"]
    call_logs: list[dict[str, Any]] = []
    metrics_out: dict[str, Any] = {metric: None for metric in metrics}

    needs_price = any(metric in PRICE_METRICS for metric in metrics)
    needs_pe = any(metric in PE_METRICS for metric in metrics)
    needs_pb = any(metric in PB_METRICS for metric in metrics)
    needs_financial = any(metric in FINANCIAL_METRICS for metric in metrics)
    needs_ps = "ps_ttm" in metrics_out

    profile = {
        "company_name": "",
        "industry": "",
        "listed_at": None,
        "latest_price": None,
        "ps_ttm": None,
    }

    price_df = _safe_price_history(symbol, notes, call_logs) if needs_price else pd.DataFrame()
    pe_df = _safe_valuation_series(symbol, notes, "市盈率(TTM)", call_logs) if needs_pe else pd.DataFrame()
    pb_df = _safe_valuation_series(symbol, notes, "市净率", call_logs) if needs_pb else pd.DataFrame()
    financial_df = _safe_financial_indicators(symbol, notes, call_logs) if needs_financial else pd.DataFrame()
    spot_df = pd.DataFrame()
    spot_map: dict[str, Any] = {}

    if not price_df.empty:
        close_series = price_df["close"]
        returns = close_series.pct_change()
        if "price_last" in metrics_out:
            metrics_out["price_last"] = _latest_float(close_series)
        if "ret_1d" in metrics_out and len(close_series) >= 2:
            metrics_out["ret_1d"] = float(returns.iloc[-1])
        if "ret_5d" in metrics_out and len(close_series) >= 6:
            metrics_out["ret_5d"] = float(close_series.iloc[-1] / close_series.iloc[-6] - 1.0)
        if "ret_20d" in metrics_out and len(close_series) >= 21:
            metrics_out["ret_20d"] = float(close_series.iloc[-1] / close_series.iloc[-21] - 1.0)
        if "vol_20d" in metrics_out and returns.dropna().shape[0] >= 20:
            metrics_out["vol_20d"] = float(returns.dropna().tail(20).std() * sqrt(252))
        if "max_drawdown_1y" in metrics_out and not close_series.dropna().empty:
            trailing = close_series.dropna().tail(252)
            rolling_peak = trailing.cummax()
            drawdown = trailing / rolling_peak - 1.0
            metrics_out["max_drawdown_1y"] = float(drawdown.min())

    if "pe_ttm" in metrics_out:
        metrics_out["pe_ttm"] = _latest_float(pe_df["value"]) if not pe_df.empty else None
    if "pb" in metrics_out:
        metrics_out["pb"] = _latest_float(pb_df["value"]) if not pb_df.empty else None
    if "pe_quantile_5y" in metrics_out:
        metrics_out["pe_quantile_5y"] = _quantile_from_series(pe_df["value"]) if not pe_df.empty else None
    if "pb_quantile_5y" in metrics_out:
        metrics_out["pb_quantile_5y"] = _quantile_from_series(pb_df["value"]) if not pb_df.empty else None

    need_spot_snapshot = (
        needs_ps
        or ("price_last" in metrics_out and metrics_out["price_last"] is None)
        or ("ret_1d" in metrics_out and metrics_out["ret_1d"] is None)
    )
    if need_spot_snapshot:
        spot_df = _safe_spot_snapshot(symbol, notes, call_logs)
        spot_map = _normalize_spot_snapshot(spot_df)

    need_profile_snapshot = needs_ps
    if need_profile_snapshot:
        profile = _safe_stock_profile(symbol, notes, call_logs)

    if "ps_ttm" in metrics_out and need_profile_snapshot:
        metrics_out["ps_ttm"] = _to_float(profile.get("ps_ttm"))
    if "ps_ttm" in metrics_out and metrics_out["ps_ttm"] is None:
        ps_value = pd.to_numeric(pd.Series([spot_map.get("市销率")]), errors="coerce").dropna()
        metrics_out["ps_ttm"] = float(ps_value.iloc[0]) if not ps_value.empty else None
        if metrics_out["ps_ttm"] is None:
            # None + notes 是设计行为。
            # 这里保留可追溯缺口，而不是伪造指标值。
            notes.append("ps_ttm is unavailable from stock_individual_spot_xq")

    if "price_last" in metrics_out and metrics_out["price_last"] is None and need_profile_snapshot:
        metrics_out["price_last"] = _to_float(profile.get("latest_price"))
    if "price_last" in metrics_out and metrics_out["price_last"] is None:
        metrics_out["price_last"] = _spot_price_last(spot_map)
    if "ret_1d" in metrics_out and metrics_out["ret_1d"] is None:
        metrics_out["ret_1d"] = _spot_ret_1d(spot_map, metrics_out.get("price_last"))

    if "revenue_yoy" in metrics_out:
        metrics_out["revenue_yoy"] = _extract_named_rate(financial_df, REVENUE_YOY_CANDIDATES)
        if metrics_out["revenue_yoy"] is None:
            # 缺字段时返回 None，并把原因写入 notes。
            notes.append("revenue_yoy could not be resolved from financial indicators")
    if "profit_yoy" in metrics_out:
        metrics_out["profit_yoy"] = _extract_named_rate(financial_df, PROFIT_YOY_CANDIDATES)
        if metrics_out["profit_yoy"] is None:
            # 缺字段时返回 None，并把原因写入 notes。
            notes.append("profit_yoy could not be resolved from financial indicators")

    valuation_merged: list[dict[str, Any]] = []
    if not pe_df.empty or not pb_df.empty:
        merged = None
        if not pe_df.empty:
            merged = pe_df.rename(columns={"value": "pe_ttm"})[["date", "pe_ttm"]]
        if not pb_df.empty:
            pb_only = pb_df.rename(columns={"value": "pb"})[["date", "pb"]]
            merged = pb_only if merged is None else merged.merge(pb_only, on="date", how="outer")
        if merged is not None:
            merged = merged.sort_values("date").reset_index(drop=True)
            valuation_merged = normalize_valuation_rows(merged.to_dict(orient="records"))

    financial_rows: list[dict[str, Any]] = []
    if not financial_df.empty:
        preview_rows = financial_df[["date"]].copy()
        preview_rows["revenue_yoy"] = _extract_named_rate(financial_df, REVENUE_YOY_CANDIDATES)
        preview_rows["profit_yoy"] = _extract_named_rate(financial_df, PROFIT_YOY_CANDIDATES)
        latest_row = preview_rows.tail(1).to_dict(orient="records")
        financial_rows = normalize_financial_rows(latest_row)

    data_origin = infer_price_data_origin(call_logs)
    network_evidence = extract_network_evidence(call_logs)

    asof = None
    if not price_df.empty:
        latest_date = price_df["date"].dropna().iloc[-1]
        asof = latest_date.date().isoformat()
    elif valuation_merged:
        asof = str(valuation_merged[-1]["date"])

    raw_bundle = {
        "profile": profile,
        "price_history_1y": normalize_price_history_rows(price_df.tail(252).to_dict(orient="records")) if not price_df.empty else [],
        "valuation_5y": valuation_merged,
        "financial_indicators": financial_rows,
    }

    hook_payload = build_hook_payload(
        symbol=symbol,
        resolved_name=str(profile.get("company_name") or ""),
        asof=asof,
        metrics=metrics_out,
        notes=notes,
        raw_bundle=raw_bundle,
        akshare_calls=call_logs,
        data_origin=data_origin,
        network_evidence=network_evidence,
    )
    return to_local_tool_result(hook_payload)
