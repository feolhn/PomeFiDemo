from __future__ import annotations

from typing import Any

from .formula import FormulaToolClient
from .metrics import AKSHARE_METRICS, AKSHARE_RATE_METRICS, get_akshare_tool_schema


def __getattr__(name: str) -> Any:
    if name == "execute_akshare_tool":
        from .akshare_tool import execute as execute_akshare_tool

        return execute_akshare_tool
    raise AttributeError(name)

__all__ = [
    "AKSHARE_METRICS",
    "AKSHARE_RATE_METRICS",
    "FormulaToolClient",
    "execute_akshare_tool",
    "get_akshare_tool_schema",
]
