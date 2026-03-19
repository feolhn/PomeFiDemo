from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import inspect
import re
import time
from typing import Any, Awaitable, Callable

import akshare as ak

from pomefi.budgets import BudgetLimits
from pomefi.tools.akshare_tool import extract_network_evidence

from .common import classify_error, make_skill_result, run_tool_grounded_json_skill

TIMELINE_PRICE_START_DATE = "20250101"
TIMELINE_PRICE_TIMEOUT_SECONDS = 8.0
TIMELINE_PRICE_MAX_ATTEMPTS = 3

TIMELINE_EVENT_TOOL_SYSTEM_PROMPT = """
你是A股过去事件研究助手。必须先调用 web_search，再输出证据摘要。
只允许 1 次 web_search，不得追加第二次搜索。
不要直接输出 JSON，不要跳过 tool_call。
tool_call 后必须只输出 1-4 行事件证据。
每行格式固定为：YYYY-MM-DD | 事件标题 | 来源。
如果证据没有明确日期，不得输出该行。
""".strip()

TIMELINE_EVENT_JSON_SYSTEM_PROMPT = """
你是A股时间线抽取助手。必须输出 JSON object，不要 markdown。
事件日期必须落在“今天往前最近三个月”的窗口内。
如果证据里只出现“3月10日”这类月日，没有明确年份，必须结合今天推断正确年份，禁止输出窗口外年份。
schema:
{
  "summary": "string",
  "events": [
    {
      "date": "YYYY-MM-DD",
      "title": "string",
      "source": "string",
      "url": "string"
    }
  ]
}
如果 evidence 中存在带 YYYY-MM-DD 的事件证据行，events 不得为空。
""".strip()


def _load_price_rows(symbol: str) -> dict[str, Any]:
    call_logs: list[dict[str, Any]] = []
    history_df = None
    last_error: Exception | None = None

    def _tx_symbol(code: str) -> str:
        if code.startswith(("6", "9")):
            return f"sh{code}"
        if code.startswith(("4", "8")):
            return f"bj{code}"
        return f"sz{code}"

    def _append_log(interface: str, attempt: int, started: float, *, status: str, error: str) -> None:
        call_logs.append(
            {
                "interface": interface,
                "symbol": symbol,
                "latency_ms": max(int((time.perf_counter() - started) * 1000), 0),
                "status": status,
                "error": error,
                "attempt": attempt,
                "retry_count": attempt - 1,
                "dedup_hit": False,
            }
        )

    for attempt in range(1, TIMELINE_PRICE_MAX_ATTEMPTS + 1):
        started = time.perf_counter()
        try:
            history_df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=TIMELINE_PRICE_START_DATE,
                end_date=datetime.now().strftime("%Y%m%d"),
                adjust="qfq",
                timeout=TIMELINE_PRICE_TIMEOUT_SECONDS,
            )
            _append_log("stock_zh_a_hist", attempt, started, status="ok", error="")
            break
        except Exception as exc:
            last_error = exc
            _append_log("stock_zh_a_hist", attempt, started, status="error", error=str(exc))
            if attempt < TIMELINE_PRICE_MAX_ATTEMPTS:
                time.sleep(0.35 * attempt)

    if history_df is None:
        for attempt in range(1, TIMELINE_PRICE_MAX_ATTEMPTS + 1):
            started = time.perf_counter()
            try:
                history_df = ak.stock_zh_a_hist_tx(
                    symbol=_tx_symbol(symbol),
                    start_date=TIMELINE_PRICE_START_DATE,
                    end_date=datetime.now().strftime("%Y%m%d"),
                    adjust="qfq",
                    timeout=TIMELINE_PRICE_TIMEOUT_SECONDS,
                )
                _append_log("stock_zh_a_hist_tx", attempt, started, status="ok", error="")
                break
            except Exception as exc:
                last_error = exc
                _append_log("stock_zh_a_hist_tx", attempt, started, status="error", error=str(exc))
                if attempt < TIMELINE_PRICE_MAX_ATTEMPTS:
                    time.sleep(0.35 * attempt)

    if history_df is None:
        return {
            "rows": [],
            "asof": "",
            "data_origin": "partial",
            "network_evidence": extract_network_evidence(call_logs),
            "akshare_calls": call_logs,
            "error": f"price_fetch_failed: {last_error}",
        }
    if history_df.empty:
        return {
            "rows": [],
            "asof": "",
            "data_origin": "partial",
            "network_evidence": extract_network_evidence(call_logs),
            "akshare_calls": call_logs,
            "error": "price_history_empty",
        }

    if hasattr(history_df, "rename"):
        history_df = history_df.rename(columns={"日期": "date", "收盘": "close"}).copy()
    raw_rows = history_df.to_dict(orient="records")
    rows = []
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        date_text = str(row.get("date") or row.get("日期") or "")[:10]
        close_value = row.get("close")
        if close_value is None:
            close_value = row.get("收盘")
        rows.append({"date": date_text, "close": close_value, "event_desc": ""})
    return {
        "rows": rows[-90:],
        "asof": str(rows[-1].get("date") or "")[:10] if rows else "",
        "data_origin": "live",
        "network_evidence": extract_network_evidence(call_logs),
        "akshare_calls": call_logs,
        "error": None,
    }


