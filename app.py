from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
import sys
from typing import Any

import akshare as ak
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)
if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_TEXT)

from pomefi import BudgetTracker, EventLogger, assemble_garden_card
from pomefi.agent.loop import KimiAgentLoop
from pomefi.config import resolve_kimi_config
from pomefi.protocol import fallback_response
from pomefi.tools import FormulaToolClient, execute_akshare_tool, get_akshare_tool_schema
from pomefi.ui import inject_page_styles, render_header, render_question_hint, render_result_card

FORMULA_URIS = [
    "moonshot/date:latest",
    "moonshot/web-search:latest",
]

APP_SYSTEM_PROMPT = """
你是 PomeFi 的研究引擎。

规则：
1. 当前版本只支持 A 股单标的、宏观/新闻类问题。
2. 任何价格、估值、波动率、财务增速相关判断，必须调用 akshare_tool。
3. 任何“今天 / 最新 / 新闻 / 事件”相关判断，必须优先调用 date，必要时再调用 web_search。
4. 不要臆造数值；工具拿不到就明确承认缺口。
5. 最终回答保持冷静、克制、结构化，用中文输出 2-4 句即可。
""".strip()

MACRO_KEYWORDS = {
    "宏观",
    "新闻",
    "政策",
    "行业",
    "市场",
    "大盘",
    "经济",
    "利率",
    "今天",
    "最新",
    "事件",
    "公告",
    "ai",
}

UNSUPPORTED_KEYWORDS = {
    "美股",
    "港股",
    "基金",
    "etf",
    "期货",
    "比特币",
    "btc",
    "ethereum",
    "黄金",
    "原油",
}


def _preview_text(value: Any, limit: int = 160) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= limit else f"{text[:limit]}..."


def _extract_primary_local_context(trace: dict[str, Any]) -> dict[str, Any]:
    local_context = dict(trace.get("local_context") or {})
    for value in local_context.values():
        if isinstance(value, dict) and "metrics_data" in value:
            return value
    return {}


def _parse_date_value(trace: dict[str, Any]) -> str | None:
    for event in list(trace.get("tool_events") or []):
        if str(event.get("tool_name") or "") != "date":
            continue
        content = str(event.get("tool_content") or event.get("tool_content_preview") or "").strip()
        if not content:
            continue
        try:
            loaded = json.loads(content)
        except json.JSONDecodeError:
            return content
        if isinstance(loaded, dict):
            for key in ("date", "today", "current_date", "formatted_date"):
                if loaded.get(key):
                    return str(loaded[key])
        return content
    return None


