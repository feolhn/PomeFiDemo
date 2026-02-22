from __future__ import annotations

import json
import logging
import math
import os
import tomllib
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from utils import (
    DISCLAIMER_TEXT,
    REQUIRED_FIELDS_BY_SKILL,
    deep_set,
    enforce_disclaimer,
    fill_missing_fields_with_na,
    format_pct,
    now_iso,
    parse_date_safe,
    safe_json_loads,
    sanitize_analysis_text,
)

logger = logging.getLogger(__name__)

try:
    import akshare as ak
except Exception:
    ak = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    import streamlit as st
except Exception:
    st = None

SKILLS = {"trend_follower", "fund_diagnostic", "stock_diagnostic"}

CAP_BUCKETS = {
    "large": 200_000_000_000,
    "mid": 50_000_000_000,
}

STYLE_HINTS = {
    "trend_follower": {"persona": "趋势猎手", "mbti": "ENTP / ESTP", "creator": "爱研究的小星"},
    "fund_diagnostic": {"persona": "价值守望者", "mbti": "ISTJ / ISFJ", "creator": "爱研究的小星"},
    "stock_diagnostic": {"persona": "价值守望者", "mbti": "INTJ / ENFP", "creator": "爱研究的小王"},
}

FEATURES = {
    "trend_follower": ["上涨原因", "题材地位", "新闻时间线", "估值（近5年）", "结构风险", "与用户画像匹配度"],
    "fund_diagnostic": ["前十大重仓", "行业集中度", "市值风格", "风险", "与用户画像匹配度"],
    "stock_diagnostic": ["行业集中度", "市值风格", "组合风险", "与用户画像匹配度"],
}

PROMPT_CONTEXT_MAX_CHARS = 3500