def _normalize_date(text: str) -> str:
    match = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", str(text or ""))
    if not match:
        return ""
    y, m, d = match.group(1).split("-")
    return f"{y}-{m.zfill(2)}-{d.zfill(2)}"


def _repair_event_year(date_text: str, *, today: datetime | None = None) -> str:
    normalized = _normalize_date(date_text)
    if not normalized:
        return ""
    try:
        parsed = datetime.strptime(normalized, "%Y-%m-%d").date()
    except ValueError:
        return ""
    today_date = (today or datetime.now()).date()
    window_start = today_date - timedelta(days=120)
    if window_start <= parsed <= today_date:
        return normalized
    candidates: list[datetime.date] = []
    for year in {window_start.year, today_date.year}:
        try:
            candidate = parsed.replace(year=year)
        except ValueError:
            continue
        if window_start <= candidate <= today_date:
            candidates.append(candidate)
    if not candidates:
        return normalized
    best = min(candidates, key=lambda item: abs((today_date - item).days))
    return best.isoformat()


def _normalize_events(items: Any, *, today: datetime | None = None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in list(items or [])[:8]:
        if not isinstance(item, dict):
            continue
        date_text = _repair_event_year(str(item.get("date") or ""), today=today)
        title = str(item.get("title") or "").strip()
        if not date_text or not title:
            continue
        key = (date_text, title)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "date": date_text,
                "event_date": date_text,
                "title": title,
                "source": str(item.get("source") or "web_search"),
                "url": item.get("url"),
            }
        )
    return normalized[:4]


def _parse_events_from_evidence_lines(text: str, *, today: datetime | None = None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip().lstrip("-").strip()
        if not line or "|" not in line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 3:
            continue
        date_text = _repair_event_year(parts[0], today=today)
        title = parts[1]
        source = parts[2]
        if not date_text or not title:
            continue
        key = (date_text, title)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "date": date_text,
                "event_date": date_text,
                "title": title,
                "source": source or "web_search",
                "url": None,
            }
        )
    return normalized[:4]