def _parse_search_summaries(trace: dict[str, Any]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for event in list(trace.get("tool_events") or []):
        if str(event.get("tool_name") or "") != "web_search":
            continue
        content = str(event.get("tool_content") or "").strip()
        if not content:
            continue
        try:
            loaded = json.loads(content)
        except json.JSONDecodeError:
            continue
        if isinstance(loaded, list):
            summaries.extend([dict(item) for item in loaded if isinstance(item, dict)])
        elif isinstance(loaded, dict):
            items = loaded.get("items") or loaded.get("results") or loaded.get("data")
            if isinstance(items, list):
                summaries.extend([dict(item) for item in items if isinstance(item, dict)])
    return summaries[:5]


def _looks_unsupported(question: str) -> bool:
    lower_question = question.lower()
    return any(keyword in lower_question for keyword in UNSUPPORTED_KEYWORDS)


def _looks_macro(question: str) -> bool:
    lower_question = question.lower()
    return any(keyword in lower_question for keyword in MACRO_KEYWORDS)


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
    code_match = re.search(r"(?<!\d)(\d{6})(?!\d)", question)
    if code_match:
        code = code_match.group(1)
        for row in _load_stock_table():
            if row["code"] == code:
                return code, row["name"]
        return code, None

    exact_matches = [row for row in _load_stock_table() if row["name"] == question.strip()]
    if len(exact_matches) == 1:
        return exact_matches[0]["code"], exact_matches[0]["name"]

    contains_matches = [row for row in _load_stock_table() if row["name"] in question]
    if len(contains_matches) == 1:
        return contains_matches[0]["code"], contains_matches[0]["name"]

    return None, None


def _validate_app_config() -> tuple[bool, str]:
    config = resolve_kimi_config()
    if not config.api_key:
        return False, "缺少 KIMI_API_KEY。"
    if config.stream:
        return False, "当前前台仅支持 KIMI_STREAM=0。"
    if config.model == "kimi-k2.5" and config.temperature != 1.0:
        return False, "KIMI_MODEL=kimi-k2.5 时，KIMI_TEMPERATURE 必须为 1.0。"
    return True, ""


def build_user_prompt(question: str, resolved_symbol: str | None, resolved_name: str | None) -> str:
    if resolved_symbol:
        return (
            f"已解析到 A 股标的：{resolved_symbol}"
            f"{f'（{resolved_name}）' if resolved_name else ''}。"
            f"用户问题：{question}"
        )
    return question


async def _run_analysis(question: str) -> dict[str, Any]:
    config = resolve_kimi_config()
    logger = EventLogger(debug=config.debug)

    if _looks_unsupported(question):
        card = fallback_response(
            question=question,
            model=config.model,
            answer="当前版本只支持 A 股单标的与宏观/新闻类问题。",
            degrade_reason="unsupported_scope",
        )
        return {"card": card, "trace": {"tool_events": [], "events": logger.snapshot(), "local_context": {}}, "local_context": {}}

    resolved_symbol, resolved_name = resolve_symbol(question)
    if not resolved_symbol and not _looks_macro(question):
        card = fallback_response(
            question=question,
            model=config.model,
            answer="当前无法解析 A 股标的，请直接输入 6 位代码或准确公司名。",
            degrade_reason="symbol_unresolved",
        )
        return {"card": card, "trace": {"tool_events": [], "events": logger.snapshot(), "local_context": {}}, "local_context": {}}

    formula_client: FormulaToolClient | None = None
    agent: KimiAgentLoop | None = None
    try:
        formula_client = FormulaToolClient(base_url=config.base_url, api_key=config.api_key)
        await formula_client.load_tools(FORMULA_URIS)
        agent = KimiAgentLoop(config=config, formula_client=formula_client)
        budget_tracker = BudgetTracker()

        trace = await agent.run_conversation_trace(
            user_prompt=build_user_prompt(question, resolved_symbol, resolved_name),
            system_prompt=APP_SYSTEM_PROMPT,
            local_tools=[get_akshare_tool_schema()],
            local_tool_handlers={"akshare_tool": execute_akshare_tool},
            budget_tracker=budget_tracker,
            logger=logger,
        )
        if not str(trace.get("final_content") or "").strip() and not list(trace.get("tool_events") or []):
            trace["degrade_reason"] = trace.get("degrade_reason") or budget_tracker.note_no_progress()
            trace["events"] = logger.snapshot()

        local_context = _extract_primary_local_context(trace)
        card = assemble_garden_card(
            question=question,
            answer=str(trace.get("final_content") or ""),
            model=config.model,
            trace=trace,
            search_summaries=_parse_search_summaries(trace),
            date_value=_parse_date_value(trace),
            usage=trace.get("usage"),
            degrade_reason=trace.get("degrade_reason"),
            logger=logger,
        )
        trace["budget"] = budget_tracker.snapshot()
        trace["events"] = logger.snapshot()
        return {"card": card, "trace": trace, "local_context": local_context}
    finally:
        if agent is not None:
            await agent.aclose()
        if formula_client is not None:
            await formula_client.aclose()


def run_analysis(question: str) -> dict[str, Any]:
    return asyncio.run(_run_analysis(question))


def main() -> None:
    st.set_page_config(
        page_title="PomeFi Finance Garden",
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

    with st.form("question_form", clear_on_submit=False):
        question = st.text_area(
            "输入你的问题",
            value=st.session_state.get("last_question", ""),
            placeholder="例如：300750 现在估值高吗？",
            height=120,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("生成花园卡片", use_container_width=True)

    if submitted:
        cleaned_question = question.strip()
        st.session_state.last_question = cleaned_question
        if not cleaned_question:
            st.warning("先输入一个问题。")
        else:
            with st.spinner("研究中，正在调用工具和整理卡片..."):
                try:
                    st.session_state.analysis_payload = run_analysis(cleaned_question)
                except Exception as exc:
                    config = resolve_kimi_config()
                    st.session_state.analysis_payload = {
                        "card": fallback_response(
                            question=cleaned_question,
                            model=config.model,
                            answer=f"前台运行失败：{_preview_text(exc)}",
                            degrade_reason="assembler_error",
                        ),
                        "trace": {"tool_events": [], "events": [], "local_context": {}},
                        "local_context": {},
                    }

    payload = st.session_state.analysis_payload
    if not payload:
        st.markdown(
            '<div class="pf-empty">输入一个问题后，这里会出现新的金融花园卡片，而不是聊天气泡。</div>',
            unsafe_allow_html=True,
        )
        return

    render_result_card(
        result=payload["card"],
        trace=payload["trace"],
        local_context=payload.get("local_context") or {},
    )


if __name__ == "__main__":
    main()
