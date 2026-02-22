from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

DISCLAIMER_TEXT = "仅为历史数据与公开信息结构展示，不构成投资建议。"

FIELD_MAPPING = {
    "Skill ID": "skill_id",
    "Skill分类": "skill_category",
    "创建者": "creator",
    "投资人格标签": "attributes.investor_persona",
    "MBTI标签": "attributes.mbti",
    "功能": "features[]",
    "输入参数": "input_summary",
    "上涨原因": "upside_reasons[]",
    "题材地位": "theme_position.{level,explanation}",
    "新闻时间线": "news_timeline[]",
    "估值（近5年）": "valuation_5y.{current_pe,percentile,interpretation}",
    "前十大重仓": "top10_holdings[]",
    "行业集中度": "industry_concentration.{breakdown,interpretation}",
    "市值风格": "market_cap_style.{cap_breakdown,style_breakdown,interpretation}",
    "组合风险": "portfolio_risks[]",
    "结构风险": "structural_risks[]",
    "与用户画像匹配度": "profile_match.{summary,explanation}",
    "免责声明": "disclaimer",
    "生成时间": "metadata.generated_at",
    "数据来源": "metadata.data_source",
    "质量状态": "quality_status",
}

REQUIRED_FIELDS_BY_SKILL = {
    "trend_follower": [
        "skill_id",
        "skill_category",
        "creator",
        "attributes.investor_persona",
        "attributes.mbti",
        "features",
        "input_summary",
        "upside_reasons",
        "theme_position.level",
        "theme_position.explanation",
        "news_timeline",
        "valuation_5y.current_pe",
        "valuation_5y.percentile",
        "valuation_5y.interpretation",
        "structural_risks",
        "profile_match.summary",
        "profile_match.explanation",
        "disclaimer",
    ],
    "fund_diagnostic": [
        "skill_id",
        "skill_category",
        "creator",
        "attributes.investor_persona",
        "attributes.mbti",
        "features",
        "input_summary",
        "top10_holdings",
        "industry_concentration.breakdown",
        "industry_concentration.interpretation",
        "market_cap_style.cap_breakdown",
        "market_cap_style.style_breakdown",
        "market_cap_style.interpretation",
        "profile_match.summary",
        "profile_match.explanation",
        "risks",
        "disclaimer",
    ],
    "stock_diagnostic": [
        "skill_id",
        "skill_category",
        "creator",
        "attributes.investor_persona",
        "attributes.mbti",
        "features",
        "input_summary",
        "industry_concentration.breakdown",
        "industry_concentration.interpretation",
        "market_cap_style.cap_breakdown",
        "market_cap_style.style_breakdown",
        "market_cap_style.interpretation",
        "portfolio_risks",
        "profile_match.summary",
        "profile_match.explanation",
        "disclaimer",
    ],
}

BANNED_PHRASES = ["强烈推荐", "必涨", "赶紧上车", "稳赚不赔"]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_json_loads(raw: str) -> dict[str, Any] | None:
    try:
        val = json.loads(raw)
    except Exception:
        return None
    return val if isinstance(val, dict) else None


def format_pct(value: float | int | None, ndigits: int = 1) -> str:
    if value is None:
        return "N/A"
    return f"{round(float(value), ndigits)}%"


def ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def sanitize_analysis_text(text: str) -> str:
    out = text or ""
    for phrase in BANNED_PHRASES:
        out = out.replace(phrase, "保持谨慎")
    return out.strip()


def deep_get(data: dict[str, Any], path: str) -> Any:
    cur: Any = data
    for token in path.split("."):
        if not isinstance(cur, dict) or token not in cur:
            return None
        cur = cur[token]
    return cur


def deep_set(data: dict[str, Any], path: str, value: Any) -> None:
    tokens = path.split(".")
    cur = data
    for token in tokens[:-1]:
        nxt = cur.get(token)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[token] = nxt
        cur = nxt
    cur[tokens[-1]] = value


def enforce_disclaimer(data: dict[str, Any]) -> None:
    data["disclaimer"] = DISCLAIMER_TEXT


def fill_missing_fields_with_na(data: dict[str, Any], required_fields: list[str]) -> int:
    missing = 0
    for field in required_fields:
        existing = deep_get(data, field)
        if existing is not None:
            continue

        missing += 1
        if field.endswith("[]"):
            deep_set(data, field[:-2], [])
            continue

        if field.endswith("_timeline"):
            deep_set(data, field, [])
            continue

        if field in {"features", "upside_reasons", "structural_risks", "portfolio_risks", "risks", "top10_holdings", "news_timeline"}:
            deep_set(data, field, [])
            continue

        deep_set(data, field, "N/A")

    return missing


def parse_date_safe(date_str: str) -> bool:
    from datetime import datetime

    try:
        datetime.fromisoformat(date_str)
        return True
    except Exception:
        return False
