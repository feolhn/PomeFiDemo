from __future__ import annotations

import asyncio
from collections.abc import Callable
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
from pomefi.stock_wiki import run_stock_wiki_analysis, run_stock_wiki_analysis_stream
from pomefi.stock_wiki.router import resolve_symbol_from_table
from pomefi.streaming.events import EVENT_LLM_CONTENT_DELTA, EVENT_LLM_REASONING_DELTA, EVENT_SESSION_DONE
from pomefi.ui import (
    create_live_panel_slots,
    inject_page_styles,
    render_header,
    render_question_hint,
    render_result_card,
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


def _validate_app_config() -> tuple[bool, str]:
    config = resolve_kimi_config()
    if not config.api_key:
        return False, "缺少 KIMI_API_KEY。"
    if config.model == "kimi-k2.5" and config.temperature != 1.0:
        return False, "KIMI_MODEL=kimi-k2.5 时，KIMI_TEMPERATURE 必须为 1.0。"
    return True, ""


def _error_payload(question: str, model: str, reason: str, message: str) -> dict[str, Any]:
    skills = {
        "summary": {"skill": "summary", "status": "degraded", "latency_ms": 0, "data": {"summary": message}, "sources": [], "error": reason},
        "entity_info": {"skill": "entity_info", "status": "degraded", "latency_ms": 0, "data": {"summary": message}, "sources": [], "error": reason},
        "timeline": {"skill": "timeline", "status": "degraded", "latency_ms": 0, "data": {"summary": message, "series": [], "events": []}, "sources": [], "error": reason},
        "watch_calendar": {"skill": "watch_calendar", "status": "degraded", "latency_ms": 0, "data": {"summary": message, "items": []}, "sources": [], "error": reason},
        "relationship": {"skill": "relationship", "status": "degraded", "latency_ms": 0, "data": {"summary": message, "pending": False, "nodes": [], "edges": []}, "sources": [], "error": reason},
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
                "critical_failures": ["summary", "timeline", "watch_calendar"],
                "failure_mask": {
                    "summary": reason,
                    "timeline": reason,
                    "watch_calendar": reason,
                },
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
) -> dict[str, Any]:
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

    config_ok, config_error = _validate_app_config()
    if not config_ok:
        st.error(config_error)
        return

    if "analysis_payload" not in st.session_state:
        st.session_state.analysis_payload = None
    if "live_events" not in st.session_state:
        st.session_state.live_events = []

    with st.form("question_form", clear_on_submit=False):
        question = st.text_area(
            "输入你的问题",
            value=st.session_state.get("last_question", ""),
            placeholder="例如：宁德时代怎么看？",
            height=120,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("生成股票百科", use_container_width=True)

    if submitted:
        cleaned_question = question.strip()
        st.session_state.last_question = cleaned_question
        if not cleaned_question:
            st.warning("先输入一个问题。")
        else:
            live_state = _new_live_state()
            slots = create_live_panel_slots()
            update_live_panel(
                slots,
                thinking_text=live_state["thinking"],
                final_output_text=live_state["final_output"],
                tool_lines=live_state["tool_lines"],
                skill_states=live_state["skill_states"],
            )

            def _on_event(event: dict[str, Any]) -> None:
                _apply_live_event(live_state, event)
                update_live_panel(
                    slots,
                    thinking_text=live_state["thinking"],
                    final_output_text=live_state["final_output"],
                    tool_lines=live_state["tool_lines"],
                    skill_states=live_state["skill_states"],
                )

            try:
                payload = run_analysis_stream(cleaned_question, on_event=_on_event)
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
            except Exception as exc:
                config = resolve_kimi_config()
                st.session_state.analysis_payload = _error_payload(
                    cleaned_question,
                    config.model,
                    "app_runtime_error",
                    f"前台运行失败：{_preview_text(exc)}",
                )

    payload = st.session_state.analysis_payload
    if not payload:
        st.markdown(
            '<div class="pf-empty">输入一个股票问题后，会并行生成 Summary / Entity / Timeline / Calendar / Relationship 五张卡片。</div>',
            unsafe_allow_html=True,
        )
        return

    trace = dict(payload.get("trace") or {})
    trace["stream_events"] = list(st.session_state.get("live_events") or [])
    render_result_card(
        result=payload["card"],
        trace=trace,
        local_context=payload.get("local_context") or {},
    )


if __name__ == "__main__":
    main()