def _anchor_events_to_series(
    events: list[dict[str, Any]],
    series: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not events or not series:
        return events, series

    series_dates = [str(item.get("date") or "") for item in series if str(item.get("date") or "")]
    if not series_dates:
        return events, series

    event_desc_by_date: dict[str, list[str]] = {}
    anchored_events: list[dict[str, Any]] = []
    for item in events:
        source_date = str(item.get("event_date") or item.get("date") or "")
        chart_date = ""
        for candidate in reversed(series_dates):
            if candidate <= source_date:
                chart_date = candidate
                break
        if not chart_date:
            chart_date = series_dates[0]
        anchored = dict(item)
        anchored["date"] = chart_date
        anchored_events.append(anchored)
        title = str(anchored.get("title") or "").strip()
        if title:
            event_desc_by_date.setdefault(chart_date, []).append(title)

    anchored_series: list[dict[str, Any]] = []
    for row in series:
        row_copy = dict(row)
        date_text = str(row_copy.get("date") or "")
        titles = event_desc_by_date.get(date_text) or []
        row_copy["event_desc"] = " | ".join(titles[:2])
        anchored_series.append(row_copy)
    return anchored_events, anchored_series


async def _emit_timeline_phase(
    event_handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None,
    *,
    phase: str,
    status: str,
    latency_ms: int,
    error: str | None = None,
) -> None:
    if event_handler is None:
        return
    result = event_handler(
        {
            "type": "timeline_phase",
            "phase": phase,
            "status": status,
            "latency_ms": latency_ms,
            "error": error,
        }
    )
    if inspect.isawaitable(result):
        await result


async def _load_price_branch(
    symbol: str,
    *,
    event_handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        payload = await asyncio.to_thread(_load_price_rows, symbol)
    except Exception as exc:
        latency_ms = max(int((time.perf_counter() - started) * 1000), 0)
        error_text = f"price_fetch_failed: {exc}"
        await _emit_timeline_phase(
            event_handler,
            phase="price_series",
            status="error",
            latency_ms=latency_ms,
            error=error_text,
        )
        return {
            "payload": {
                "rows": [],
                "asof": "",
                "data_origin": "partial",
                "network_evidence": [],
                "akshare_calls": [],
                "error": error_text,
            },
            "status": "error",
            "latency_ms": latency_ms,
            "error": error_text,
        }

    latency_ms = max(int((time.perf_counter() - started) * 1000), 0)
    payload_error = str(payload.get("error") or "").strip() or None
    status = "valid" if list(payload.get("rows") or []) else "error"
    await _emit_timeline_phase(
        event_handler,
        phase="price_series",
        status=status,
        latency_ms=latency_ms,
        error=payload_error,
    )
    return {
        "payload": payload,
        "status": status,
        "latency_ms": latency_ms,
        "error": payload_error,
    }


async def _load_events_branch(
    symbol: str,
    company_name: str,
    *,
    config: Any,
    formula_client: Any,
    event_handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    probe = await run_tool_grounded_json_skill(
        symbol=symbol,
        company_name=company_name,
        config=config,
        formula_client=formula_client,
        tool_system_prompt=TIMELINE_EVENT_TOOL_SYSTEM_PROMPT,
        tool_user_prompts=[
            (
                f"标的：{company_name}({symbol})。"
                f"今天是 {datetime.now().strftime('%Y-%m-%d')}。"
                "不要直接回答。必须先调用 1 次 web_search，搜索过去三个月内影响该公司股价的重要事件。"
                "重点关注财报、订单、产能、产品发布、监管、事故、合作、传闻澄清。"
                "拿到结果后立刻输出 1-4 行事件证据。"
                "每行必须是“YYYY-MM-DD | 事件标题 | 来源”。"
                "禁止输出散文摘要，禁止第二次搜索。"
            ),
            (
                f"标的：{company_name}({symbol})。"
                "不要直接回答。必须调用 1 次 web_search，抽取过去三个月关键事件并输出 1-4 行事件证据；"
                "每行必须是“YYYY-MM-DD | 事件标题 | 来源”；"
                "若未调用工具，本轮视为失败。"
            ),
        ],
        json_system_prompt=TIMELINE_EVENT_JSON_SYSTEM_PROMPT,
        json_user_prompt_builder=lambda evidence_text, _trace: (
            f"标的：{company_name}({symbol})。"
            "请基于下列 tool-grounded 证据，抽取过去三个月关键事件 JSON：\n"
            f"{evidence_text}"
        ),
        event_scope="timeline",
        required_tools={"web_search"},
        event_handler=event_handler,
        disable_tool_thinking=True,
        tool_budget_limits=BudgetLimits(
            max_search_calls=1,
            max_tool_iterations=2,
            max_total_turns=3,
        ),
        json_max_completion_tokens=1536,
    )
    latency_ms = max(int((time.perf_counter() - started) * 1000), 0)
    trace = dict(probe.get("tool_trace") or {})
    payload = dict(probe.get("content_json") or {})
    items = _normalize_events(payload.get("events"))
    if not items:
        items = _parse_events_from_evidence_lines(str(trace.get("final_content") or ""))
    error_text = str(probe.get("error") or "").strip() or None
    status = "valid" if items else "error"
    if error_text is None and not items:
        error_text = "timeline_events_empty"
    await _emit_timeline_phase(
        event_handler,
        phase="events_json",
        status=status,
        latency_ms=latency_ms,
        error=error_text,
    )
    return {
        "payload": {
            "summary": str(payload.get("summary") or "").strip(),
            "events": items,
            "trace": {
                "tool_call_required": True,
                "tool_call_observed": bool(probe.get("tool_call_observed")),
                "retry_count": int(probe.get("retry_count") or 0),
                "observed_tools": list(probe.get("observed_tools") or []),
                "turns": list(trace.get("turns") or []),
                "tool_events": list(trace.get("tool_events") or []),
                "degrade_reason": trace.get("degrade_reason"),
                "final_content": str(trace.get("final_content") or ""),
            },
            "sources": [dict(item) for item in list(probe.get("sources") or []) if isinstance(item, dict)],
            "error": error_text,
        },
        "status": status,
        "latency_ms": latency_ms,
        "error": error_text,
    }


async def _run_timeline_branches(
    symbol: str,
    company_name: str,
    *,
    config: Any = None,
    formula_client: Any = None,
    event_handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    return await asyncio.gather(
        _load_price_branch(symbol, event_handler=event_handler),
        _load_events_branch(
            symbol,
            company_name,
            config=config,
            formula_client=formula_client,
            event_handler=event_handler,
        ),
    )


def _build_timeline_payloads(
    symbol: str,
    company_name: str,
    *,
    price_branch: dict[str, Any],
    events_branch: dict[str, Any],
) -> dict[str, Any]:
    price_payload = dict(price_branch.get("payload") or {})
    events_payload = dict(events_branch.get("payload") or {})
    price_rows = [dict(item) for item in list(price_payload.get("rows") or []) if isinstance(item, dict)]
    timeline_events = [dict(item) for item in list(events_payload.get("events") or []) if isinstance(item, dict)]
    data_origin = str(price_payload.get("data_origin") or "partial")
    network_evidence = [dict(item) for item in list(price_payload.get("network_evidence") or []) if isinstance(item, dict)]
    akshare_calls = [dict(item) for item in list(price_payload.get("akshare_calls") or []) if isinstance(item, dict)]
    price_error = str(price_payload.get("error") or "").strip()
    asof = str(price_payload.get("asof") or "")
    events_summary = str(events_payload.get("summary") or "").strip()
    events_trace = dict(events_payload.get("trace") or {})
    if not timeline_events:
        timeline_events = _parse_events_from_evidence_lines(str(events_trace.get("final_content") or ""))
    sources: list[dict[str, Any]] = [
        {"source": "AkShare", "kind": "akshare", "title": f"{symbol} 近三个月K线", "published_at": asof, "url": None}
    ]
    sources.extend([dict(item) for item in list(events_payload.get("sources") or []) if isinstance(item, dict)])
    timeline_events, price_rows = _anchor_events_to_series(timeline_events, price_rows)
    trace_payload = {
        "tool_call_required": True,
        "tool_call_observed": bool(events_trace.get("tool_call_observed")),
        "retry_count": int(events_trace.get("retry_count") or 0),
        "observed_tools": list(events_trace.get("observed_tools") or []),
        "turns": list(events_trace.get("turns") or []),
        "tool_events": list(events_trace.get("tool_events") or []),
        "degrade_reason": events_trace.get("degrade_reason"),
        "phase_latency_ms": {
            "price_series": int(price_branch.get("latency_ms") or 0),
            "events_json": int(events_branch.get("latency_ms") or 0),
        },
        "phase_status": {
            "price_series": str(price_branch.get("status") or "unknown"),
            "events_json": str(events_branch.get("status") or "unknown"),
        },
        "phase_error": {
            "price_series": price_branch.get("error"),
            "events_json": events_branch.get("error"),
        },
    }
    return {
        "price_rows": price_rows,
        "timeline_events": timeline_events,
        "data_origin": data_origin,
        "network_evidence": network_evidence,
        "akshare_calls": akshare_calls,
        "price_error": price_error,
        "asof": asof,
        "events_summary": events_summary,
        "sources": sources,
        "trace_payload": trace_payload,
    }


def _build_timeline_result(
    symbol: str,
    company_name: str,
    *,
    price_branch: dict[str, Any],
    events_branch: dict[str, Any],
) -> dict[str, Any]:
    payloads = _build_timeline_payloads(
        symbol,
        company_name,
        price_branch=price_branch,
        events_branch=events_branch,
    )
    price_rows = payloads["price_rows"]
    timeline_events = payloads["timeline_events"]
    data_origin = payloads["data_origin"]
    network_evidence = payloads["network_evidence"]
    akshare_calls = payloads["akshare_calls"]
    price_error = payloads["price_error"]
    sources = payloads["sources"]
    trace_payload = payloads["trace_payload"]

    if not price_rows:
        error_text = price_error or str(price_branch.get("error") or "price_fetch_failed")
        error_category = classify_error(error_text)
        unrecovered_reason_code = "AKSHARE_NETWORK_UNRECOVERED" if network_evidence or error_category in {"network", "rate_limit"} else "UNKNOWN_UNRECOVERED"
        return make_skill_result(
            status="error",
            data={
                "symbol": symbol,
                "company_name": company_name,
                "series": [],
                "events": timeline_events,
                "summary": "价格折线图抓取失败，timeline 无法生成。",
                "data_origin": data_origin,
                "network_evidence": network_evidence,
                "akshare_calls": akshare_calls,
                "trace": trace_payload,
                "recovered": False,
                "unrecovered_reason_code": unrecovered_reason_code,
            },
            sources=sources,
            error=error_text,
            error_category=error_category,
            data_ready=False,
            is_critical=True,
        )

    if not timeline_events:
        error_text = str(events_branch.get("error") or "timeline_events_unavailable")
        return make_skill_result(
            status="error",
            data={
                "symbol": symbol,
                "company_name": company_name,
                "series": price_rows,
                "events": [],
                "summary": "过去三个月关键事件抓取失败，timeline 无法生成。",
                "data_origin": data_origin,
                "network_evidence": network_evidence,
                "akshare_calls": akshare_calls,
                "trace": trace_payload,
                "recovered": False,
                "unrecovered_reason_code": "TIMELINE_EVENTS_UNRECOVERED",
            },
            sources=sources,
            error=error_text,
            error_category=classify_error(error_text),
            data_ready=False,
            is_critical=True,
        )

    return make_skill_result(
        status="valid",
        data={
            "symbol": symbol,
            "company_name": company_name,
            "series": price_rows,
            "events": timeline_events,
            "summary": payloads["events_summary"] or f"已抓取近三个月价格与 {len(timeline_events)} 个关键事件。",
            "data_origin": data_origin,
            "network_evidence": network_evidence,
            "akshare_calls": akshare_calls,
            "trace": trace_payload,
            "recovered": True,
            "unrecovered_reason_code": None,
        },
        sources=payloads["sources"],
        error=None,
        error_category=None,
        data_ready=True,
        is_critical=True,
    )


def _build_timeline_debug_result(
    symbol: str,
    company_name: str,
    *,
    branch_name: str,
    branch: dict[str, Any],
) -> dict[str, Any]:
    payload = dict(branch.get("payload") or {})
    latency_ms = int(branch.get("latency_ms") or 0)
    error_text = str(branch.get("error") or payload.get("error") or "").strip() or None
    if branch_name == "akshare":
        rows = [dict(item) for item in list(payload.get("rows") or []) if isinstance(item, dict)]
        return make_skill_result(
            status="valid" if rows else "error",
            data={
                "symbol": symbol,
                "company_name": company_name,
                "series": rows,
                "asof": str(payload.get("asof") or ""),
                "data_origin": str(payload.get("data_origin") or "partial"),
                "network_evidence": [dict(item) for item in list(payload.get("network_evidence") or []) if isinstance(item, dict)],
                "akshare_calls": [dict(item) for item in list(payload.get("akshare_calls") or []) if isinstance(item, dict)],
                "trace": {
                    "phase_latency_ms": {"price_series": latency_ms},
                    "phase_status": {"price_series": str(branch.get("status") or "unknown")},
                    "phase_error": {"price_series": error_text},
                },
            },
            sources=[
                {
                    "source": "AkShare",
                    "kind": "akshare",
                    "title": f"{symbol} 近三个月K线",
                    "published_at": str(payload.get("asof") or ""),
                    "url": None,
                }
            ],
            error=error_text,
            error_category=classify_error(error_text) if error_text else None,
            data_ready=bool(rows),
            is_critical=True,
        )
    events = [dict(item) for item in list(payload.get("events") or []) if isinstance(item, dict)]
    trace = dict(payload.get("trace") or {})
    return make_skill_result(
        status="valid" if events else "error",
        data={
            "symbol": symbol,
            "company_name": company_name,
            "events": events,
            "summary": str(payload.get("summary") or "").strip(),
            "trace": trace,
        },
        sources=[dict(item) for item in list(payload.get("sources") or []) if isinstance(item, dict)],
        error=error_text,
        error_category=classify_error(error_text) if error_text else None,
        data_ready=bool(events),
        is_critical=True,
    )


async def get_timeline(
    symbol: str,
    company_name: str,
    *,
    config: Any = None,
    formula_client: Any = None,
    event_handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None = None,
) -> dict[str, Any]:
    price_branch, events_branch = await _run_timeline_branches(
        symbol,
        company_name,
        config=config,
        formula_client=formula_client,
        event_handler=event_handler,
    )
    return _build_timeline_result(
        symbol,
        company_name,
        price_branch=price_branch,
        events_branch=events_branch,
    )


async def get_timeline_debug_bundle(
    symbol: str,
    company_name: str,
    *,
    config: Any = None,
    formula_client: Any = None,
    event_handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None = None,
) -> dict[str, Any]:
    price_branch, events_branch = await _run_timeline_branches(
        symbol,
        company_name,
        config=config,
        formula_client=formula_client,
        event_handler=event_handler,
    )
    return {
        "merged": _build_timeline_result(
            symbol,
            company_name,
            price_branch=price_branch,
            events_branch=events_branch,
        ),
        "akshare": _build_timeline_debug_result(
            symbol,
            company_name,
            branch_name="akshare",
            branch=price_branch,
        ),
        "kimi": _build_timeline_debug_result(
            symbol,
            company_name,
            branch_name="kimi",
            branch=events_branch,
        ),
    }
