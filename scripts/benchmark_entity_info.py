from __future__ import annotations

import argparse
import asyncio
import contextlib
import io
import json
import statistics
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)
if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_TEXT)

from pomefi.config import resolve_kimi_config
from pomefi.stock_wiki.skills.entity_info import get_entity_info
from pomefi.tools.formula import FormulaToolClient
from scripts.debug_skill import collect_runtime_info, write_skill_output
from scripts.target_stock import load_target_stock

OUTPUT_PATH = PROJECT_ROOT / "debug_outputs" / "stock_wiki" / "entity_info.benchmark.json"
FORMULA_URIS = ["moonshot/web-search:latest"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark the entity_info Kimi branch.")
    parser.add_argument("--runs", type=int, default=3, help="Number of live runs to execute.")
    return parser


async def _run_benchmark(symbol: str, company_name: str, runs: int) -> dict:
    config = resolve_kimi_config()
    if not config.api_key:
        raise RuntimeError("entity_info benchmark requires KIMI_API_KEY")

    run_rows: list[dict] = []
    formula_client = FormulaToolClient(base_url=config.base_url, api_key=config.api_key)
    try:
        await formula_client.load_tools(FORMULA_URIS)
        for index in range(1, runs + 1):
            started = time.perf_counter()
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    result = await get_entity_info(symbol, company_name, config=config, formula_client=formula_client)
                latency_ms = int((time.perf_counter() - started) * 1000)
                data = dict(result.get("data") or {})
                run_rows.append(
                    {
                        "run_index": index,
                        "status": str(result.get("status") or "unknown"),
                        "latency_ms": latency_ms,
                        "company_name": str(data.get("company_name") or ""),
                        "industry": str(data.get("industry") or ""),
                        "main_business": str(data.get("main_business") or ""),
                        "summary_100cn": str(data.get("summary_100cn") or ""),
                        "core_competencies": [str(item) for item in list(data.get("core_competencies") or []) if str(item).strip()],
                        "profit_analysis": {
                            "revenue_structure": str(dict(data.get("profit_analysis") or {}).get("revenue_structure") or ""),
                            "profit_tag": str(dict(data.get("profit_analysis") or {}).get("profit_tag") or ""),
                        },
                        "investment_tags": [str(item) for item in list(data.get("investment_tags") or []) if str(item).strip()],
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
                        "company_name": company_name,
                        "industry": "",
                        "main_business": "",
                        "summary_100cn": "",
                        "core_competencies": [],
                        "profit_analysis": {"revenue_structure": "", "profit_tag": ""},
                        "investment_tags": [],
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
    finally:
        await formula_client.aclose()

    success_rows = [row for row in run_rows if row["status"] == "valid"]
    latencies = [int(row["latency_ms"]) for row in run_rows]
    tag_counts = [len(list(row["investment_tags"])) for row in success_rows]
    summary = {
        "runs": runs,
        "valid_runs": len(success_rows),
        "success_rate": round(len(success_rows) / runs, 4) if runs else 0.0,
        "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0.0,
        "min_latency_ms": min(latencies) if latencies else 0,
        "max_latency_ms": max(latencies) if latencies else 0,
        "avg_tags": round(statistics.mean(tag_counts), 2) if tag_counts else 0.0,
    }
    return {
        "skill": "entity_info_benchmark",
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