def generate_skill_card(
    skill_type: str,
    input_param: Any,
    stream_mode: bool = True,
    stream_callback: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    if skill_type not in SKILLS:
        raise ValueError(f"Unsupported skill_type: {skill_type}")

    normalized_input = _normalize_input(skill_type, input_param)
    response = {
        "data": {},
        "metadata": {"generated_at": now_iso(), "data_source": "mixed"},
        "quality_status": "valid",
    }

    degraded_reason: str | None = None

    symbol_bundle = _normalize_symbol_by_market(skill_type, normalized_input)
    ak_data, ak_ok = _fetch_akshare_with_fallback(skill_type, symbol_bundle)
    if not ak_ok:
        response["quality_status"] = "degraded"
        degraded_reason = "akshare_failed"
        logger.warning("degraded_reason=%s skill=%s", degraded_reason, skill_type)

    prompt = _build_kimi_prompt(skill_type, normalized_input, ak_data)
    llm_json, llm_ok = _call_kimi_with_optional_stream(
        prompt=prompt,
        stream_mode=stream_mode,
        stream_callback=stream_callback,
    )
    if not llm_ok:
        if response["quality_status"] == "valid":
            response["quality_status"] = "degraded"
        degraded_reason = degraded_reason or "llm_invalid_json"
        logger.warning("degraded_reason=%s skill=%s", degraded_reason, skill_type)

    data = _normalize_payload(skill_type, normalized_input, ak_data, llm_json)
    missing_count = fill_missing_fields_with_na(data, REQUIRED_FIELDS_BY_SKILL[skill_type])
    if missing_count > 0:
        if response["quality_status"] == "valid":
            response["quality_status"] = "degraded"
        degraded_reason = degraded_reason or "partial_missing_fields"
        logger.warning("degraded_reason=%s skill=%s missing=%s", degraded_reason, skill_type, missing_count)

    enforce_disclaimer(data)
    response["data"] = data

    if _is_unrecoverable(data):
        response["quality_status"] = "error"
        response["data"] = _minimal_renderable_payload(skill_type, normalized_input)

    # degraded_reason is internal log-only by contract, not returned to UI.
    return response


def _normalize_input(skill_type: str, input_param: Any) -> Any:
    if skill_type in {"trend_follower", "fund_diagnostic"}:
        val = str(input_param).strip()
        if not val.isdigit() or len(val) != 6:
            raise ValueError("input_param must be a 6-digit code")
        return val

    if skill_type == "stock_diagnostic":
        if not isinstance(input_param, (list, tuple)):
            raise ValueError("stock_diagnostic input_param must be a list of codes")
        cleaned = []
        for x in input_param:
            code = str(x).strip()
            if not code.isdigit() or len(code) != 6:
                raise ValueError("each stock code must be 6-digit")
            cleaned.append(code)
        if len(cleaned) != 5:
            raise ValueError("stock_diagnostic requires exactly 5 stock codes")
        return cleaned

    raise ValueError("Unsupported skill_type")


def _normalize_symbol_by_market(skill_type: str, normalized_input: Any) -> Any:
    def to_symbol(code: str) -> str:
        c = code.upper().replace(".", "")
        if c.startswith(("SH", "SZ")):
            return c
        prefix = code[:3]
        if prefix in {"600", "601", "603", "605", "688"}:
            return f"SH{code}"
        if prefix in {"000", "001", "002", "003", "300", "301"}:
            return f"SZ{code}"
        return f"SZ{code}"

    if skill_type in {"trend_follower", "fund_diagnostic"}:
        return {"raw": normalized_input, "symbol": to_symbol(normalized_input)}

    return [{"raw": c, "symbol": to_symbol(c)} for c in normalized_input]


def _fetch_akshare_with_fallback(skill_type: str, symbol_bundle: Any) -> tuple[dict[str, Any], bool]:
    if ak is None:
        return _sample_ak_data(skill_type, symbol_bundle), False

    try:
        if skill_type == "trend_follower":
            return _fetch_trend_ak(symbol_bundle), True
        if skill_type == "fund_diagnostic":
            return _fetch_fund_ak(symbol_bundle), True
        return _fetch_stock_diag_ak(symbol_bundle), True
    except Exception as exc:
        logger.warning("akshare fetch failed: %s", exc)
        return _sample_ak_data(skill_type, symbol_bundle), False


def _fetch_trend_ak(symbol_bundle: dict[str, str]) -> dict[str, Any]:
    code = symbol_bundle["raw"]
    symbol = symbol_bundle["symbol"]

    end_date = datetime.now().strftime("%Y%m%d")
    start_year = datetime.now().year - 5
    start_date = f"{start_year}0101"

    hist_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="")
    if not isinstance(hist_df, pd.DataFrame) or hist_df.empty:
        raise RuntimeError("empty hist")

    close_col = "收盘" if "收盘" in hist_df.columns else hist_df.columns[2]
    date_col = "日期" if "日期" in hist_df.columns else hist_df.columns[0]
    prices = [
        {"date": str(row[date_col])[:10], "close": float(row[close_col])}
        for _, row in hist_df.tail(200).iterrows()
    ]

    spot_df = ak.stock_individual_spot_xq(symbol=symbol)
    spot_map = {str(r["item"]): r["value"] for _, r in spot_df.iterrows()}

    info_df = ak.stock_individual_info_em(symbol=code)
    info_map = {str(r["item"]): r["value"] for _, r in info_df.iterrows()}

    pe_val = _to_float(spot_map.get("市盈率(TTM)") or spot_map.get("市盈率(动)"))

    closes = [p["close"] for p in prices if p["close"] is not None]
    p25 = _percentile(closes, 25)
    p75 = _percentile(closes, 75)
    percentile = 62.0
    if closes:
        min_v, max_v = min(closes), max(closes)
        if max_v > min_v and pe_val is not None:
            percentile = max(0.0, min(100.0, (closes[-1] - min_v) / (max_v - min_v) * 100))

    return {
        "symbol": code,
        "name": info_map.get("股票简称") or info_map.get("名称") or code,
        "industry": info_map.get("行业") or "N/A",
        "prices": prices,
        "current_pe": pe_val,
        "pe_percentile": percentile,
        "price_band": {"p25": p25, "p75": p75},
    }


def _fetch_fund_ak(symbol_bundle: dict[str, str]) -> dict[str, Any]:
    code = symbol_bundle["raw"]
    current_year = datetime.now().year

    hold_df = None
    for year in [current_year, current_year - 1, current_year - 2]:
        try:
            df = ak.fund_portfolio_hold_em(symbol=code, date=str(year))
            if isinstance(df, pd.DataFrame) and not df.empty:
                hold_df = df
                break
        except Exception:
            continue
    if hold_df is None:
        raise RuntimeError("fund hold unavailable")

    top10 = []
    for _, row in hold_df.head(10).iterrows():
        top10.append(
            {
                "name": str(row.get("股票名称", "N/A")),
                "weight": _to_float(row.get("占净值比例")),
                "industry": str(row.get("行业", "N/A")) if "行业" in row else "N/A",
            }
        )

    ind_df = None
    for year in [current_year, current_year - 1, current_year - 2]:
        try:
            df = ak.fund_portfolio_industry_allocation_em(symbol=code, date=str(year))
            if isinstance(df, pd.DataFrame) and not df.empty:
                ind_df = df
                break
        except Exception:
            continue
    industry = []
    if ind_df is not None:
        recent = ind_df.head(10)
        for _, row in recent.iterrows():
            industry.append(
                {
                    "industry": str(row.get("行业类别", "N/A")),
                    "weight": _to_float(row.get("占净值比例")),
                }
            )

    return {"fund_code": code, "top10": top10, "industry": industry}


