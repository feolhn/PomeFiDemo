from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import time
from typing import Any


def _xq_symbol(symbol: str) -> str:
    if symbol.startswith(("6", "9")):
        return f"SH{symbol}"
    if symbol.startswith(("4", "8")):
        return f"BJ{symbol}"
    return f"SZ{symbol}"


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


def _normalize_spot_map(df: Any) -> dict[str, Any]:
    spot_map: dict[str, Any] = {}
    try:
        columns = set(df.columns)
    except Exception:
        return spot_map

    if {"item", "value"}.issubset(columns):
        for row in df[["item", "value"]].to_dict(orient="records"):
            key = str(row.get("item") or "").strip()
            if key:
                spot_map[key] = row.get("value")
        if spot_map:
            return spot_map

    if "data" in columns:
        for row in df.to_dict(orient="records"):
            data = row.get("data")
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        key = str(item.get("item") or "").strip()
                        if key:
                            spot_map[key] = item.get("value")
            elif isinstance(data, dict):
                quote = data.get("quote")
                if isinstance(quote, dict):
                    for key, value in quote.items():
                        if value is not None:
                            spot_map[str(key)] = value
                if "item" in data and "value" in data:
                    key = str(data.get("item") or "").strip()
                    if key:
                        spot_map[key] = data.get("value")
        if spot_map:
            return spot_map

    if len(df.index) > 0:
        row = dict(df.iloc[0].to_dict())
        for key, value in row.items():
            if value is not None:
                spot_map[str(key)] = value
    return spot_map


def _table_to_item_value_map(df: Any) -> dict[str, Any]:
    try:
        if df.empty:
            return {}
        columns = [str(col) for col in list(df.columns)]
    except Exception:
        return {}
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


def _extract_price_fields(spot_map: dict[str, Any]) -> dict[str, Any]:
    price_last = None
    for key in ("现价", "最新价", "最新", "close", "current", "last", "last_close"):
        maybe = _to_float(spot_map.get(key))
        if maybe is not None:
            price_last = maybe
            break
    ret_1d = None
    for key in ("涨跌幅", "涨幅", "change_percent", "pct_chg"):
        maybe = _to_float(spot_map.get(key))
        if maybe is not None:
            ret_1d = maybe / 100.0 if abs(maybe) > 1.0 else maybe
            break
    return {"price_last": price_last, "ret_1d": ret_1d}


def _run_call(name: str, fn: Any) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        payload = fn()
        latency_ms = max(int((time.perf_counter() - started) * 1000), 0)
        columns = list(getattr(payload, "columns", []))[:20]
        rows = int(getattr(payload, "shape", [0])[0]) if hasattr(payload, "shape") else None
        return {
            "name": name,
            "ok": True,
            "latency_ms": latency_ms,
            "rows": rows,
            "columns": columns,
            "error": "",
            "data": payload,
        }
    except Exception as exc:
        latency_ms = max(int((time.perf_counter() - started) * 1000), 0)
        return {
            "name": name,
            "ok": False,
            "latency_ms": latency_ms,
            "rows": None,
            "columns": [],
            "error": str(exc),
            "data": None,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="AkShare 单标的行情最小探针")
    parser.add_argument("--symbol", default="300750", help="A股6位代码，例如 300750")
    parser.add_argument("--timeout", type=float, default=8.0, help="接口超时秒数")
    args = parser.parse_args()

    try:
        import akshare as ak
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"akshare import failed: {exc}"}, ensure_ascii=False, indent=2))
        return 2

    symbol = str(args.symbol).strip()
    xq_symbol = _xq_symbol(symbol)
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

    calls = [
        _run_call(
            "stock_individual_info_em",
            lambda: ak.stock_individual_info_em(symbol=symbol, timeout=args.timeout),
        ),
        _run_call(
            "stock_individual_spot_xq",
            lambda: ak.stock_individual_spot_xq(symbol=xq_symbol, timeout=args.timeout),
        ),
        _run_call(
            "stock_zh_a_hist",
            lambda: ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
                timeout=args.timeout,
            ),
        ),
    ]

    extracted: dict[str, Any] = {
        "symbol": symbol,
        "xq_symbol": xq_symbol,
        "spot_xq": {},
        "hist_last_close": None,
        "info_latest": None,
    }

    for item in calls:
        if not item["ok"]:
            continue
        data = item["data"]
        if item["name"] == "stock_individual_spot_xq":
            spot_map = _normalize_spot_map(data)
            extracted["spot_xq"] = _extract_price_fields(spot_map) | {"keys_preview": list(spot_map.keys())[:12]}
        elif item["name"] == "stock_zh_a_hist":
            try:
                if not data.empty and "收盘" in data.columns:
                    extracted["hist_last_close"] = _to_float(data["收盘"].iloc[-1])
            except Exception:
                pass
        elif item["name"] == "stock_individual_info_em":
            try:
                info_map = _table_to_item_value_map(data)
                for key in ("最新", "最新价", "现价", "收盘"):
                    maybe = _to_float(info_map.get(key))
                    if maybe is not None:
                        extracted["info_latest"] = maybe
                        break
            except Exception:
                pass

    report = {
        "ok": True,
        "symbol": symbol,
        "timeout": args.timeout,
        "calls": [
            {
                "name": item["name"],
                "ok": item["ok"],
                "latency_ms": item["latency_ms"],
                "rows": item["rows"],
                "columns": item["columns"],
                "error": item["error"],
            }
            for item in calls
        ],
        "extracted": extracted,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    price_sources = [
        extracted.get("spot_xq", {}).get("price_last"),
        extracted.get("hist_last_close"),
        extracted.get("info_latest"),
    ]
    return 0 if any(value is not None for value in price_sources) else 3


if __name__ == "__main__":
    raise SystemExit(main())
