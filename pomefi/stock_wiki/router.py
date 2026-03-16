from __future__ import annotations

import re
from typing import Any, Callable

UNSUPPORTED_KEYWORDS = {
    "美股",
    "港股",
    "基金",
    "etf",
    "期货",
    "比特币",
    "btc",
    "ethereum",
    "黄金",
    "原油",
}


def looks_unsupported(question: str) -> bool:
    lower_question = str(question or "").lower()
    return any(keyword in lower_question for keyword in UNSUPPORTED_KEYWORDS)


def resolve_symbol_from_table(question: str, stock_rows: list[dict[str, str]]) -> tuple[str | None, str | None]:
    code_match = re.search(r"(?<!\d)(\d{6})(?!\d)", question)
    if code_match:
        code = code_match.group(1)
        for row in stock_rows:
            if row["code"] == code:
                return code, row["name"]
        return code, None

    exact_matches = [row for row in stock_rows if row["name"] == question.strip()]
    if len(exact_matches) == 1:
        return exact_matches[0]["code"], exact_matches[0]["name"]

    contains_matches = [row for row in stock_rows if row["name"] in question]
    if len(contains_matches) == 1:
        return contains_matches[0]["code"], contains_matches[0]["name"]

    return None, None


def route_query(
    *,
    question: str,
    stock_table_loader: Callable[[], list[dict[str, str]]],
) -> dict[str, Any]:
    question_text = str(question or "").strip()
    if looks_unsupported(question_text):
        return {
            "status": "degraded",
            "scope": "unsupported",
            "symbol": "",
            "company_name": "",
            "intent": "stock_wiki",
            "confidence": 1.0,
            "reason": "unsupported_scope",
        }

    symbol, company_name = resolve_symbol_from_table(question_text, stock_table_loader())
    if not symbol:
        return {
            "status": "degraded",
            "scope": "a_share",
            "symbol": "",
            "company_name": "",
            "intent": "stock_wiki",
            "confidence": 0.0,
            "reason": "symbol_unresolved",
        }

    return {
        "status": "valid",
        "scope": "a_share",
        "symbol": symbol,
        "company_name": company_name or "",
        "intent": "stock_wiki",
        "confidence": 1.0 if company_name else 0.8,
        "reason": "",
    }