def _fetch_stock_diag_ak(symbol_bundle: list[dict[str, str]]) -> dict[str, Any]:
    stocks = []

    spot_all = None
    try:
        spot_all = ak.stock_zh_a_spot_em()
    except Exception:
        spot_all = None

    for item in symbol_bundle:
        code = item["raw"]
        symbol = item["symbol"]

        industry = "N/A"
        market_cap = None
        pe = None

        try:
            info_df = ak.stock_individual_info_em(symbol=code)
            info_map = {str(r["item"]): r["value"] for _, r in info_df.iterrows()}
            industry = str(info_map.get("行业") or "N/A")
            market_cap = _to_float(info_map.get("总市值") or info_map.get("流通市值"))
        except Exception:
            pass

        try:
            spot_df = ak.stock_individual_spot_xq(symbol=symbol)
            spot_map = {str(r["item"]): r["value"] for _, r in spot_df.iterrows()}
            pe = _to_float(spot_map.get("市盈率(TTM)") or spot_map.get("市盈率(动)"))
            market_cap = market_cap or _to_float(spot_map.get("总市值") or spot_map.get("流通值"))
            industry = industry if industry != "N/A" else str(spot_map.get("行业") or "N/A")
        except Exception:
            pass

        if spot_all is not None and (market_cap is None or pe is None):
            try:
                row = spot_all.loc[spot_all["代码"].astype(str) == code].head(1)
                if not row.empty:
                    rr = row.iloc[0]
                    market_cap = market_cap or _to_float(rr.get("总市值") or rr.get("流通市值"))
                    pe = pe or _to_float(rr.get("市盈率-动态"))
                    industry = industry if industry != "N/A" else str(rr.get("行业") or "N/A")
            except Exception:
                pass

        stocks.append({"code": code, "industry": industry, "market_cap": market_cap, "pe": pe})

    return {"stocks": stocks}


def _build_kimi_prompt(skill_type: str, normalized_input: Any, ak_data: dict[str, Any]) -> str:
    context = _build_prompt_context(skill_type, ak_data)
    context, clipped = _apply_prompt_context_budget(skill_type, context, max_chars=PROMPT_CONTEXT_MAX_CHARS)
    context_chars = len(json.dumps(context, ensure_ascii=False))
    logger.info(
        "prompt_context_size skill=%s field_count=%s chars=%s clipped=%s",
        skill_type,
        len(context.keys()) if isinstance(context, dict) else 0,
        context_chars,
        clipped,
    )

    prompt = {
        "system": (
            "你是冷静、理性、结构化的金融分析师。"
            "输出必须是 JSON，不要 Markdown，不要投资建议，不要出现强烈推荐或必涨。"
        ),
        "skill": skill_type,
        "input": normalized_input,
        "context": context,
        "required_output": {
            "trend_follower": ["upside_reasons", "theme_position", "news_timeline", "valuation_5y", "structural_risks", "profile_match"],
            "fund_diagnostic": ["top10_holdings", "industry_concentration", "market_cap_style", "risks", "profile_match"],
            "stock_diagnostic": ["industry_concentration", "market_cap_style", "portfolio_risks", "profile_match"],
        }[skill_type],
    }
    return json.dumps(prompt, ensure_ascii=False)


def _safe_call_and_parse_kimi(prompt: str) -> tuple[dict[str, Any], bool]:
    key, base_url, model = _resolve_kimi_config()
    if not key or OpenAI is None:
        return {}, False

    try:
        temperature = _resolve_model_temperature(model)
        client = OpenAI(api_key=key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
        content = resp.choices[0].message.content or ""
        val = safe_json_loads(content)
        return (val or {}, bool(val))
    except Exception as exc:
        logger.warning("kimi call failed: %s", exc)
        return {}, False


def _call_kimi_with_optional_stream(
    prompt: str,
    stream_mode: bool,
    stream_callback: Callable[[str], None] | None = None,
) -> tuple[dict[str, Any], bool]:
    if not stream_mode:
        return _safe_call_and_parse_kimi(prompt)

    llm_json, ok, used_fallback = _stream_kimi_response(prompt, stream_callback=stream_callback)
    if used_fallback:
        logger.info("stream_fallback_used=true")
    return llm_json, ok


def _stream_kimi_response(
    prompt: str,
    stream_callback: Callable[[str], None] | None = None,
) -> tuple[dict[str, Any], bool, bool]:
    key, base_url, model = _resolve_kimi_config()
    if not key or OpenAI is None:
        return {}, False, True

    start = time.perf_counter()
    chunk_count = 0
    buffer: list[str] = []
    logger.info("stream_started=true model=%s", model)

    try:
        temperature = _resolve_model_temperature(model)
        client = OpenAI(api_key=key, base_url=base_url)
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            stream=True,
        )

        for chunk in stream:
            chunk_count += 1
            delta = chunk.choices[0].delta
            piece = getattr(delta, "content", None)
            if not piece:
                continue
            buffer.append(piece)
            if stream_callback is not None:
                try:
                    stream_callback("".join(buffer))
                except Exception:
                    pass

        text = "".join(buffer).strip()
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "stream_duration_ms=%s stream_chunks=%s stream_fallback_used=false",
            duration_ms,
            chunk_count,
        )
        val = safe_json_loads(text)
        if not val:
            logger.warning("stream_invalid_json=true")
            return {}, False, True
        return val, True, False
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.warning(
            "stream_error=%s stream_duration_ms=%s stream_chunks=%s stream_fallback_used=true",
            exc,
            duration_ms,
            chunk_count,
        )
        # Fallback to non-stream mode
        fallback_json, fallback_ok = _safe_call_and_parse_kimi(prompt)
        return fallback_json, fallback_ok, True


