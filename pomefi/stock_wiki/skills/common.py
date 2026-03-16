from __future__ import annotations

import json
from typing import Any


def classify_error(error: str | None) -> str:
    text = str(error or "").lower()
    if not text:
        return "unknown"
    if any(token in text for token in ("proxyerror", "connection", "timed out", "timeout", "httpsconnectionpool")):
        return "network"
    if any(token in text for token in ("rate", "too many", "429", "forbidden", "blocked")):
        return "rate_limit"
    if "empty" in text or "not found" in text:
        return "empty"
    if "json" in text or "schema" in text or "parse" in text:
        return "schema"
    if "tool" in text:
        return "tool"
    return "unknown"


def make_skill_result(
    *,
    status: str,
    data: dict[str, Any] | None = None,
    sources: list[dict[str, Any]] | None = None,
    error: str | None = None,
    error_category: str | None = None,
    data_ready: bool | None = None,
    is_critical: bool = False,
) -> dict[str, Any]:
    if error_category is None and error:
        error_category = classify_error(error)
    return {
        "status": status,
        "data": dict(data or {}),
        "sources": list(sources or []),
        "error": error,
        "error_category": error_category,
        "data_ready": data_ready,
        "is_critical": bool(is_critical),
    }


def parse_formula_content(content: str) -> list[dict[str, Any]]:
    text = str(content or "").strip()
    if not text:
        return []
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        return []

    if isinstance(loaded, list):
        return [dict(item) for item in loaded if isinstance(item, dict)]

    if isinstance(loaded, dict):
        for key in ("items", "results", "data"):
            value = loaded.get(key)
            if isinstance(value, list):
                return [dict(item) for item in value if isinstance(item, dict)]
        return [loaded]

    return []
