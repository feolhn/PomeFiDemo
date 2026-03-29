from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
import importlib.metadata
import os
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)
if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_TEXT)

from pomefi.config import resolve_kimi_config
from pomefi.tools.formula import FormulaToolClient

SKILLS = {"summary", "entity_info", "timeline", "watch_calendar", "relationship"}
FORMULA_URIS = [
    "moonshot/date:latest",
    "moonshot/web-search:latest",
]
ENTITY_INFO_FORMULA_URIS = [
    "moonshot/web-search:latest",
]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "debug_outputs" / "stock_wiki"


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def collect_runtime_info() -> dict[str, Any]:
    return {
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "cwd": str(PROJECT_ROOT),
        "venv": os.environ.get("VIRTUAL_ENV"),
        "packages": {
            "akshare": _package_version("akshare"),
            "python-dotenv": _package_version("python-dotenv"),
            "httpx": _package_version("httpx"),
            "openai": _package_version("openai"),
        },
        "proxy_env": {
            key: os.environ.get(key)
            for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "all_proxy", "no_proxy")
            if os.environ.get(key) is not None
        },
    }


def _finalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(payload)
    enriched.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
    enriched["runtime"] = collect_runtime_info()
    return enriched


async def get_stock_summary(symbol: str, company_name: str) -> dict[str, Any]:
    from pomefi.stock_wiki.skills.stock_summary import get_stock_summary as _get_stock_summary

    return await _get_stock_summary(symbol, company_name)


async def get_timeline(symbol: str, company_name: str, *, event_handler: Any | None = None) -> dict[str, Any]:
    from pomefi.stock_wiki.skills.timeline import get_timeline as _get_timeline

    config = resolve_kimi_config()
    if not config.api_key:
        raise RuntimeError("timeline requires KIMI_API_KEY")
    formula_client = FormulaToolClient(base_url=config.base_url, api_key=config.api_key)
    try:
        await formula_client.load_tools(FORMULA_URIS)
        return await _get_timeline(
            symbol,
            company_name,
            config=config,
            formula_client=formula_client,
            event_handler=event_handler,
        )
    finally:
        await formula_client.aclose()


async def get_timeline_debug_bundle(symbol: str, company_name: str, *, event_handler: Any | None = None) -> dict[str, Any]:
    from pomefi.stock_wiki.skills.timeline import get_timeline_debug_bundle as _get_timeline_debug_bundle

    config = resolve_kimi_config()
    if not config.api_key:
        raise RuntimeError("timeline requires KIMI_API_KEY")
    formula_client = FormulaToolClient(base_url=config.base_url, api_key=config.api_key)
    try:
        await formula_client.load_tools(FORMULA_URIS)
        return await _get_timeline_debug_bundle(
            symbol,
            company_name,
            config=config,
            formula_client=formula_client,
            event_handler=event_handler,
        )
    finally:
        await formula_client.aclose()


async def get_entity_info(
    symbol: str,
    company_name: str,
    *,
    config: Any,
    formula_client: Any,
    event_handler: Any | None = None,
) -> dict[str, Any]:
    from pomefi.stock_wiki.skills.entity_info import get_entity_info as _get_entity_info

    return await _get_entity_info(
        symbol,
        company_name,
        config=config,
        formula_client=formula_client,
        event_handler=event_handler,
    )


async def get_watch_calendar(
    symbol: str,
    company_name: str,
    *,
    config: Any,
    formula_client: Any,
    event_handler: Any | None = None,
) -> dict[str, Any]:
    from pomefi.stock_wiki.skills.watch_calendar import get_watch_calendar as _get_watch_calendar

    return await _get_watch_calendar(
        symbol,
        company_name,
        config=config,
        formula_client=formula_client,
        event_handler=event_handler,
    )