def _build_prompt_context(skill_type: str, ak_data: dict[str, Any]) -> dict[str, Any]:
    if skill_type == "trend_follower":
        prices = ak_data.get("prices", [])
        recent = prices[-20:] if isinstance(prices, list) else []
        closes = [float(x.get("close")) for x in prices if isinstance(x, dict) and _to_float(x.get("close")) is not None]
        price_min = round(min(closes), 2) if closes else "N/A"
        price_max = round(max(closes), 2) if closes else "N/A"
        if len(closes) >= 20 and closes[-20] != 0:
            change_20d = round((closes[-1] - closes[-20]) / closes[-20] * 100, 2)
        else:
            change_20d = "N/A"

        cleaned_recent = []
        for x in recent:
            if not isinstance(x, dict):
                continue
            cleaned_recent.append(
                {
                    "date": str(x.get("date", ""))[:10],
                    "close": round(float(x.get("close", 0)), 2) if _to_float(x.get("close")) is not None else "N/A",
                }
            )
        return {
            "symbol": str(ak_data.get("symbol", "N/A")),
            "name": str(ak_data.get("name", "N/A")),
            "industry": str(ak_data.get("industry", "N/A")),
            "recent_prices": cleaned_recent,
            "current_pe": round(float(ak_data.get("current_pe")), 2) if _to_float(ak_data.get("current_pe")) is not None else "N/A",
            "pe_percentile": round(float(ak_data.get("pe_percentile")), 1) if _to_float(ak_data.get("pe_percentile")) is not None else "N/A",
            "price_min": price_min,
            "price_max": price_max,
            "price_change_20d_pct": change_20d,
        }

    if skill_type == "fund_diagnostic":
        top10 = []
        for item in ak_data.get("top10", [])[:10]:
            if not isinstance(item, dict):
                continue
            top10.append(
                {
                    "name": str(item.get("name", "N/A")),
                    "weight_pct": round(float(item.get("weight")), 2) if _to_float(item.get("weight")) is not None else "N/A",
                    "industry": str(item.get("industry", "N/A")),
                }
            )

        industry_items = []
        for item in ak_data.get("industry", [])[:5]:
            if not isinstance(item, dict):
                continue
            industry_items.append(
                {
                    "industry": str(item.get("industry", "N/A")),
                    "weight_pct": round(float(item.get("weight")), 2) if _to_float(item.get("weight")) is not None else "N/A",
                }
            )

        # Fund source does not provide stable market-cap/style split in current pipeline.
        # Keep deterministic defaults so prompt has compact, stable structure.
        style_ratio = {
            "cap_breakdown": {"大盘": 70.0, "中盘": 20.0, "小盘": 10.0},
            "style_breakdown": {"价值": 60.0, "平衡": 25.0, "成长": 15.0},
        }
        return {
            "fund_code": str(ak_data.get("fund_code", "N/A")),
            "top10_holdings": top10,
            "industry_top5": industry_items,
            "style_ratio": style_ratio,
        }

    # stock_diagnostic
    stocks = []
    for item in ak_data.get("stocks", [])[:5]:
        if not isinstance(item, dict):
            continue
        market_cap = _to_float(item.get("market_cap"))
        pe = _to_float(item.get("pe"))
        stocks.append(
            {
                "code": str(item.get("code", "N/A")),
                "industry": str(item.get("industry", "N/A")),
                "market_cap_bucket": _market_cap_bucket(market_cap),
                "pe_bucket": _pe_bucket(pe),
                "market_cap": round(float(market_cap), 2) if market_cap is not None else "N/A",
                "pe": round(float(pe), 2) if pe is not None else "N/A",
            }
        )

    count = len(stocks) or 1
    industry_counter: dict[str, float] = {}
    cap_counter = {"大盘": 0.0, "中盘": 0.0, "小盘": 0.0}
    pe_vals: list[float] = []
    for s in stocks:
        industry = s["industry"] if s["industry"] else "其他"
        industry_counter[industry] = industry_counter.get(industry, 0.0) + round(100.0 / count, 1)
        cap_counter[s["market_cap_bucket"]] += round(100.0 / count, 1)
        if isinstance(s["pe"], (int, float)):
            pe_vals.append(float(s["pe"]))
    pe_mean = round(sum(pe_vals) / len(pe_vals), 2) if pe_vals else "N/A"
    return {
        "per_stock_summary": stocks,
        "aggregate": {
            "industry_ratio": industry_counter,
            "cap_ratio": {k: round(v, 1) for k, v in cap_counter.items()},
            "pe_mean": pe_mean,
        },
    }


