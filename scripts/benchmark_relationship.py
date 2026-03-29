from __future__ import annotations

import argparse
import asyncio
import contextlib
import io
import json
import statistics
import time
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)
if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_TEXT)

from pomefi.config import resolve_kimi_config
from pomefi.stock_wiki.skills.relationship import get_relationship
from pomefi.tools.formula import FormulaToolClient
from scripts.debug_skill import collect_runtime_info, write_skill_output
from scripts.target_stock import load_target_stock

FORMULA_URIS = ["moonshot/web-search:latest"]
OUTPUT_PATH = PROJECT_ROOT / "debug_outputs" / "stock_wiki" / "relationship.benchmark.json"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark the relationship Kimi branch.")
    parser.add_argument("--runs", type=int, default=3, help="Number of live runs to execute.")
    return parser


def _summarize_edges(edges: list[dict[str, Any]]) -> list[str]:
    rows: list[str] = []
    for item in edges:
        if not isinstance(item, dict):
            continue
        source = str(item.get("from") or "").strip()
        relation = str(item.get("relation") or "").strip()
        target = str(item.get("to") or "").strip()
        if not source or not relation or not target:
            continue
        rows.append(f"{source} -> {relation} -> {target}")
    return rows


def _sanitize_trace(trace: dict[str, Any]) -> dict[str, Any]:
    turns = []
    for turn in list(trace.get("turns") or []):
        if not isinstance(turn, dict):
            continue
        turns.append(
            {
                "index": turn.get("index"),
                "has_tool_calls": turn.get("has_tool_calls"),
                "tool_names": list(turn.get("tool_names") or []),
                "content_preview": str(turn.get("content_preview") or ""),
            }
        )

    tool_events = []
    for event in list(trace.get("tool_events") or []):
        if not isinstance(event, dict):
            continue
        tool_events.append(
            {
                "tool_name": event.get("tool_name"),
                "tool_call_id": event.get("tool_call_id"),
                "formula_uri": event.get("formula_uri"),
                "arguments_dict": dict(event.get("arguments_dict") or {}),
                "content_preview": str(event.get("tool_content_preview") or ""),
                "content_encrypted": str(event.get("tool_content_preview") or "").startswith("----MOONSHOT ENCRYPTED BEGIN----"),
            }
        )

    return {
        "tool_call_required": bool(trace.get("tool_call_required")),
        "tool_call_observed": bool(trace.get("tool_call_observed")),
        "retry_count": int(trace.get("retry_count") or 0),
        "observed_tools": list(trace.get("observed_tools") or []),
        "turns": turns,
        "tool_events": tool_events,
        "degrade_reason": trace.get("degrade_reason"),
    }


async def _run_benchmark(symbol: str, company_name: str, runs: int) -> dict[str, Any]:
    config = resolve_kimi_config()
    if not config.api_key:
        raise RuntimeError("relationship benchmark requires KIMI_API_KEY")

    formula_client = FormulaToolClient(base_url=config.base_url, api_key=config.api_key)
    await formula_client.load_tools(FORMULA_URIS)
    run_rows: list[dict[str, Any]] = []
    try:
        for index in range(1, runs + 1):
            started = time.perf_counter()
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    result = await get_relationship(
                        symbol,
                        company_name,
                        config=config,
                        formula_client=formula_client,
                    )
                latency_ms = int((time.perf_counter() - started) * 1000)
                data = dict(result.get("data") or {})
                nodes = [dict(item) for item in list(data.get("nodes") or []) if isinstance(item, dict)]
                edges = [dict(item) for item in list(data.get("edges") or []) if isinstance(item, dict)]
                trace = dict(data.get("trace") or {})
                run_rows.append(
                    {
                        "run_index": index,
                        "status": str(result.get("status") or "unknown"),
                        "latency_ms": latency_ms,
                        "summary": str(data.get("summary") or ""),
                        "nodes": nodes,
                        "node_ids": [str(item.get("id") or "") for item in nodes if str(item.get("id") or "").strip()],
                        "edges": edges,
                        "edge_summaries": _summarize_edges(edges),
                        "sources": [dict(item) for item in list(result.get("sources") or []) if isinstance(item, dict)],
                        "tool_call_observed": bool(trace.get("tool_call_observed")),
                        "trace": _sanitize_trace(trace),
                        "error": result.get("error"),
                    }
                )
            except Exception as exc:
                latency_ms = int((time.perf_counter() - started) * 1000)
                run_rows.append(
                    {
                        "run_index": index,
                        "status": "error",
                        "latency_ms": latency_ms,
                        "summary": "",
                        "nodes": [],
                        "node_ids": [],
                        "edges": [],
                        "edge_summaries": [],
                        "sources": [],
                        "tool_call_observed": False,
                        "trace": {},
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
    finally:
        await formula_client.aclose()

    success_rows = [row for row in run_rows if row["status"] == "valid"]
    latencies = [int(row["latency_ms"]) for row in run_rows]
    edge_counts = [len(list(row["edges"])) for row in success_rows]
    summary = {
        "runs": runs,
        "valid_runs": len(success_rows),
        "success_rate": round(len(success_rows) / runs, 4) if runs else 0.0,
        "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0.0,
        "min_latency_ms": min(latencies) if latencies else 0,
        "max_latency_ms": max(latencies) if latencies else 0,
        "avg_edges": round(statistics.mean(edge_counts), 2) if edge_counts else 0.0,
    }
    return {
        "skill": "relationship_benchmark",
        "symbol": symbol,
        "company_name": company_name,
        "runtime": collect_runtime_info(),
        "summary": summary,
        "runs": run_rows,
    }


def main() -> int:
    args = _build_parser().parse_args()
    symbol, company_name = load_target_stock()
    payload = asyncio.run(_run_benchmark(symbol, company_name, max(1, args.runs)))
    write_skill_output(payload, OUTPUT_PATH)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
