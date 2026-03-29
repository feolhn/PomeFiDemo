from __future__ import annotations

from typing import Any


def __getattr__(name: str) -> Any:
    if name == "aggregate_stock_wiki_payload":
        from .aggregator import aggregate_stock_wiki_payload

        return aggregate_stock_wiki_payload
    if name == "route_query":
        from .router import route_query

        return route_query
    if name == "run_stock_wiki_analysis":
        from .engine import run_stock_wiki_analysis

        return run_stock_wiki_analysis
    if name == "run_stock_wiki_analysis_stream":
        from .engine import run_stock_wiki_analysis_stream

        return run_stock_wiki_analysis_stream
    if name == "run_parallel_skills":
        from .orchestrator import run_parallel_skills

        return run_parallel_skills
    raise AttributeError(name)

__all__ = [
    "aggregate_stock_wiki_payload",
    "route_query",
    "run_stock_wiki_analysis",
    "run_stock_wiki_analysis_stream",
    "run_parallel_skills",
]