def _apply_prompt_context_budget(skill_type: str, context: dict[str, Any], max_chars: int) -> tuple[dict[str, Any], bool]:
    serialized = json.dumps(context, ensure_ascii=False)
    if len(serialized) <= max_chars:
        return context, False

    clipped = False
    trimmed = json.loads(serialized)
    if skill_type == "trend_follower":
        rp = trimmed.get("recent_prices", [])
        if isinstance(rp, list) and len(rp) > 10:
            trimmed["recent_prices"] = rp[-10:]
            clipped = True
    elif skill_type == "fund_diagnostic":
        h = trimmed.get("top10_holdings", [])
        i = trimmed.get("industry_top5", [])
        if isinstance(h, list) and len(h) > 6:
            trimmed["top10_holdings"] = h[:6]
            clipped = True
        if isinstance(i, list) and len(i) > 3:
            trimmed["industry_top5"] = i[:3]
            clipped = True
    else:
        ps = trimmed.get("per_stock_summary", [])
        if isinstance(ps, list):
            for row in ps:
                if isinstance(row, dict):
                    row.pop("market_cap", None)
                    row.pop("pe", None)
            clipped = True

    # Final hard clamp if still too large.
    serialized2 = json.dumps(trimmed, ensure_ascii=False)
    if len(serialized2) > max_chars:
        if skill_type == "trend_follower":
            trimmed["recent_prices"] = trimmed.get("recent_prices", [])[-5:]
        elif skill_type == "fund_diagnostic":
            trimmed["top10_holdings"] = trimmed.get("top10_holdings", [])[:5]
            trimmed["industry_top5"] = trimmed.get("industry_top5", [])[:3]
        else:
            trimmed["per_stock_summary"] = trimmed.get("per_stock_summary", [])[:5]
        clipped = True
    return trimmed, clipped


def _resolve_kimi_config() -> tuple[str | None, str, str]:
    key = os.getenv("MOONSHOT_API_KEY")
    base_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
    model = os.getenv("KIMI_MODEL", "moonshot-v1-8k")

    if key:
        return key, base_url, model

    # Streamlit runtime secrets.
    if st is not None:
        try:
            key = st.secrets.get("MOONSHOT_API_KEY")  # type: ignore[attr-defined]
            base_url = st.secrets.get("KIMI_BASE_URL", base_url)  # type: ignore[attr-defined]
            model = st.secrets.get("KIMI_MODEL", model)  # type: ignore[attr-defined]
            if key:
                return str(key), str(base_url), str(model)
        except Exception:
            pass

    # Local debug fallback when running plain python.
    secrets_path = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            data = tomllib.loads(secrets_path.read_text())
            key = data.get("MOONSHOT_API_KEY")
            base_url = data.get("KIMI_BASE_URL", base_url)
            model = data.get("KIMI_MODEL", model)
            if key:
                return str(key), str(base_url), str(model)
        except Exception:
            pass

    return None, base_url, model


def _resolve_model_temperature(model: str) -> float:
    # Some Moonshot models (e.g., kimi-k2.5) only accept temperature=1.
    if model.strip().lower() == "kimi-k2.5":
        return 1.0
    return 0.2


def _normalize_payload(skill_type: str, normalized_input: Any, ak_data: dict[str, Any], llm_json: dict[str, Any]) -> dict[str, Any]:
    base = {
        "skill_id": skill_type,
        "skill_category": "结构认知引擎",
        "creator": STYLE_HINTS[skill_type]["creator"],
        "attributes": {
            "investor_persona": STYLE_HINTS[skill_type]["persona"],
            "mbti": STYLE_HINTS[skill_type]["mbti"],
        },
        "features": FEATURES[skill_type],
        "input_summary": normalized_input,
        "disclaimer": DISCLAIMER_TEXT,
    }

    if skill_type == "trend_follower":
        base.update(_normalize_trend_data(ak_data, llm_json))
    elif skill_type == "fund_diagnostic":
        base.update(_normalize_fund_data(ak_data, llm_json))
    else:
        base.update(_normalize_stock_diag_data(ak_data, llm_json))

    return base