async def get_relationship(
    symbol: str,
    company_name: str,
    *,
    config: Any,
    formula_client: Any,
    event_handler: Any | None = None,
) -> dict[str, Any]:
    from pomefi.stock_wiki.skills.relationship import get_relationship as _get_relationship

    return await _get_relationship(
        symbol,
        company_name,
        config=config,
        formula_client=formula_client,
        event_handler=event_handler,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Debug one stock wiki skill independently.")
    parser.add_argument("--skill", required=True, choices=sorted(SKILLS))
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--company-name", default="")
    parser.add_argument("--output", default="")
    return parser


async def _run_skill(skill: str, symbol: str, company_name: str) -> dict[str, Any]:
    config = resolve_kimi_config()
    events: list[dict[str, Any]] = []

    async def _event_handler(event: dict[str, Any]) -> None:
        events.append(dict(event))

    if skill == "summary":
        result = await get_stock_summary(symbol, company_name or symbol)
        return _finalize_payload({"skill": skill, "result": result, "trace": {"events": events}})

    if not config.api_key:
        raise RuntimeError(f"{skill} requires KIMI_API_KEY")

    if skill == "timeline":
        result = await get_timeline(symbol, company_name or symbol, event_handler=_event_handler)
        return _finalize_payload({"skill": skill, "result": result, "trace": {"events": events}})

    if skill == "entity_info":
        formula_client = FormulaToolClient(base_url=config.base_url, api_key=config.api_key)
        try:
            await formula_client.load_tools(ENTITY_INFO_FORMULA_URIS)
            result = await get_entity_info(
                symbol,
                company_name or symbol,
                config=config,
                formula_client=formula_client,
                event_handler=_event_handler,
            )
            return _finalize_payload({"skill": skill, "result": result, "trace": {"events": events}})
        finally:
            await formula_client.aclose()

    formula_client = FormulaToolClient(base_url=config.base_url, api_key=config.api_key)
    try:
        await formula_client.load_tools(FORMULA_URIS)
        if skill == "watch_calendar":
            result = await get_watch_calendar(
                symbol,
                company_name or symbol,
                config=config,
                formula_client=formula_client,
                event_handler=_event_handler,
            )
        elif skill == "relationship":
            result = await get_relationship(
                symbol,
                company_name or symbol,
                config=config,
                formula_client=formula_client,
                event_handler=_event_handler,
            )
        else:
            raise RuntimeError(f"unsupported skill: {skill}")
        return _finalize_payload({"skill": skill, "result": result, "trace": {"events": events}})
    finally:
        await formula_client.aclose()


async def _run_timeline_bundle(symbol: str, company_name: str) -> dict[str, Any]:
    events: list[dict[str, Any]] = []

    async def _event_handler(event: dict[str, Any]) -> None:
        events.append(dict(event))

    bundle = await get_timeline_debug_bundle(symbol, company_name or symbol, event_handler=_event_handler)
    return _finalize_payload(
        {
            "skill": "timeline",
            "result": bundle["merged"],
            "trace": {"events": events},
            "branches": {
                "akshare": bundle["akshare"],
                "kimi": bundle["kimi"],
            },
        }
    )


def default_output_path(skill: str) -> Path:
    return DEFAULT_OUTPUT_DIR / f"{skill}.json"


def write_skill_output(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_error_payload(skill: str, symbol: str, company_name: str, error: BaseException) -> dict[str, Any]:
    message = f"{type(error).__name__}: {error}"
    return _finalize_payload({
        "skill": skill,
        "result": {
            "skill": skill,
            "status": "error",
            "latency_ms": 0,
            "data": {
                "symbol": symbol,
                "company_name": company_name,
            },
            "sources": [],
            "error": message,
            "error_category": "runtime",
            "data_ready": False,
            "is_critical": False,
        },
        "trace": {
            "events": [],
            "error": message,
        },
    })


def main() -> int:
    args = _build_parser().parse_args()
    had_error = False
    try:
        payload = asyncio.run(_run_skill(args.skill, args.symbol, args.company_name))
    except Exception as exc:  # pragma: no cover - debug script fallback
        payload = build_error_payload(args.skill, args.symbol, args.company_name, exc)
        had_error = True
    if args.output:
        write_skill_output(payload, Path(args.output))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
