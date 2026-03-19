from __future__ import annotations

import asyncio
from collections.abc import Callable
import json
import os
from pathlib import Path
import sys
from typing import Any

import akshare as ak
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)
if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_TEXT)

from pomefi.config import resolve_kimi_config
from pomefi.stock_wiki import aggregate_stock_wiki_payload, run_stock_wiki_analysis, run_stock_wiki_analysis_stream
from pomefi.stock_wiki.router import resolve_symbol_from_table
from pomefi.streaming.events import EVENT_LLM_CONTENT_DELTA, EVENT_LLM_REASONING_DELTA, EVENT_SESSION_DONE, EVENT_SKILL_RESULT_READY
from pomefi.ui import (
    create_live_panel_slots,
    inject_page_styles,
    render_cards_export_button,
    render_header,
    render_progressive_cards,
    render_question_hint,
    render_result_card,
    render_status,
    render_debug,
    update_live_panel,
)


def _preview_text(value: Any, limit: int = 160) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= limit else f"{text[:limit]}..."


@st.cache_data(ttl=3600, show_spinner=False)
def _load_stock_table() -> list[dict[str, str]]:
    stock_info = ak.stock_info_a_code_name()
    if stock_info.empty:
        return []
    rows: list[dict[str, str]] = []
    for row in stock_info[["code", "name"]].to_dict(orient="records"):
        code = str(row.get("code") or "").strip()
        name = str(row.get("name") or "").strip()
        if code and name:
            rows.append({"code": code, "name": name})
    return rows


def resolve_symbol(question: str) -> tuple[str | None, str | None]:
    # 当前是轻量 symbol resolver，不是独立 resolver module。
    return resolve_symbol_from_table(question, _load_stock_table())


def _validate_app_config(*, use_local_fixture: bool = False) -> tuple[bool, str]:
    if _local_fixture_mode_enabled(use_local_fixture=use_local_fixture):
        return True, ""
    config = resolve_kimi_config()
    if not config.api_key:
        return False, "缺少 KIMI_API_KEY。"
    if config.model == "kimi-k2.5" and config.temperature != 1.0:
        return False, "KIMI_MODEL=kimi-k2.5 时，KIMI_TEMPERATURE 必须为 1.0。"
    return True, ""


def _default_local_fixture_dir() -> Path | None:
    path = PROJECT_ROOT / "debug_outputs" / "stock_wiki"
    required = ("summary", "entity_info", "timeline", "watch_calendar", "relationship")
    if path.exists() and all((path / f"{skill}.json").exists() for skill in required):
        return path
    return None


def _configured_local_fixture_dir() -> Path | None:
    raw = str(os.getenv("POMEFI_LOCAL_FIXTURE_DIR") or "").strip()
    if not raw:
        return None
    path = Path(raw)
    return path if path.exists() else None


def _active_local_fixture_dir(*, use_local_fixture: bool = False) -> Path | None:
    configured = _configured_local_fixture_dir()
    if configured is not None:
        return configured
    if use_local_fixture:
        return _default_local_fixture_dir()
    return None


def _local_fixture_mode_enabled(*, use_local_fixture: bool = False) -> bool:
    return _active_local_fixture_dir(use_local_fixture=use_local_fixture) is not None