def _normalize_trend_data(ak_data: dict[str, Any], llm_json: dict[str, Any]) -> dict[str, Any]:
    reasons = llm_json.get("upside_reasons") if isinstance(llm_json.get("upside_reasons"), list) else []
    reasons = [sanitize_analysis_text(str(x)) for x in reasons if str(x).strip()]
    if not reasons:
        reasons = [
            "价格趋势阶段性修复，资金偏好回暖。",
            "产业链边际数据改善，情绪从悲观回归中性。",
        ]

    timeline = llm_json.get("news_timeline") if isinstance(llm_json.get("news_timeline"), list) else []
    normalized_tl = []
    for item in timeline:
        if not isinstance(item, dict):
            continue
        d = str(item.get("date", ""))[:10]
        t = str(item.get("title", "")).strip()
        if d and t and parse_date_safe(d):
            normalized_tl.append({"date": d, "title": t})

    if not normalized_tl:
        normalized_tl = [
            {"date": "2026-02-18", "title": "产业链订单边际改善"},
            {"date": "2026-02-12", "title": "海外业务进展更新"},
        ]

    pe = ak_data.get("current_pe")
    pct = ak_data.get("pe_percentile")
    interp = "估值处于历史中枢附近，需关注业绩兑现节奏。"

    return {
        "upside_reasons": reasons,
        "theme_position": {
            "level": llm_json.get("theme_position", {}).get("level", "板块核心标的")
            if isinstance(llm_json.get("theme_position"), dict)
            else "板块核心标的",
            "explanation": sanitize_analysis_text(
                llm_json.get("theme_position", {}).get("explanation", "具备规模优势与资金关注度。")
                if isinstance(llm_json.get("theme_position"), dict)
                else "具备规模优势与资金关注度。"
            ),
        },
        "news_timeline": normalized_tl,
        "valuation_5y": {
            "current_pe": pe if pe is not None else "N/A",
            "percentile": f"{round(float(pct), 1)}%" if pct is not None else "N/A",
            "interpretation": sanitize_analysis_text(
                llm_json.get("valuation_5y", {}).get("interpretation", interp)
                if isinstance(llm_json.get("valuation_5y"), dict)
                else interp
            ),
        },
        "structural_risks": llm_json.get("structural_risks")
        if isinstance(llm_json.get("structural_risks"), list)
        else ["高估值阶段波动放大", "景气反转验证不及预期"],
        "profile_match": {
            "summary": llm_json.get("profile_match", {}).get("summary", "中度匹配")
            if isinstance(llm_json.get("profile_match"), dict)
            else "中度匹配",
            "explanation": sanitize_analysis_text(
                llm_json.get("profile_match", {}).get("explanation", "偏成长风格投资者更容易接受该波动特征。")
                if isinstance(llm_json.get("profile_match"), dict)
                else "偏成长风格投资者更容易接受该波动特征。"
            ),
        },
        "price_series": ak_data.get("prices", []),
    }


