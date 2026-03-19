from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any

from pomefi.config import KimiConfig
from pomefi.streaming.events import EVENT_SESSION_DONE, EVENT_SESSION_ERROR, EVENT_SESSION_START, EVENT_SKILL_RESULT_READY, make_event
from pomefi.tools.formula import FormulaToolClient

from .aggregator import aggregate_stock_wiki_payload
from .orchestrator import run_parallel_skills_stream
from .router import route_query
from .skills import (
    get_entity_info,
    get_relationship,
    get_stock_summary,
    get_timeline,
    get_watch_calendar,
)

FORMULA_URIS = [
    "moonshot/date:latest",
    "moonshot/web-search:latest",
]


def _placeholder_result(skill: str, message: str, *, pending: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {"summary": message}
    if skill == "relationship":
        data = {"summary": message, "pending": pending, "nodes": [], "edges": []}
    elif skill == "timeline":
        data = {"summary": message, "series": [], "events": []}
    elif skill == "watch_calendar":
        data = {"summary": message, "items": []}
    return {
        "skill": skill,
        "status": "error",
        "latency_ms": 0,
        "data": data,
        "sources": [],
        "error": "router_blocked",
        "error_category": "routing",
        "data_ready": False,
        "is_critical": skill in {"summary", "timeline"},
    }


def _blocked_skill_results(message: str) -> dict[str, dict[str, Any]]:
    return {
        "summary": _placeholder_result("summary", message),
        "entity_info": _placeholder_result("entity_info", message),
        "timeline": _placeholder_result("timeline", message),
        "watch_calendar": _placeholder_result("watch_calendar", message),
        "relationship": _placeholder_result("relationship", message, pending=False),
    }


def _blocked_payload(
    *,
    question: str,
    route: dict[str, Any],
    reason: str,
    message: str,
) -> dict[str, Any]:
    results = _blocked_skill_results(message)
    card = aggregate_stock_wiki_payload(
        question=question,
        symbol="",
        company_name="",
        skill_results=results,
    )
    card["quality_status"] = "error"
    card["metadata"]["degrade_reason"] = reason
    card["metadata"]["execution_status"] = "failed"
    card["metadata"]["failure_reason_code"] = "ROUTING_UNRESOLVED"
    card["metadata"]["failure_reason_message"] = (
        "当前问题不在支持范围内，请输入A股单标的问题。"
        if reason == "unsupported_scope"
        else "未解析到A股代码，请输入6位代码或准确公司名。"
    )
    card["metadata"]["failure_stage"] = "routing"
    card["metadata"]["failure_evidence"] = {"route": route, "reason": reason}
    return {"card": card, "trace": {"route": route, "skill_results": results, "events": []}, "local_context": {}}


def _collect_tool_events(skill_results: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for skill_name in ("relationship", "timeline", "watch_calendar"):
        result = dict(skill_results.get(skill_name) or {})
        skill_trace = dict((result.get("data") or {}).get("trace") or {})
        for item in list(skill_trace.get("tool_events") or []):
            if isinstance(item, dict):
                events.append(dict(item))

    for skill_name in ("summary", "timeline", "watch_calendar"):
        result = dict(skill_results.get(skill_name) or {})
        data = dict(result.get("data") or {})
        data_origin = str(data.get("data_origin") or "").strip()
        if data_origin:
            events.append(
                {
                    "tool_name": "akshare_data_origin",
                    "tool_call_id": f"{skill_name}_akshare_origin",
                    "source": "local",
                    "formula_uri": None,
                    "arguments_text": "{}",
                    "arguments_dict": {"skill": skill_name},
                    "jsonable_ok": None,
                    "tool_content_preview": f"{skill_name} data_origin={data_origin}",
                }
            )
        for index, evidence in enumerate(list(data.get("network_evidence") or [])):
            if not isinstance(evidence, dict):
                continue
            interface = str(evidence.get("interface") or "akshare")
            status = str(evidence.get("status") or "error")
            error_text = str(evidence.get("error") or "").strip()
            preview = f"{skill_name} {interface} {status}".strip()
            if error_text:
                preview = f"{preview}: {error_text}"[:200]
            events.append(
                {
                    "tool_name": interface,
                    "tool_call_id": f"{skill_name}_network_{index}",
                    "source": "local",
                    "formula_uri": None,
                    "arguments_text": "{}",
                    "arguments_dict": {"skill": skill_name},
                    "jsonable_ok": None,
                    "tool_content_preview": preview,
                }
            )
        for index, call in enumerate(list(data.get("akshare_calls") or [])):
            if not isinstance(call, dict):
                continue
            interface = str(call.get("interface") or "akshare")
            error_text = str(call.get("error") or "").strip()
            status = str(call.get("status") or "")
            preview = f"{interface} {status}".strip()
            if error_text:
                preview = f"{preview}: {error_text}"[:200]
            events.append(
                {
                    "tool_name": interface,
                    "tool_call_id": f"{skill_name}_akshare_{index}",
                    "source": "local",
                    "formula_uri": None,
                    "arguments_text": "{}",
                    "arguments_dict": {"symbol": call.get("symbol")},
                    "jsonable_ok": None,
                    "tool_content_preview": preview,
                }
            )

        error = str(result.get("error") or "").strip()
        if not error:
            continue
        events.append(
            {
                "tool_name": "akshare",
                "tool_call_id": f"{skill_name}_akshare",
                "source": "local",
                "formula_uri": None,
                "arguments_text": "{}",
                "arguments_dict": {},
                "jsonable_ok": None,
                "tool_content_preview": error[:200],
            }
        )
    return events


async def run_stock_wiki_analysis_stream(
    *,
    question: str,
    config: KimiConfig,
    stock_table_loader: Callable[[], list[dict[str, str]]],
) -> AsyncIterator[dict[str, Any]]:
    yield make_event(EVENT_SESSION_START, question=question, model=config.model)

    route = route_query(question=question, stock_table_loader=stock_table_loader)
    yield make_event("route_resolved", route=route)

    symbol = str(route.get("symbol") or "")
    company_name = str(route.get("company_name") or "")
    reason = str(route.get("reason") or "")

    if reason == "unsupported_scope":
        payload = _blocked_payload(
            question=question,
            route=route,
            reason="unsupported_scope",
            message="当前版本仅支持 A 股股票问题。",
        )
        yield make_event(EVENT_SESSION_DONE, payload=payload)
        return

    if not symbol:
        payload = _blocked_payload(
            question=question,
            route=route,
            reason="symbol_unresolved",
            message="未解析到A股代码，请输入6位代码或准确公司名。",
        )
        yield make_event(EVENT_SESSION_DONE, payload=payload)
        return

    formula_client = FormulaToolClient(base_url=config.base_url, api_key=config.api_key)
    orchestrator_events: list[dict[str, Any]] = []
    try:
        await formula_client.load_tools(FORMULA_URIS)
        yield make_event("formula_tools_loaded", tools=formula_client.tool_to_uri)

        runners = {
            "summary": lambda s, n: get_stock_summary(s, n),
            "entity_info": lambda s, n, **kw: get_entity_info(s, n, config=config, **kw),
            "timeline": lambda s, n, **kw: get_timeline(s, n, config=config, formula_client=formula_client, **kw),
            "watch_calendar": lambda s, n, **kw: get_watch_calendar(s, n, config=config, formula_client=formula_client, **kw),
            "relationship": lambda s, n, **kw: get_relationship(s, n, config=config, formula_client=formula_client, **kw),
        }

        skill_results: dict[str, dict[str, Any]] = {}
        async for event in run_parallel_skills_stream(
            symbol=symbol,
            company_name=company_name,
            runners=runners,
        ):
            orchestrator_events.append(event)
            if event.get("type") == EVENT_SKILL_RESULT_READY:
                maybe_result = event.get("result")
                skill_name = str(event.get("skill") or "")
                if skill_name and isinstance(maybe_result, dict):
                    skill_results[skill_name] = dict(maybe_result)
            yield event
            if event.get("type") == "orchestrator_done":
                maybe_results = event.get("skill_results")
                if isinstance(maybe_results, dict):
                    skill_results.update({str(name): dict(result) for name, result in maybe_results.items() if isinstance(result, dict)})
            if event.get("type") == "orchestrator_error":
                raise RuntimeError(str(event.get("error") or "orchestrator_error"))

        if not skill_results:
            raise RuntimeError("orchestrator_done_missing")

        card = aggregate_stock_wiki_payload(
            question=question,
            symbol=symbol,
            company_name=company_name,
            skill_results=skill_results,
        )
        payload = {
            "card": card,
            "trace": {
                "route": route,
                "skill_results": skill_results,
                "events": orchestrator_events,
                "tool_events": _collect_tool_events(skill_results),
            },
            "local_context": {},
        }
        yield make_event(EVENT_SESSION_DONE, payload=payload)
    except Exception as exc:
        payload = _blocked_payload(
            question=question,
            route=route,
            reason="engine_runtime_error",
            message=f"运行失败：{exc}",
        )
        yield make_event(EVENT_SESSION_ERROR, error=str(exc), payload=payload)
        yield make_event(EVENT_SESSION_DONE, payload=payload)
    finally:
        await formula_client.aclose()


async def run_stock_wiki_analysis(
    *,
    question: str,
    config: KimiConfig,
    stock_table_loader: Callable[[], list[dict[str, str]]],
) -> dict[str, Any]:
    payload: dict[str, Any] | None = None
    async for event in run_stock_wiki_analysis_stream(
        question=question,
        config=config,
        stock_table_loader=stock_table_loader,
    ):
        if event.get("type") == EVENT_SESSION_DONE:
            maybe_payload = event.get("payload")
            if isinstance(maybe_payload, dict):
                payload = maybe_payload
    if payload is None:
        raise RuntimeError("session_done_missing_payload")
    return payload


async def run_stock_wiki_analysis_quick(
    *,
    question: str,
    config: KimiConfig,
    stock_table_loader: Callable[[], list[dict[str, str]]],
) -> dict[str, Any]:
    # 兼容旧调用方：仍然提供一次性返回。
    return await run_stock_wiki_analysis(
        question=question,
        config=config,
        stock_table_loader=stock_table_loader,
    )