def _load_local_fixture_payload(question: str, fixture_dir: Path) -> dict[str, Any]:
    if fixture_dir is None:
        raise RuntimeError("local_fixture_dir_missing")
    skill_results: dict[str, dict[str, Any]] = {}
    symbol = ""
    company_name = ""
    for skill in ("summary", "entity_info", "timeline", "watch_calendar", "relationship"):
        path = fixture_dir / f"{skill}.json"
        if not path.exists():
            raise RuntimeError(f"missing fixture: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        result = payload.get("result")
        if not isinstance(result, dict):
            raise RuntimeError(f"invalid result payload: {path}")
        skill_results[skill] = dict(result)
        if not symbol:
            symbol = str(((result.get("data") or {}).get("symbol")) or payload.get("symbol") or "").strip()
        if not company_name:
            company_name = str(((result.get("data") or {}).get("company_name")) or payload.get("company_name") or "").strip()

    card = aggregate_stock_wiki_payload(
        question=question,
        symbol=symbol,
        company_name=company_name,
        skill_results=skill_results,
    )
    return {
        "card": card,
        "trace": {
            "route": {"symbol": symbol, "company_name": company_name, "mode": "local_fixture"},
            "skill_results": skill_results,
            "events": [],
            "tool_events": [],
        },
        "local_context": {},
    }


def _error_payload(question: str, model: str, reason: str, message: str) -> dict[str, Any]:
    skills = {
        "summary": {"skill": "summary", "status": "error", "latency_ms": 0, "data": {"summary": message}, "sources": [], "error": reason, "data_ready": False, "is_critical": True},
        "entity_info": {"skill": "entity_info", "status": "error", "latency_ms": 0, "data": {"summary": message}, "sources": [], "error": reason, "data_ready": False, "is_critical": False},
        "timeline": {"skill": "timeline", "status": "error", "latency_ms": 0, "data": {"summary": message, "series": [], "events": []}, "sources": [], "error": reason, "data_ready": False, "is_critical": True},
        "watch_calendar": {"skill": "watch_calendar", "status": "error", "latency_ms": 0, "data": {"summary": message, "items": []}, "sources": [], "error": reason, "data_ready": False, "is_critical": False},
        "relationship": {"skill": "relationship", "status": "error", "latency_ms": 0, "data": {"summary": message, "pending": False, "nodes": [], "edges": []}, "sources": [], "error": reason, "data_ready": False, "is_critical": False},
    }
    return {
        "card": {
            "data": {
                "question": question,
                "summary": skills["summary"]["data"],
                "entity_info": skills["entity_info"]["data"],
                "timeline": skills["timeline"]["data"],
                "watch_calendar": skills["watch_calendar"]["data"],
                "relationship": skills["relationship"]["data"],
                "skills": skills,
            },
            "metadata": {
                "trace_id": "trace_error",
                "model": model,
                "partial_release": False,
                "relationship_pending": False,
                "degrade_reason": reason,
                "strict_fail": True,
                "critical_failures": ["summary", "timeline"],
                "failure_mask": {"summary": reason, "timeline": reason},
                "execution_status": "failed",
                "failure_reason_code": "UNKNOWN_UNRECOVERED",
                "failure_reason_message": message,
                "failure_stage": "routing",
                "failure_evidence": {"source": "app", "reason": reason},
            },
            "quality_status": "error",
            "sources": [],
        },
        "trace": {"route": {}, "skill_results": skills, "events": []},
        "local_context": {},
    }


async def _run_analysis(question: str) -> dict[str, Any]:
    # 页面层到研究引擎的主胶水层。
    config = resolve_kimi_config()
    return await run_stock_wiki_analysis(
        question=question,
        config=config,
        stock_table_loader=_load_stock_table,
    )


async def _run_analysis_stream(question: str):
    config = resolve_kimi_config()
    async for event in run_stock_wiki_analysis_stream(
        question=question,
        config=config,
        stock_table_loader=_load_stock_table,
    ):
        yield event


def run_analysis(question: str) -> dict[str, Any]:
    # 同步包装层，给脚本和测试复用。
    return asyncio.run(_run_analysis(question))


def run_analysis_stream(
    question: str,
    on_event: Callable[[dict[str, Any]], None] | None = None,
    *,
    use_local_fixture: bool = False,
) -> dict[str, Any]:
    fixture_dir = _active_local_fixture_dir(use_local_fixture=use_local_fixture)
    if fixture_dir is not None:
        payload = _load_local_fixture_payload(question, fixture_dir)
        if on_event is not None:
            route = dict((payload.get("trace") or {}).get("route") or {})
            route["fixture_dir"] = str(fixture_dir)
            on_event({"type": "route_resolved", "route": route})
            for skill, result in dict((payload.get("trace") or {}).get("skill_results") or {}).items():
                on_event({"type": "skill_result_ready", "skill": skill, "result": dict(result)})
            on_event({"type": EVENT_SESSION_DONE, "payload": payload})
        return payload

    async def _runner() -> dict[str, Any]:
        payload: dict[str, Any] | None = None
        async for event in _run_analysis_stream(question):
            if on_event is not None:
                on_event(event)
            if event.get("type") == EVENT_SESSION_DONE:
                maybe_payload = event.get("payload")
                if isinstance(maybe_payload, dict):
                    payload = maybe_payload
        if payload is None:
            raise RuntimeError("session_done_missing_payload")
        return payload

    return asyncio.run(_runner())


def _new_live_state() -> dict[str, Any]:
    return {
        "thinking": "",
        "final_output": "",
        "tool_lines": [],
        "skill_states": {
            "summary": "pending",
            "entity_info": "pending",
            "timeline": "pending",
            "watch_calendar": "pending",
            "relationship": "pending",
        },
        "events": [],
    }


def _new_live_card_store() -> dict[str, Any]:
    return {
        "route": {},
        "cards": {
            "summary": {"state": "pending", "result": None},
            "entity_info": {"state": "pending", "result": None},
            "timeline": {"state": "pending", "result": None},
            "watch_calendar": {"state": "pending", "result": None},
            "relationship": {"state": "pending", "result": None},
        },
        "events": [],
        "session_done": False,
    }


def _card_store_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    card = dict(payload.get("card") or {})
    data = dict(card.get("data") or {})
    metadata = dict(card.get("metadata") or {})
    skills = dict(data.get("skills") or {})
    store = _new_live_card_store()
    store["route"] = {
        "symbol": metadata.get("symbol"),
        "company_name": metadata.get("company_name"),
        "question": data.get("question"),
    }
    for skill in list(store["cards"].keys()):
        result = skills.get(skill)
        if not isinstance(result, dict):
            section = data.get(skill)
            if isinstance(section, dict):
                result = {
                    "skill": skill,
                    "status": "valid",
                    "latency_ms": 0,
                    "data": dict(section),
                    "sources": [],
                    "error": None,
                    "error_category": None,
                    "data_ready": True,
                    "is_critical": skill in {"summary", "timeline"},
                }
        if not isinstance(result, dict):
            continue
        status = str(result.get("status") or "pending")
        store["cards"][skill] = {
            "state": "valid" if status == "valid" else "error",
            "result": dict(result),
        }
    store["session_done"] = True
    return store


def _flatten_skill_event(raw_event: dict[str, Any]) -> dict[str, Any]:
    event = dict(raw_event)
    if event.get("type") == "relationship_event" and isinstance(event.get("event"), dict):
        return dict(event.get("event") or {})
    return event


def _apply_live_event(state: dict[str, Any], event: dict[str, Any]) -> None:
    state["events"].append(event)
    event_type = str(event.get("type") or "")

    if event_type == "skill_start":
        skill = str(event.get("skill") or "")
        if skill:
            state["skill_states"][skill] = "running"
        return

    if event_type == "skill_done":
        skill = str(event.get("skill") or "")
        status = str(event.get("status") or "done")
        if skill:
            state["skill_states"][skill] = status
        data_origin = str(event.get("data_origin") or "").strip()
        if skill and data_origin:
            state["tool_lines"].append(f"{skill} data_origin: {data_origin}")
        for evidence in list(event.get("network_evidence") or [])[:2]:
            if not isinstance(evidence, dict):
                continue
            interface = str(evidence.get("interface") or "akshare")
            err = _preview_text(evidence.get("error"), limit=120)
            status_text = str(evidence.get("status") or "error")
            state["tool_lines"].append(f"{skill} network {interface} {status_text}: {err}")
        if event.get("error"):
            state["tool_lines"].append(f"{skill}: {_preview_text(event.get('error'), limit=160)}")
        return

    if event_type == "route_resolved":
        route = event.get("route") or {}
        state["tool_lines"].append(f"route: {route}")
        return

    if event_type == "formula_tools_loaded":
        tools = event.get("tools") or {}
        state["tool_lines"].append(f"formula tools loaded: {list(dict(tools).keys())}")
        return

    if event_type == EVENT_SKILL_RESULT_READY:
        skill = str(event.get("skill") or "")
        result = event.get("result")
        if skill and isinstance(result, dict):
            status = str(result.get("status") or "error")
            state["skill_states"][skill] = "valid" if status == "valid" else "error"
        return

    if event_type != "skill_event":
        return

    skill = str(event.get("skill") or "")
    nested_raw = event.get("event")
    if not isinstance(nested_raw, dict):
        return
    nested = _flatten_skill_event(nested_raw)
    nested_type = str(nested.get("type") or "")

    if nested_type == EVENT_LLM_REASONING_DELTA:
        state["thinking"] += str(nested.get("delta") or "")
        return

    if nested_type == EVENT_LLM_CONTENT_DELTA and skill == "relationship":
        state["final_output"] += str(nested.get("delta") or "")
        return

    if nested_type == "tool_call":
        tool_name = str(nested.get("tool_name") or "")
        arguments_text = _preview_text(nested.get("arguments_text"), limit=120)
        state["tool_lines"].append(f"{skill} -> tool_call {tool_name} {arguments_text}")
        return

    if nested_type == "tool_result":
        tool_name = str(nested.get("tool_name") or "")
        preview = _preview_text(nested.get("content_preview"), limit=120)
        state["tool_lines"].append(f"{skill} <- tool_result {tool_name} {preview}")
        return

    if nested_type == "tool_grounded_retry":
        reason = _preview_text(nested.get("reason"), limit=120)
        attempt = nested.get("attempt")
        state["tool_lines"].append(f"{skill} retry attempt={attempt} reason={reason}")
        return

    if nested_type == "session_error":
        error_text = _preview_text(nested.get("error"), limit=160)
        state["tool_lines"].append(f"{skill} session_error: {error_text}")


def main() -> None:
    # 这里只管理页面生命周期和 session state，不承载研究逻辑细节。
    st.set_page_config(
        page_title="PomeFi Stock Wiki",
        page_icon="P",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_page_styles()
    render_header()
    render_question_hint()

    if "analysis_payload" not in st.session_state:
        st.session_state.analysis_payload = None
    if "live_events" not in st.session_state:
        st.session_state.live_events = []
    if "live_card_store" not in st.session_state:
        st.session_state.live_card_store = None
    if "use_local_fixture_mode" not in st.session_state:
        st.session_state.use_local_fixture_mode = _default_local_fixture_dir() is not None

    fixture_default_dir = _default_local_fixture_dir()
    configured_fixture_dir = _configured_local_fixture_dir()
    st.session_state.use_local_fixture_mode = st.toggle(
        "使用本地 Fixture 调试",
        value=bool(st.session_state.use_local_fixture_mode),
        help="开启后优先读取 debug_outputs/stock_wiki 或 POMEFI_LOCAL_FIXTURE_DIR，不触发 live skill 执行。",
    )
    active_fixture_dir = _active_local_fixture_dir(use_local_fixture=bool(st.session_state.use_local_fixture_mode))
    if active_fixture_dir is not None:
        fixture_source = "env" if configured_fixture_dir is not None else "default"
        st.caption(f"Fixture mode: {fixture_source} -> {active_fixture_dir}")
    elif st.session_state.use_local_fixture_mode and fixture_default_dir is None:
        st.warning("已开启本地 Fixture 调试，但未找到完整的 debug_outputs/stock_wiki JSON 文件。")

    config_ok, config_error = _validate_app_config(use_local_fixture=bool(st.session_state.use_local_fixture_mode))
    if not config_ok:
        st.error(config_error)
        return

    with st.form("question_form", clear_on_submit=False):
        question = st.text_area(
            "输入你的问题",
            value=st.session_state.get("last_question", ""),
            placeholder="例如：宁德时代怎么看？",
            height=120,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("生成股票百科", use_container_width=True)

    cards_slot = st.empty()
    submitted_rendered = False

    if submitted:
        cleaned_question = question.strip()
        st.session_state.last_question = cleaned_question
        if not cleaned_question:
            st.warning("先输入一个问题。")
        else:
            use_local_fixture = bool(st.session_state.use_local_fixture_mode)
            live_state = _new_live_state()
            live_card_store = _new_live_card_store()
            st.session_state.live_card_store = live_card_store
            slots = create_live_panel_slots()
            update_live_panel(
                slots,
                thinking_text=live_state["thinking"],
                final_output_text=live_state["final_output"],
                tool_lines=live_state["tool_lines"],
                skill_states=live_state["skill_states"],
            )

            def _render_cards() -> None:
                cards_slot.empty()
                with cards_slot.container():
                    render_progressive_cards(
                        live_card_store,
                        metadata=dict(((st.session_state.analysis_payload or {}).get("card") or {}).get("metadata") or {}),
                )

            _render_cards()

            if use_local_fixture:
                try:
                    payload = run_analysis_stream(
                        cleaned_question,
                        on_event=None,
                        use_local_fixture=True,
                    )
                    st.session_state.analysis_payload = payload
                    st.session_state.live_events = []
                    st.session_state.live_card_store = _card_store_from_payload(payload)
                    cards_slot.empty()
                    with cards_slot.container():
                        render_progressive_cards(
                            st.session_state.live_card_store,
                            metadata=dict(((payload.get("card") or {}).get("metadata") or {})),
                        )
                    submitted_rendered = True
                except Exception as exc:
                    config = resolve_kimi_config()
                    st.session_state.analysis_payload = _error_payload(
                        cleaned_question,
                        config.model,
                        "app_runtime_error",
                        f"前台运行失败：{_preview_text(exc)}",
                    )
                    st.session_state.live_card_store = _card_store_from_payload(st.session_state.analysis_payload)
                    submitted_rendered = True
            else:
                def _on_event(event: dict[str, Any]) -> None:
                    _apply_live_event(live_state, event)
                    live_card_store["events"].append(event)
                    event_type = str(event.get("type") or "")
                    if event_type == "route_resolved":
                        live_card_store["route"] = dict(event.get("route") or {})
                    elif event_type == "skill_start":
                        skill = str(event.get("skill") or "")
                        if skill in live_card_store["cards"]:
                            live_card_store["cards"][skill]["state"] = "running"
                    elif event_type == EVENT_SKILL_RESULT_READY:
                        skill = str(event.get("skill") or "")
                        result = event.get("result")
                        if skill in live_card_store["cards"] and isinstance(result, dict):
                            status = str(result.get("status") or "error")
                            live_card_store["cards"][skill] = {
                                "state": "valid" if status == "valid" else "error",
                                "result": dict(result),
                            }
                    elif event_type == EVENT_SESSION_DONE:
                        live_card_store["session_done"] = True
                    update_live_panel(
                        slots,
                        thinking_text=live_state["thinking"],
                        final_output_text=live_state["final_output"],
                        tool_lines=live_state["tool_lines"],
                        skill_states=live_state["skill_states"],
                    )
                    _render_cards()

                try:
                    payload = run_analysis_stream(
                        cleaned_question,
                        on_event=_on_event,
                        use_local_fixture=False,
                    )
                    if not live_state["final_output"]:
                        relationship_summary = str(
                            ((payload.get("card") or {}).get("data") or {}).get("relationship", {}).get("summary") or ""
                        ).strip()
                        live_state["final_output"] = relationship_summary
                        update_live_panel(
                            slots,
                            thinking_text=live_state["thinking"],
                            final_output_text=live_state["final_output"],
                            tool_lines=live_state["tool_lines"],
                            skill_states=live_state["skill_states"],
                        )
                    st.session_state.analysis_payload = payload
                    st.session_state.live_events = live_state["events"]
                    st.session_state.live_card_store = _card_store_from_payload(payload)
                    cards_slot.empty()
                    with cards_slot.container():
                        render_progressive_cards(
                            st.session_state.live_card_store,
                            metadata=dict(((payload.get("card") or {}).get("metadata") or {})),
                        )
                    submitted_rendered = True
                except Exception as exc:
                    config = resolve_kimi_config()
                    st.session_state.analysis_payload = _error_payload(
                        cleaned_question,
                        config.model,
                        "app_runtime_error",
                        f"前台运行失败：{_preview_text(exc)}",
                    )
                    st.session_state.live_card_store = _card_store_from_payload(st.session_state.analysis_payload)
                    submitted_rendered = True

    payload = st.session_state.analysis_payload
    card_store = st.session_state.live_card_store
    if not payload and not card_store:
        st.markdown(
            '<div class="pf-empty">输入一个股票问题后，会并行生成 Summary / Entity / Timeline / Calendar / Relationship 五张卡片。</div>',
            unsafe_allow_html=True,
        )
        return

    export_store = card_store
    if export_store is None and payload:
        export_store = _card_store_from_payload(payload)
    if export_store is not None:
        card_states = [str((item or {}).get("state") or "pending") for item in dict(export_store.get("cards") or {}).values()]
        pending_states = [state for state in card_states if state in {"pending", "running"}]
        render_cards_export_button(
            disabled=bool(pending_states),
            hint="等待卡片完成后再导出" if pending_states else "",
        )

    if payload:
        trace = dict(payload.get("trace") or {})
        trace["stream_events"] = list(st.session_state.get("live_events") or [])
        if submitted_rendered:
            render_status(payload["card"])
            render_debug(
                trace,
                payload["card"],
                local_context=payload.get("local_context") or {},
            )
            return
        render_result_card(
            result=payload["card"],
            trace=trace,
            local_context=payload.get("local_context") or {},
        )
        return

    cards_slot.empty()
    with cards_slot.container():
        render_progressive_cards(card_store, metadata={})


if __name__ == "__main__":
    main()