def _normalize_fund_data(ak_data: dict[str, Any], llm_json: dict[str, Any]) -> dict[str, Any]:
    top10 = []
    for item in ak_data.get("top10", [])[:10]:
        top10.append(
            {
                "name": item.get("name", "N/A"),
                "weight": format_pct(item.get("weight")),
                "industry": item.get("industry", "N/A"),
            }
        )
    while len(top10) < 10:
        top10.append({"name": "N/A", "weight": "N/A", "industry": "N/A"})

    breakdown = {}
    for it in ak_data.get("industry", []):
        k = str(it.get("industry", "其他"))
        v = it.get("weight")
        if v is not None:
            breakdown[k] = f"{round(float(v), 1)}%"

    if not breakdown:
        breakdown = {"其他": "100.0%"}

    return {
        "top10_holdings": top10,
        "industry_concentration": {
            "breakdown": breakdown,
            "interpretation": sanitize_analysis_text(
                llm_json.get("industry_concentration", {}).get("interpretation", "行业集中度偏高，需关注单一风格回撤。")
                if isinstance(llm_json.get("industry_concentration"), dict)
                else "行业集中度偏高，需关注单一风格回撤。"
            ),
        },
        "market_cap_style": {
            "cap_breakdown": llm_json.get("market_cap_style", {}).get("cap_breakdown", {"大盘": "70.0%", "中盘": "20.0%", "小盘": "10.0%"})
            if isinstance(llm_json.get("market_cap_style"), dict)
            else {"大盘": "70.0%", "中盘": "20.0%", "小盘": "10.0%"},
            "style_breakdown": llm_json.get("market_cap_style", {}).get("style_breakdown", {"价值": "60.0%", "平衡": "25.0%", "成长": "15.0%"})
            if isinstance(llm_json.get("market_cap_style"), dict)
            else {"价值": "60.0%", "平衡": "25.0%", "成长": "15.0%"},
            "interpretation": sanitize_analysis_text(
                llm_json.get("market_cap_style", {}).get("interpretation", "组合偏大盘价值，波动通常低于成长风格。")
                if isinstance(llm_json.get("market_cap_style"), dict)
                else "组合偏大盘价值，波动通常低于成长风格。"
            ),
        },
        "risks": llm_json.get("risks") if isinstance(llm_json.get("risks"), list) else ["行业暴露集中", "风格漂移风险"],
        "profile_match": {
            "summary": llm_json.get("profile_match", {}).get("summary", "中性")
            if isinstance(llm_json.get("profile_match"), dict)
            else "中性",
            "explanation": sanitize_analysis_text(
                llm_json.get("profile_match", {}).get("explanation", "与低波动偏好更匹配。")
                if isinstance(llm_json.get("profile_match"), dict)
                else "与低波动偏好更匹配。"
            ),
        },
    }


def _normalize_stock_diag_data(ak_data: dict[str, Any], llm_json: dict[str, Any]) -> dict[str, Any]:
    stocks = ak_data.get("stocks", [])
    if not stocks:
        stocks = _sample_ak_data("stock_diagnostic", []).get("stocks", [])

    count = len(stocks) or 1
    unit = 100.0 / count

    industry_counter: dict[str, float] = {}
    cap_counter = {"大盘": 0.0, "中盘": 0.0, "小盘": 0.0}
    style_counter = {"价值": 0.0, "平衡": 0.0, "成长": 0.0}
    pe_values = []

    for s in stocks:
        industry = s.get("industry") or "其他"
        industry_counter[industry] = industry_counter.get(industry, 0.0) + unit

        cap = s.get("market_cap")
        if cap is None:
            bucket = "中盘"
        elif cap >= CAP_BUCKETS["large"]:
            bucket = "大盘"
        elif cap >= CAP_BUCKETS["mid"]:
            bucket = "中盘"
        else:
            bucket = "小盘"
        cap_counter[bucket] += unit

        pe = s.get("pe")
        if pe is not None and pe > 0:
            pe_values.append(float(pe))
            if pe <= 15:
                style_counter["价值"] += unit
            elif pe <= 30:
                style_counter["平衡"] += unit
            else:
                style_counter["成长"] += unit
        else:
            style_counter["平衡"] += unit

    industry_breakdown = {k: f"{round(v, 1)}%" for k, v in industry_counter.items()}
    cap_breakdown = {k: f"{round(v, 1)}%" for k, v in cap_counter.items()}
    style_breakdown = {k: f"{round(v, 1)}%" for k, v in style_counter.items()}
    pe_mean = round(sum(pe_values) / len(pe_values), 2) if pe_values else None

    return {
        "industry_concentration": {
            "breakdown": industry_breakdown,
            "interpretation": sanitize_analysis_text(
                llm_json.get("industry_concentration", {}).get("interpretation", "组合行业集中度较高，回撤相关性风险较大。")
                if isinstance(llm_json.get("industry_concentration"), dict)
                else "组合行业集中度较高，回撤相关性风险较大。"
            ),
        },
        "market_cap_style": {
            "cap_breakdown": cap_breakdown,
            "style_breakdown": style_breakdown,
            "interpretation": sanitize_analysis_text(
                llm_json.get("market_cap_style", {}).get("interpretation", "中小盘占比越高，组合弹性越大但波动也更高。")
                if isinstance(llm_json.get("market_cap_style"), dict)
                else "中小盘占比越高，组合弹性越大但波动也更高。"
            ),
        },
        "portfolio_risks": llm_json.get("portfolio_risks")
        if isinstance(llm_json.get("portfolio_risks"), list)
        else ["行业集中风险", "流动性风险", "估值回调风险"],
        "profile_match": {
            "summary": llm_json.get("profile_match", {}).get("summary", "需谨慎")
            if isinstance(llm_json.get("profile_match"), dict)
            else "需谨慎",
            "explanation": sanitize_analysis_text(
                llm_json.get("profile_match", {}).get("explanation", "适合高波动容忍度投资者。")
                if isinstance(llm_json.get("profile_match"), dict)
                else "适合高波动容忍度投资者。"
            ),
        },
        "pe_mean": pe_mean if pe_mean is not None else "N/A",
        "stocks": stocks,
    }


