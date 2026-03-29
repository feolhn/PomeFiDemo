from __future__ import annotations

from typing import Any


def __getattr__(name: str) -> Any:
    if name == "get_entity_info":
        from .entity_info import get_entity_info

        return get_entity_info
    if name == "get_relationship":
        from .relationship import get_relationship

        return get_relationship
    if name == "get_stock_summary":
        from .stock_summary import get_stock_summary

        return get_stock_summary
    if name == "get_timeline":
        from .timeline import get_timeline

        return get_timeline
    if name == "get_watch_calendar":
        from .watch_calendar import get_watch_calendar

        return get_watch_calendar
    raise AttributeError(name)

__all__ = [
    "get_entity_info",
    "get_relationship",
    "get_stock_summary",
    "get_timeline",
    "get_watch_calendar",
]
