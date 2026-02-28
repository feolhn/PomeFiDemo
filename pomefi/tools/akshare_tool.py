from __future__ import annotations

from datetime import datetime, timedelta
from math import sqrt
import sys
from pathlib import Path
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


def _xq_symbol(symbol: str) -> str:
    if symbol.startswith(("6", "9")):
        return f"SH{symbol}"
    if symbol.startswith(("4", "8")):
        return f"BJ{symbol}"
    return f"SZ{symbol}"


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


def _safe_stock_profile(symbol: str, notes: list[str]) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "company_name": "",
        "industry": "",
        "listed_at": None,
    }
    try:
        info_df = ak.stock_individual_info_em(symbol=symbol)
    except Exception as exc:
        notes.append(f"stock_individual_info_em failed: {exc}")
        return profile

    if info_df.empty:
        notes.append("stock_individual_info_em returned empty dataframe")
        return profile

    info_map = dict(zip(info_df["item"], info_df["value"]))
    profile["company_name"] = str(info_map.get("股票简称", "") or "")
    profile["industry"] = str(info_map.get("行业", "") or "")
    listed_at = info_map.get("上市时间")
    if listed_at:
        listed_at_text = str(listed_at)
        if len(listed_at_text) == 8 and listed_at_text.isdigit():
            profile["listed_at"] = f"{listed_at_text[:4]}-{listed_at_text[4:6]}-{listed_at_text[6:]}"
        else:
            profile["listed_at"] = listed_at_text
    return profile


def _safe_price_history(symbol: str, notes: list[str]) -> pd.DataFrame:
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=760)).strftime("%Y%m%d")
    try:
        history_df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )
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


def _safe_valuation_series(symbol: str, notes: list[str], indicator: str) -> pd.DataFrame:
    try:
        valuation_df = ak.stock_zh_valuation_baidu(symbol=symbol, indicator=indicator, period="近五年")
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


def _safe_spot_snapshot(symbol: str, notes: list[str]) -> pd.DataFrame:
    try:
        spot_df = ak.stock_individual_spot_xq(symbol=_xq_symbol(symbol))
    except Exception as exc:
        notes.append(f"stock_individual_spot_xq failed: {exc}")
        return pd.DataFrame()

    if spot_df.empty:
        notes.append("stock_individual_spot_xq returned empty dataframe")
    return spot_df


def _safe_financial_indicators(symbol: str, notes: list[str]) -> pd.DataFrame:
    start_year = str(max(datetime.now().year - 5, 2018))
    try:
        financial_df = ak.stock_financial_analysis_indicator(symbol=symbol, start_year=start_year)
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
    symbol, metrics = _requested(arguments.get("symbol", ""), list(arguments.get("metrics") or []))
    if not symbol:
        raise RuntimeError("akshare_tool requires a non-empty symbol")
    if not metrics:
        raise RuntimeError("akshare_tool requires at least one metric")

    invalid_metrics = [metric for metric in metrics if metric not in AKSHARE_METRICS]
    if invalid_metrics:
        raise RuntimeError(f"Unsupported metrics requested: {invalid_metrics}")

    notes: list[str] = ["rate-like metrics are normalized to decimal fractions"]
    profile = _safe_stock_profile(symbol, notes)
    price_df = _safe_price_history(symbol, notes)
    pe_df = _safe_valuation_series(symbol, notes, "市盈率(TTM)")
    pb_df = _safe_valuation_series(symbol, notes, "市净率")
    spot_df = _safe_spot_snapshot(symbol, notes)
    financial_df = _safe_financial_indicators(symbol, notes)

    metrics_out: dict[str, Any] = {metric: None for metric in metrics}

    if not price_df.empty:
        close_series = price_df["close"]
        returns = close_series.pct_change()
        metrics_out["price_last"] = metrics_out.get("price_last", None)
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

    if "ps_ttm" in metrics_out and not spot_df.empty:
        spot_map = dict(zip(spot_df["item"], spot_df["value"]))
        ps_value = pd.to_numeric(pd.Series([spot_map.get("市销率")]), errors="coerce").dropna()
        metrics_out["ps_ttm"] = float(ps_value.iloc[0]) if not ps_value.empty else None
        if metrics_out["ps_ttm"] is None:
            notes.append("ps_ttm is unavailable from stock_individual_spot_xq")

    if "revenue_yoy" in metrics_out:
        metrics_out["revenue_yoy"] = _extract_named_rate(financial_df, REVENUE_YOY_CANDIDATES)
        if metrics_out["revenue_yoy"] is None:
            notes.append("revenue_yoy could not be resolved from financial indicators")
    if "profit_yoy" in metrics_out:
        metrics_out["profit_yoy"] = _extract_named_rate(financial_df, PROFIT_YOY_CANDIDATES)
        if metrics_out["profit_yoy"] is None:
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
    )
    return to_local_tool_result(hook_payload)