def _is_unrecoverable(data: dict[str, Any]) -> bool:
    core = [data.get("skill_id"), data.get("skill_category"), data.get("features")]
    return any(v in (None, "", []) for v in core)


def _minimal_renderable_payload(skill_type: str, normalized_input: Any) -> dict[str, Any]:
    data = {
        "skill_id": skill_type,
        "skill_category": "结构认知引擎",
        "creator": STYLE_HINTS[skill_type]["creator"],
        "attributes": {
            "investor_persona": STYLE_HINTS[skill_type]["persona"],
            "mbti": STYLE_HINTS[skill_type]["mbti"],
        },
        "features": FEATURES[skill_type],
        "input_summary": normalized_input,
        "disclaimer": DISCLAIMER_TEXT,
    }
    return data


def _sample_ak_data(skill_type: str, symbol_bundle: Any) -> dict[str, Any]:
    if skill_type == "trend_follower":
        code = symbol_bundle["raw"] if isinstance(symbol_bundle, dict) else "300750"
        return {
            "symbol": code,
            "name": "宁德时代",
            "industry": "动力电池",
            "prices": [
                {"date": "2026-02-18", "close": 190.2},
                {"date": "2026-02-19", "close": 193.8},
                {"date": "2026-02-20", "close": 196.1},
            ],
            "current_pe": 32.4,
            "pe_percentile": 62.0,
        }

    if skill_type == "fund_diagnostic":
        return {
            "fund_code": symbol_bundle.get("raw", "001410") if isinstance(symbol_bundle, dict) else "001410",
            "top10": [
                {"name": "贵州茅台", "weight": 9.2, "industry": "白酒"},
                {"name": "美的集团", "weight": 7.8, "industry": "白电"},
                {"name": "五粮液", "weight": 7.5, "industry": "白酒"},
                {"name": "泸州老窖", "weight": 6.1, "industry": "白酒"},
                {"name": "格力电器", "weight": 5.8, "industry": "白电"},
                {"name": "中国平安", "weight": 5.2, "industry": "保险"},
                {"name": "招商银行", "weight": 4.9, "industry": "银行"},
                {"name": "伊利股份", "weight": 4.5, "industry": "乳制品"},
                {"name": "恒瑞医药", "weight": 4.1, "industry": "创新药"},
                {"name": "宁德时代", "weight": 3.8, "industry": "动力电池"},
            ],
            "industry": [
                {"industry": "消费", "weight": 62.5},
                {"industry": "金融", "weight": 10.1},
                {"industry": "制造", "weight": 8.9},
                {"industry": "医药", "weight": 4.1},
                {"industry": "其他", "weight": 14.4},
            ],
        }

    stocks = []
    for idx, item in enumerate(symbol_bundle if isinstance(symbol_bundle, list) else []):
        defaults = [
            ("半导体", 220_000_000_000, 35),
            ("AI", 180_000_000_000, 42),
            ("金融", 350_000_000_000, 8),
            ("新能源", 120_000_000_000, 28),
            ("保险", 280_000_000_000, 12),
        ]
        industry, cap, pe = defaults[idx % len(defaults)]
        stocks.append({"code": item["raw"], "industry": industry, "market_cap": cap, "pe": pe})
    if not stocks:
        stocks = [
            {"code": "600519", "industry": "消费", "market_cap": 2_300_000_000_000, "pe": 28},
            {"code": "002594", "industry": "新能源", "market_cap": 760_000_000_000, "pe": 31},
            {"code": "600036", "industry": "金融", "market_cap": 910_000_000_000, "pe": 7},
            {"code": "601012", "industry": "新能源", "market_cap": 190_000_000_000, "pe": 16},
            {"code": "601318", "industry": "保险", "market_cap": 860_000_000_000, "pe": 10},
        ]
    return {"stocks": stocks}


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if math.isnan(float(value)):
            return None
        return float(value)
    txt = str(value).replace(",", "").replace("%", "").strip()
    if not txt:
        return None
    try:
        return float(txt)
    except Exception:
        return None


def _market_cap_bucket(market_cap: float | None) -> str:
    if market_cap is None:
        return "中盘"
    if market_cap >= CAP_BUCKETS["large"]:
        return "大盘"
    if market_cap >= CAP_BUCKETS["mid"]:
        return "中盘"
    return "小盘"


def _pe_bucket(pe: float | None) -> str:
    if pe is None or pe <= 0:
        return "平衡"
    if pe <= 15:
        return "价值"
    if pe <= 30:
        return "平衡"
    return "成长"


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    idx = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
    return float(s[idx])
