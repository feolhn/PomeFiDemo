from __future__ import annotations

from html import escape
import json
from typing import Any

import plotly.graph_objects as go
import streamlit as st

# 这是纯展示层。
# 它消费稳定 contract，不负责研究逻辑。


def inject_page_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&display=swap');

        :root {
          --bg: #f8f9fa;
          --card: #ffffff;
          --ink: #1a1d21;
          --muted: #5f6368;
          --line: #e8eaed;
          --ok: #1e8e3e;
          --warn: #f9ab00;
          --err: #d93025;
          --pill: #e8f0fe;
          --accent: #1a73e8;
          --hover-bg: #f1f3f4;
        }

        .stApp {
          background: var(--bg);
          color: var(--ink);
        }

        .block-container {
          max-width: 430px;
          padding-top: 0.75rem;
          padding-bottom: 2rem;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        h1, h2, h3 {
          font-family: "Public Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
          font-weight: 600 !important;
          letter-spacing: -0.02em;
          color: var(--ink);
        }

        .pf-hero {
          margin-bottom: 0.6rem;
          padding-bottom: 1rem;
          border-bottom: 1px solid var(--line);
        }

        .pf-kicker {
          display: none;
        }

        .pf-subtitle {
          font-size: 0.9rem;
          color: var(--muted);
          line-height: 1.5;
          margin-top: 0.25rem;
          margin-bottom: 0.5rem;
        }

        .pf-status {
          display: inline-flex;
          align-items: center;
          border-radius: 999px;
          border: 1px solid var(--line);
          padding: 0.25rem 0.75rem;
          font-size: 0.75rem;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          background: #fff;
          margin-right: 0.5rem;
          margin-bottom: 0.5rem;
          transition: all 0.2s ease;
        }

        .pf-status-valid { color: var(--ok); border-color: #b7dfb9; background: #e6f4ea; }
        .pf-status-degraded { color: #b06000; border-color: #fde293; background: #fef7e0; }
        .pf-status-error { color: var(--err); border-color: #f6aea9; background: #fce8e6; }

        .pf-section-title {
          display: none;
        }

        .pf-mobile-card {
          border: 1px solid var(--line);
          background: var(--card);
          border-radius: 12px;
          padding: 0.875rem 1rem 0.75rem 1rem;
          margin-bottom: 0.75rem;
          box-shadow: 0 1px 2px rgba(60, 64, 67, 0.06);
          break-inside: avoid;
          page-break-inside: avoid;
        }

        .pf-card-head {
          display: flex;
          justify-content: space-between;
          gap: 0.75rem;
          align-items: flex-start;
          margin-bottom: 0.5rem;
        }

        .pf-card-title {
          font-weight: 600;
          font-size: 0.9375rem;
          line-height: 1.3;
          color: var(--ink);
        }

        .pf-card-badge {
          border-radius: 999px;
          padding: 0.2rem 0.65rem;
          font-size: 0.7rem;
          font-weight: 500;
          border: 1px solid var(--line);
          background: var(--pill);
          color: var(--accent);
          white-space: nowrap;
          flex-shrink: 0;
        }

        .pf-card-badge-error {
          background: #fce8e6;
          color: var(--err);
          border-color: #f6aea9;
        }

        .pf-card-badge-pending {
          background: #fef7e0;
          color: #b06000;
          border-color: #fde293;
        }

        .pf-card-sub {
          font-size: 0.875rem;
          color: var(--muted);
          margin-bottom: 0.6rem;
          line-height: 1.45;
        }

        .pf-big-num {
          font-size: 1.875rem;
          font-weight: 700;
          line-height: 1.15;
          margin-bottom: 0.35rem;
          color: var(--ink);
          letter-spacing: -0.01em;
        }

        .pf-big-num-positive { color: var(--ok); }
        .pf-big-num-negative { color: var(--err); }

        .pf-list {
          margin: 0.4rem 0 0.4rem 0;
          padding-left: 1.25rem;
        }

        .pf-list li {
          margin-bottom: 0.35rem;
          line-height: 1.5;
        }

        .pf-chip-row {
          display: flex;
          flex-wrap: wrap;
          gap: 0.35rem;
          margin-top: 0.4rem;
        }

        .pf-chip {
          border-radius: 999px;
          border: 1px solid #dadce0;
          background: var(--hover-bg);
          color: #3c4043;
          padding: 0.18rem 0.55rem;
          font-size: 0.75rem;
          font-weight: 500;
        }

        .pf-foot {
          border-top: 1px solid var(--line);
          margin-top: 0.75rem;
          padding-top: 0.6rem;
          font-size: 0.75rem;
          color: var(--muted);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .pf-reminder {
          border-radius: 999px;
          border: 1px solid #d4cbe8;
          background: #f1ecfa;
          color: #5d4f87;
          padding: 0.12rem 0.6rem;
          font-size: 0.72rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .pf-reminder:hover {
          background: #e8e0f5;
        }

        .pf-row-actions {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          flex-shrink: 0;
        }

        .pf-link-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 1.9rem;
          height: 1.9rem;
          border-radius: 999px;
          border: 1px solid var(--line);
          background: #fff;
          color: #5f6368;
          text-decoration: none;
          font-size: 0.85rem;
          line-height: 1;
          transition: all 0.15s ease;
        }

        .pf-link-icon:hover {
          background: var(--hover-bg);
          border-color: #dadce0;
        }

        .pf-kv-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 0.4rem 0.5rem;
          margin-bottom: 0.4rem;
          padding: 0.4rem 0;
          border-top: 1px solid var(--line);
          border-bottom: 1px solid var(--line);
        }

        .pf-kv-item {
          display: flex;
          flex-direction: column;
          gap: 0.15rem;
        }

        .pf-kv-label {
          color: var(--muted);
          font-size: 0.65rem;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.02em;
        }

        .pf-kv-value {
          font-size: 0.9rem;
          font-weight: 600;
          color: var(--ink);
        }

        .pf-kv-value-positive { color: var(--ok); }
        .pf-kv-value-negative { color: var(--err); }

        .pf-empty {
          border: 1px dashed var(--line);
          background: #fafbfc;
          border-radius: 14px;
          padding: 1rem 1.1rem;
          color: var(--muted);
          margin-bottom: 0.85rem;
          text-align: center;
        }

        .pf-calendar-item {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 0.75rem;
          padding: 0.6rem 0;
          border-bottom: 1px solid var(--line);
        }

        .pf-calendar-item:last-child {
          border-bottom: none;
        }

        .pf-calendar-date {
          min-width: 5.5rem;
          font-weight: 600;
          color: var(--ink);
          font-size: 0.85rem;
        }

        .pf-calendar-event {
          flex: 1;
          color: #3c4043;
          line-height: 1.4;
          font-size: 0.875rem;
        }

        .pf-timeline-event {
          display: flex;
          gap: 0.75rem;
          padding: 0.5rem 0;
          border-bottom: 1px solid var(--line);
          align-items: flex-start;
        }

        .pf-timeline-event:last-child {
          border-bottom: none;
        }

        .pf-timeline-date {
          min-width: 4.5rem;
          font-weight: 600;
          color: var(--muted);
          font-size: 0.8rem;
          font-family: monospace;
        }

        .pf-timeline-content {
          flex: 1;
          color: #3c4043;
          line-height: 1.4;
          font-size: 0.875rem;
        }

        /* Relationship Graph - Flat Design */
        .pf-rel-graph {
          position: relative;
          padding: 1.5rem 0.5rem;
          min-height: 200px;
        }

        .pf-rel-center {
          position: absolute;
          left: 50%;
          top: 50%;
          transform: translate(-50%, -50%);
          width: 70px;
          height: 70px;
          border-radius: 50%;
          background: #e8e8e8;
          border: 2px solid #d0d0d0;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.75rem;
          font-weight: 600;
          color: #333;
          z-index: 2;
        }

        .pf-rel-node {
          position: absolute;
          padding: 0.4rem 0.7rem;
          border-radius: 16px;
          font-size: 0.75rem;
          font-weight: 500;
          color: #444;
          border: 1px solid rgba(0,0,0,0.08);
          box-shadow: 0 1px 2px rgba(0,0,0,0.04);
          white-space: nowrap;
          z-index: 2;
        }

        .pf-rel-node-supplier {
          background: #f0e6dc;
          color: #5a4a3a;
        }

        .pf-rel-node-customer {
          background: #e0f0e0;
          color: #3a5a3a;
        }

        .pf-rel-node-competitor {
          background: #f0e0e0;
          color: #5a3a3a;
        }

        .pf-rel-node-other {
          background: #e0e8f0;
          color: #3a4a5a;
        }

        .pf-rel-line {
          position: absolute;
          background: #ccc;
          z-index: 1;
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
          .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
          }

          .pf-mobile-card {
            padding: 0.875rem 0.9rem 0.75rem 0.9rem;
            margin-bottom: 0.75rem;
          }

          .pf-big-num {
            font-size: 1.875rem;
          }

          .pf-kv-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.4rem 0.5rem;
          }

          .pf-section-title {
            font-size: 1rem;
            margin-top: 1rem;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <section class="pf-hero">
          <h1 style="margin-bottom: 0.25rem;">📊 Stock Wiki</h1>
          <div class="pf-subtitle">
            智能生成 Summary · Entity · Timeline · Calendar · Relationship 五维分析卡片
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_question_hint() -> None:
    st.caption("💡 试试这样问：`宁德时代怎么看？` · `300750 最近三个月关键事件` · `比亚迪的竞争对手有哪些？`")


def render_cards_export_button(*, disabled: bool = False, hint: str = "") -> None:
    html_renderer = getattr(getattr(getattr(st, "components", None), "v1", None), "html", None)
    if html_renderer is None:
        return
    button_style = (
        "border:1px solid #d9dce1;"
        "background:#ffffff;"
        "color:#1f2328;"
        "border-radius:999px;"
        "padding:0.38rem 0.8rem;"
        "font-size:0.82rem;"
        "cursor:pointer;"
    )
    if disabled:
        button_style += "opacity:0.55;cursor:not-allowed;"
    html = """
        <div style="display:flex;justify-content:flex-end;margin:0.2rem 0 0.55rem 0;">
          <button id="pf-export-cards-btn" style="
            __BUTTON_STYLE__
          " __DISABLED_ATTR__>导出五张卡片 PNG</button>
          <span id="pf-export-cards-status" style="margin-left:0.55rem;font-size:0.78rem;color:#6b7280;"></span>
        </div>
        <script>
        const doc = window.parent.document;
        const button = document.getElementById("pf-export-cards-btn");
        const status = document.getElementById("pf-export-cards-status");
        status.textContent = __HINT_JSON__;

        async function ensureHtml2Canvas() {
          if (window.parent.html2canvas) return window.parent.html2canvas;
          await new Promise((resolve, reject) => {
            const script = doc.createElement("script");
            script.src = "https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js";
            script.onload = resolve;
            script.onerror = reject;
            doc.head.appendChild(script);
          });
          return window.parent.html2canvas;
        }

        async function exportCards() {
          if (button.disabled) return;
          try {
            status.textContent = "导出中...";
            const start = doc.getElementById("pf-export-start");
            const end = doc.getElementById("pf-export-end");
            if (!start || !end) {
              status.textContent = "未找到卡片区域";
              return;
            }
            const startContainer = start.closest('[data-testid="stElementContainer"]');
            const endContainer = end.closest('[data-testid="stElementContainer"]');
            if (!startContainer || !endContainer || !startContainer.parentElement) {
              status.textContent = "卡片区域结构异常";
              return;
            }
            const cloneRoot = doc.createElement("div");
            const blockContainer = doc.querySelector(".block-container");
            cloneRoot.style.position = "fixed";
            cloneRoot.style.left = "-20000px";
            cloneRoot.style.top = "0";
            cloneRoot.style.zIndex = "-1";
            // iPhone optimized width: 390px (iPhone 14/15 standard), 430px (Pro Max)
            cloneRoot.style.width = "390px";
            cloneRoot.style.background = "#f8f9fa";
            cloneRoot.style.padding = "16px 12px";
            cloneRoot.style.display = "flex";
            cloneRoot.style.flexDirection = "column";
            cloneRoot.style.gap = "12px";
            cloneRoot.style.boxSizing = "border-box";
            let cursor = startContainer.nextElementSibling;
            let copied = 0;
            while (cursor && cursor !== endContainer) {
              const style = window.parent.getComputedStyle(cursor);
              const visible = style.display !== "none" && style.visibility !== "hidden" && cursor.getClientRects().length > 0;
              if (visible) {
                cloneRoot.appendChild(cursor.cloneNode(true));
                copied += 1;
              }
              cursor = cursor.nextElementSibling;
            }
            if (!copied) {
              status.textContent = "卡片区域为空";
              return;
            }
            doc.body.appendChild(cloneRoot);
            const html2canvas = await ensureHtml2Canvas();
            const canvas = await html2canvas(cloneRoot, {
              useCORS: true,
              backgroundColor: "#f8f9fa",
              scale: 2,
            });
            cloneRoot.remove();
            const link = doc.createElement("a");
            const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
            link.download = `pomefi-cards-${timestamp}.png`;
            link.href = canvas.toDataURL("image/png");
            link.click();
            status.textContent = "已下载";
            setTimeout(() => { status.textContent = ""; }, 1600);
          } catch (error) {
            status.textContent = "导出失败";
            console.error(error);
          }
        }

        button.addEventListener("click", exportCards);
        </script>
        """
    html = html.replace("__BUTTON_STYLE__", button_style)
    html = html.replace("__DISABLED_ATTR__", "disabled" if disabled else "")
    html = html.replace("__HINT_JSON__", json.dumps(hint or ""))
    html_renderer(
        html,
        height=56,
    )


def create_live_panel_slots() -> dict[str, Any]:
    st.markdown('<h2 class="pf-section-title">Live Execution</h2>', unsafe_allow_html=True)
    left, right = st.columns(2, gap="small")
    with left:
        thinking_slot = st.empty()
        final_slot = st.empty()
    with right:
        skill_slot = st.empty()
        tool_slot = st.empty()
    return {
        "thinking": thinking_slot,
        "final": final_slot,
        "skill": skill_slot,
        "tool": tool_slot,
    }


def update_live_panel(
    slots: dict[str, Any],
    *,
    thinking_text: str,
    final_output_text: str,
    tool_lines: list[str],
    skill_states: dict[str, str],
) -> None:
    skill_rows = "".join(f"<li>{escape(name)}: {escape(state)}</li>" for name, state in skill_states.items())
    tool_rows = "".join(f"<li>{escape(item)}</li>" for item in tool_lines[-8:])

    slots["thinking"].markdown(
        (
            '<section class="pf-mobile-card"><div class="pf-card-sub">THINKING STREAM</div>'
            f'<div>{escape(thinking_text) if thinking_text else "等待 thinking..."}</div></section>'
        ),
        unsafe_allow_html=True,
    )
    slots["final"].markdown(
        (
            '<section class="pf-mobile-card"><div class="pf-card-sub">FINAL OUTPUT STREAM</div>'
            f'<div>{escape(final_output_text) if final_output_text else "等待 final output..."}</div></section>'
        ),
        unsafe_allow_html=True,
    )
    slots["skill"].markdown(
        (
            '<section class="pf-mobile-card"><div class="pf-card-sub">SKILL PROGRESS</div>'
            f"<ul class='pf-list'>{skill_rows}</ul></section>"
        ),
        unsafe_allow_html=True,
    )
    slots["tool"].markdown(
        (
            '<section class="pf-mobile-card"><div class="pf-card-sub">TOOL USE TIMELINE</div>'
            f"<ul class='pf-list'>{tool_rows if tool_rows else '<li>等待 tool call...</li>'}</ul></section>"
        ),
        unsafe_allow_html=True,
    )


def _status_class(status: str) -> str:
    return {
        "valid": "pf-status-valid",
        "degraded": "pf-status-degraded",
        "error": "pf-status-error",
        "success": "pf-status-valid",
        "failed": "pf-status-error",
    }.get(status, "pf-status-degraded")


def render_status(result: dict[str, Any]) -> None:
    metadata = dict(result.get("metadata") or {})
    execution_status = str(metadata.get("execution_status") or "").strip().lower()
    page_status = str(metadata.get("page_status") or "").strip().lower()
    status = str(result.get("quality_status") or "error")
    if execution_status == "success":
        status = "valid"
    elif execution_status == "failed":
        status = "error"
    elif page_status == "partial":
        status = "degraded"
    degrade_reason = str(metadata.get("failure_reason_code") or metadata.get("degrade_reason") or "").strip()
    text = execution_status if execution_status else (page_status or status)
    if degrade_reason:
        text = f"{text} · {degrade_reason}"
    st.markdown(
        f'<div class="pf-status {_status_class(status)}">{text}</div>',
        unsafe_allow_html=True,
    )
    if execution_status == "failed":
        failure_stage = str(metadata.get("failure_stage") or "").strip()
        failure_message = str(metadata.get("failure_reason_message") or "").strip()
        caption_parts = []
        if failure_stage:
            caption_parts.append(f"stage={failure_stage}")
        if failure_message:
            caption_parts.append(failure_message)
        if caption_parts:
            st.caption(" | ".join(caption_parts))
    if execution_status != "failed" and bool(metadata.get("relationship_pending")):
        st.markdown('<div class="pf-status pf-status-degraded">relationship · pending</div>', unsafe_allow_html=True)
        st.caption("Relationship 正在深度分析中，已先展示其他卡片。")


SKILL_ORDER = ("summary", "entity_info", "timeline", "watch_calendar", "relationship")


def _card_state_entry(card_store: dict[str, Any], skill: str) -> dict[str, Any]:
    cards = dict(card_store.get("cards") or {})
    entry = dict(cards.get(skill) or {})
    state = str(entry.get("state") or "pending")
    result = entry.get("result")
    if not isinstance(result, dict):
        result = None
    return {"state": state, "result": result}


def _render_state_shell(*, title: str, badge: str, summary: str, bullets: list[str] | None = None, footer: str = "Source: - · Updated: -") -> None:
    bullet_html = "".join(f"<li>{escape(item)}</li>" for item in list(bullets or []))
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-head">
            <div class="pf-card-title">{escape(title)}</div>
            <div class="pf-card-badge">{escape(badge)}</div>
          </div>
          <div>{escape(summary)}</div>
          <ul class="pf-list">{bullet_html}</ul>
          <div class="pf-foot">{escape(footer)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_skill_error(title: str, entry: dict[str, Any], footer: str) -> None:
    result = dict(entry.get("result") or {})
    data = dict(result.get("data") or {})
    error = str(result.get("error") or "card_failed")
    summary = str(data.get("summary") or "当前卡片执行失败。")
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-head">
            <div class="pf-card-title">{escape(title)}</div>
            <div class="pf-card-badge pf-card-badge-error">Error</div>
          </div>
          <div style="color:#3c4043;">{escape(summary)}</div>
          <div style="margin-top:0.5rem;padding:0.5rem;background:#fce8e6;border-radius:8px;font-size:0.8rem;color:var(--err);">
            ⚠️ {escape(error)}
          </div>
          <div class="pf-foot">{escape(footer)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_skill_pending(title: str, badge: str, footer: str, state: str) -> None:
    summary = "卡片正在生成中..." if state == "running" else "等待卡片启动..."
    loading_dots = "<span class='loading-dots'>...</span>" if state == "running" else ""
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-head">
            <div class="pf-card-title">{escape(title)}</div>
            <div class="pf-card-badge pf-card-badge-pending">{escape(badge)}</div>
          </div>
          <div style="display:flex;align-items:center;gap:0.5rem;color:var(--muted);">
            <div class="pf-spinner" style="width:16px;height:16px;border:2px solid #e8eaed;border-top-color:var(--accent);border-radius:50%;animation:spin 1s linear infinite;"></div>
            <span>{escape(summary)}{loading_dots}</span>
          </div>
          <style>
            @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
          </style>
          <div class="pf-foot">{escape(footer)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_summary_card(entry: dict[str, Any]) -> None:
    state = str(entry.get("state") or "pending")
    if state in {"pending", "running"}:
        _render_skill_pending("Stock Summary", "Active", "Source: AkShare · Updated: -", state)
        return

    result = dict(entry.get("result") or {})
    data = dict(result.get("data") or {})
    metrics = dict(data.get("metrics") or {})
    if state != "valid" and not metrics:
        _render_skill_error("Stock Summary", entry, "Source: AkShare · Updated: -")
        return
    price_last = metrics.get("price_last")
    ret_1d = metrics.get("ret_1d")
    
    # Build key-value rows with proper labels
    kv_rows = []
    metric_labels = {
        "mkt_cap": "市值",
        "pe_ttm": "市盈率",
        "pb": "市净率", 
        "ret_1d": "1日涨跌",
        "ret_5d": "5日涨跌",
        "ret_20d": "20日涨跌",
        "vol_20d": "20日波动",
        "max_drawdown_1y": "1年回撤"
    }
    
    for key in ("mkt_cap", "pe_ttm", "pb", "ret_1d", "ret_5d", "ret_20d"):
        if key in metrics and metrics.get(key) is not None:
            value = _format_metric_value(metrics.get(key), key)
            # Add color class for return metrics
            value_class = ""
            if key in ("ret_1d", "ret_5d", "ret_20d") and metrics.get(key) is not None:
                try:
                    val = float(metrics.get(key))
                    value_class = " pf-kv-value-positive" if val > 0 else " pf-kv-value-negative" if val < 0 else ""
                except (TypeError, ValueError):
                    pass
            kv_rows.append((metric_labels.get(key, key), value, value_class))
    
    if not kv_rows:
        kv_rows = [(metric_labels.get(key, key), _format_metric_value(val, key), "") 
                   for key, val in list(metrics.items())[:6] if val is not None]
    
    kv_html = "".join(
        f"<div class='pf-kv-item'><div class='pf-kv-label'>{escape(label)}</div>"
        f"<div class='pf-kv-value{value_class}'>{escape(value)}</div></div>"
        for label, value, value_class in kv_rows[:6]
    )
    
    # Price display with change indicator
    price_text = "--" if price_last is None else f"¥{float(price_last):.2f}"
    price_change_html = ""
    if ret_1d is not None:
        try:
            change_pct = float(ret_1d) * 100
            change_class = "pf-big-num-positive" if change_pct > 0 else "pf-big-num-negative" if change_pct < 0 else ""
            change_sign = "+" if change_pct > 0 else ""
            price_change_html = f"<div style='font-size:0.875rem;margin-top:0.25rem;' class='{change_class}'>{change_sign}{change_pct:.2f}% 今日</div>"
        except (TypeError, ValueError):
            pass
    
    badge = "Active" if state == "valid" else "Partial"
    badge_class = "" if state == "valid" else " pf-card-badge-pending"
    
    summary_text = str(data.get("summary") or "已输出核心行情与估值指标。")
    if state != "valid" and metrics:
        summary_text = "实时价格链路失败，先展示当前已拿到的估值指标。"
    
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-head">
            <div class="pf-card-title">📊 行情概览</div>
            <div class="pf-card-badge{badge_class}">{escape(badge)}</div>
          </div>
          <div class="pf-big-num">{escape(price_text)}</div>
          {price_change_html}
          <div class="pf-kv-grid">{kv_html}</div>
          <div style="font-size:0.875rem;color:var(--muted);">{escape(summary_text)}</div>
          <div class="pf-foot">{escape(_source_footer(result, "AkShare"))}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_entity_info_card(entry: dict[str, Any], company: str, symbol: str) -> None:
    state = str(entry.get("state") or "pending")
    if state in {"pending", "running"}:
        _render_skill_pending(f"公司主体", "分析中", "Source: kimi · Updated: -", state)
        return
    if state != "valid":
        _render_skill_error(f"公司主体", entry, "Source: kimi · Updated: -")
        return

    result = dict(entry.get("result") or {})
    data = dict(result.get("data") or {})
    
    # Extract company info
    industry = data.get('industry', '')
    main_business = data.get('main_business', '')
    investment_tags = data.get('investment_tags', [])
    
    # Build info chips from various sources
    chips = []
    if industry:
        chips.append(industry)
    if main_business:
        # Split main business by delimiter and add as chips
        for item in str(main_business).split('、'):
            if item.strip():
                chips.append(item.strip())
    # Also add investment tags if available
    if investment_tags:
        for tag in investment_tags:
            if tag and tag not in chips:
                chips.append(str(tag))
    
    chip_html = "".join(f"<span class='pf-chip'>{escape(item)}</span>" for item in chips[:8])
    
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-head">
            <div class="pf-card-title">🏢 公司主体</div>
            <div class="pf-card-badge">{escape(industry or "Tech & Auto")}</div>
          </div>
          <div style="line-height:1.6;color:#3c4043;">{escape(str(data.get("summary") or "暂无公司主体介绍。"))}</div>
          {f"<div class='pf-chip-row'>{chip_html}</div>" if chip_html else ""}
          <div class="pf-foot">{escape(_source_footer(result, "kimi"))}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_timeline_card(entry: dict[str, Any]) -> None:
    state = str(entry.get("state") or "pending")
    if state in {"pending", "running"}:
        _render_skill_pending("事件时间线", "分析中", "Source: MarketWatch · Updated: -", state)
        return
    if state != "valid":
        _render_skill_error("事件时间线", entry, "Source: MarketWatch · Updated: -")
        return

    result = dict(entry.get("result") or {})
    data = dict(result.get("data") or {})
    events = [dict(item) for item in list(data.get("events") or []) if isinstance(item, dict)]
    series = [dict(item) for item in list(data.get("series") or []) if isinstance(item, dict)]
    event_html = _timeline_event_html(events)
    summary_text = _compact_text(str(data.get("summary") or "近三个月价格与事件时间线。"), limit=120)
    
    # Build SVG chart
    chart_html = ""
    if series:
        chart_html = _build_timeline_svg(series, events)
    
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-head">
            <div class="pf-card-title">📈 价格走势 & 关键事件</div>
            <div class="pf-card-badge">近3个月</div>
          </div>
          <div class="pf-card-sub">{escape(summary_text)}</div>
          {chart_html}
          <div style="font-weight:600;font-size:0.875rem;margin:0.75rem 0 0.5rem;color:var(--ink);">关键事件</div>
          <div>{event_html}</div>
          <div class="pf-foot">{escape(_source_footer(result, "MarketWatch"))}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _smooth_path_data(ys: list[float], x_scale, y_scale) -> str:
    """Generate smooth SVG path using cubic bezier curves."""
    n = len(ys)
    if n == 0:
        return ""
    if n == 1:
        return f"M{x_scale(0):.1f},{y_scale(ys[0]):.1f}"
    if n == 2:
        return f"M{x_scale(0):.1f},{y_scale(ys[0]):.1f} L{x_scale(1):.1f},{y_scale(ys[1]):.1f}"
    
    points = [(x_scale(i), y_scale(y)) for i, y in enumerate(ys)]
    
    # Build smooth curve using cubic bezier
    def control_points(p0, p1, p2, t=0.2):
        """Calculate control points for smooth curve."""
        d01 = ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5
        d12 = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5
        
        fa = t * d01 / (d01 + d12)
        fb = t * d12 / (d01 + d12)
        
        p1x = p1[0] - fa * (p2[0] - p0[0])
        p1y = p1[1] - fa * (p2[1] - p0[1])
        p2x = p1[0] + fb * (p2[0] - p0[0])
        p2y = p1[1] + fb * (p2[1] - p0[1])
        
        return (p1x, p1y), (p2x, p2y)
    
    path = f"M{points[0][0]:.1f},{points[0][1]:.1f}"
    
    # First segment
    cp1 = (points[0][0] + (points[1][0] - points[0][0]) * 0.3, points[0][1])
    cp2 = (points[1][0] - (points[2][0] - points[0][0]) * 0.1, points[1][1] - (points[2][1] - points[0][1]) * 0.1)
    path += f" C{cp1[0]:.1f},{cp1[1]:.1f} {cp2[0]:.1f},{cp2[1]:.1f} {points[1][0]:.1f},{points[1][1]:.1f}"
    
    # Middle segments
    for i in range(1, n - 2):
        cp1, cp2 = control_points(points[i], points[i+1], points[i+2])
        path += f" C{cp1[0]:.1f},{cp1[1]:.1f} {cp2[0]:.1f},{cp2[1]:.1f} {points[i+1][0]:.1f},{points[i+1][1]:.1f}"
    
    # Last segment
    if n > 2:
        cp1 = (points[-2][0] + (points[-1][0] - points[-3][0]) * 0.1, points[-2][1] + (points[-1][1] - points[-3][1]) * 0.1)
        cp2 = (points[-1][0] - (points[-1][0] - points[-2][0]) * 0.3, points[-1][1])
        path += f" C{cp1[0]:.1f},{cp1[1]:.1f} {cp2[0]:.1f},{cp2[1]:.1f} {points[-1][0]:.1f},{points[-1][1]:.1f}"
    
    return path


def _build_timeline_svg(series: list[dict[str, Any]], events: list[dict[str, Any]]) -> str:
    """Build simple SVG line chart."""
    if not series:
        return ""
    
    # Extract data
    xs = [row.get("date") for row in series]
    ys = [float(row.get("close", 0)) for row in series]
    
    if not xs or not ys:
        return ""
    
    # Dimensions
    width = 360
    height = 180
    padding = {"top": 40, "right": 20, "bottom": 30, "left": 50}
    chart_w = width - padding["left"] - padding["right"]
    chart_h = height - padding["top"] - padding["bottom"]
    
    # Scales
    y_min = min(ys)
    y_max = max(ys)
    y_range = y_max - y_min if y_max != y_min else 1
    
    def x_scale(i: int) -> float:
        return padding["left"] + (i / max(len(xs) - 1, 1)) * chart_w
    
    def y_scale(y: float) -> float:
        return padding["top"] + chart_h - ((y - y_min) / y_range) * chart_h
    
    # Build smooth curved path using Catmull-Rom spline
    path_d = _smooth_path_data(ys, x_scale, y_scale)
    
    # Y-axis labels (3 ticks)
    y_ticks = []
    for i in range(3):
        y_val = y_min + (y_range * i / 2)
        y_pos = y_scale(y_val)
        y_ticks.append(f'<text x="{padding["left"]-10}" y="{y_pos+4}" text-anchor="end" font-size="10" fill="#888">¥{y_val:.0f}</text>')
        y_ticks.append(f'<line x1="{padding["left"]}" y1="{y_pos}" x2="{width-padding["right"]}" y2="{y_pos}" stroke="#eee" stroke-width="1"/>')
    
    # X-axis labels (show first, middle, last)
    x_ticks = []
    x_indices = [0, len(xs)//2, len(xs)-1]
    for i in x_indices:
        if i < len(xs):
            date_str = str(xs[i])[5:] if len(str(xs[i])) > 5 else str(xs[i])  # MM-DD
            x_pos = x_scale(i)
            x_ticks.append(f'<text x="{x_pos}" y="{height-10}" text-anchor="middle" font-size="10" fill="#888">{date_str}</text>')
    
    # Event markers
    event_markers = []
    event_labels = []
    for idx, item in enumerate(events[:3]):
        if not isinstance(item, dict):
            continue
        date_text = str(item.get("date") or "")
        title = str(item.get("title") or "").strip()
        if not date_text or not title:
            continue
        try:
            point_idx = xs.index(date_text)
        except ValueError:
            continue
        
        x_pos = x_scale(point_idx)
        y_pos = y_scale(ys[point_idx])
        
        # Alternate label position (top/bottom)
        label_y = y_pos - 25 if idx % 2 == 0 else y_pos + 35
        
        event_markers.append(f'<circle cx="{x_pos}" cy="{y_pos}" r="4" fill="#c85a54" stroke="#fff" stroke-width="2"/>')
        event_labels.append(f'<text x="{x_pos}" y="{label_y}" text-anchor="middle" font-size="9" fill="#666">{escape(title[:12])}</text>')
    
    svg_content = f"""
    <svg width="100%" height="{height}" viewBox="0 0 {width} {height}" style="margin:0.5rem 0;">
      {''.join(y_ticks)}
      {''.join(x_ticks)}
      <path d="{path_d}" fill="none" stroke="#333" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      {''.join(event_markers)}
      {''.join(event_labels)}
    </svg>
    """
    
    return svg_content


def _watch_calendar_actions_html(url: Any) -> str:
    url_text = str(url or "").strip()
    link_html = ""
    if url_text:
        safe_url = escape(url_text, quote=True)
        link_html = (
            f"<a class='pf-link-icon' href='{safe_url}' target='_blank' rel='noopener noreferrer' "
            "title='Open source link'>🔗</a>"
        )
    return f"<div class='pf-row-actions'>{link_html}<div class='pf-reminder'>Set Reminder</div></div>"


def render_watch_calendar_card(entry: dict[str, Any]) -> None:
    state = str(entry.get("state") or "pending")
    if state in {"pending", "running"}:
        _render_skill_pending("关注日历", " upcoming", "Source: IR · Updated: -", state)
        return
    if state != "valid":
        _render_skill_error("关注日历", entry, "Source: IR · Updated: -")
        return

    result = dict(entry.get("result") or {})
    data = dict(result.get("data") or {})
    rows = [dict(item) for item in list(data.get("items") or []) if isinstance(item, dict)][:4]
    
    # Build calendar items with improved styling
    row_html = ""
    for item in rows:
        date_text = escape(str(item.get('date') or '-'))
        event_text = escape(str(item.get('event') or ''))
        certainty = str(item.get('certainty', ''))
        certainty_badge = ""
        if certainty == "high":
            certainty_badge = "<span style='font-size:0.65rem;padding:0.1rem 0.4rem;background:#e6f4ea;color:#1e8e3e;border-radius:999px;margin-left:0.5rem;'>高确定性</span>"
        elif certainty == "medium":
            certainty_badge = "<span style='font-size:0.65rem;padding:0.1rem 0.4rem;background:#fef7e0;color:#b06000;border-radius:999px;margin-left:0.5rem;'>中确定性</span>"
        
        row_html += (
            f"<div class='pf-calendar-item'>"
            f"<div style='display:flex;align-items:center;'><span class='pf-calendar-date'>{date_text}</span>{certainty_badge}</div>"
            f"<div class='pf-calendar-event'>{event_text}</div>"
            f"{_watch_calendar_actions_html(item.get('url'))}</div>"
        )
    
    if not row_html:
        row_html = "<div class='pf-calendar-item'><div class='pf-calendar-event' style='color:var(--muted);'>• 当前没有可展示的日历节点。</div></div>"
    
    summary_text = escape(str(data.get("summary") or "近期关键事件日历。"))
    
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-head">
            <div class="pf-card-title">📅 关注日历</div>
            <div class="pf-card-badge">Upcoming</div>
          </div>
          <div style="font-size:0.875rem;color:var(--muted);margin-bottom:0.75rem;">{summary_text}</div>
          <div>{row_html}</div>
          <div class="pf-foot">{escape(_source_footer(result, "IR"))}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_relationship_card(entry: dict[str, Any]) -> None:
    state = str(entry.get("state") or "pending")
    if state in {"pending", "running"}:
        _render_skill_pending("关系图谱", "分析中", "Source: Crunchbase · Updated: -", state)
        return
    if state != "valid":
        _render_skill_error("关系图谱", entry, "Source: Crunchbase · Updated: -")
        return

    result = dict(entry.get("result") or {})
    data = dict(result.get("data") or {})
    nodes = [dict(item) for item in list(data.get("nodes") or []) if isinstance(item, dict)]
    edges = [dict(item) for item in list(data.get("edges") or []) if isinstance(item, dict)]
    summary_text = _compact_text(str(data.get("summary") or "关系图谱结果暂缺。"), limit=96)
    
    # Build HTML relationship graph
    graph_html = ""
    if nodes:
        graph_html = _build_relationship_graph_html(nodes, edges)
    
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-head">
            <div class="pf-card-title">🔗 关系图谱</div>
            <div class="pf-card-badge">{len(nodes)} 节点 · {len(edges)} 关系</div>
          </div>
          <div class="pf-card-sub">{escape(summary_text)}</div>
          {graph_html}
          <div class="pf-foot">{escape(_source_footer(result, "Crunchbase"))}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _build_relationship_graph_html(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
    """Build flat-design relationship graph using HTML/CSS."""
    # Group nodes by role
    grouped: dict[str, list[str]] = {"theme": [], "supplier": [], "customer": [], "competitor": [], "other": []}
    for node in nodes:
        role = str(node.get("role", "other"))
        node_id = str(node.get("id", ""))
        if node_id:
            grouped.setdefault(role, []).append(node_id)
    
    # Get theme node (center)
    theme_node = grouped["theme"][0] if grouped["theme"] else "中心"
    
    # Build node positions
    # Left side: suppliers, Right side: customers
    # Top: others, Bottom: competitors
    nodes_html = f'<div class="pf-rel-center">{escape(theme_node)}</div>'
    
    # Left side - suppliers (positioned with inline styles)
    left_nodes = grouped.get("supplier", [])[:3]
    for idx, node_id in enumerate(left_nodes):
        top_pct = 20 + idx * 25
        nodes_html += f'<div class="pf-rel-node pf-rel-node-supplier" style="left:5%;top:{top_pct}%;">{escape(node_id)}</div>'
    
    # Right side - customers
    right_nodes = grouped.get("customer", [])[:3]
    for idx, node_id in enumerate(right_nodes):
        top_pct = 20 + idx * 25
        nodes_html += f'<div class="pf-rel-node pf-rel-node-customer" style="right:5%;top:{top_pct}%;">{escape(node_id)}</div>'
    
    # Top - others
    top_nodes = grouped.get("other", [])[:2]
    for idx, node_id in enumerate(top_nodes):
        left_pct = 35 + idx * 30
        nodes_html += f'<div class="pf-rel-node pf-rel-node-other" style="left:{left_pct}%;top:5%;">{escape(node_id)}</div>'
    
    # Bottom - competitors
    bottom_nodes = grouped.get("competitor", [])[:2]
    for idx, node_id in enumerate(bottom_nodes):
        left_pct = 35 + idx * 30
        nodes_html += f'<div class="pf-rel-node pf-rel-node-competitor" style="left:{left_pct}%;bottom:5%;">{escape(node_id)}</div>'
    
    return f'<div class="pf-rel-graph">{nodes_html}</div>'


def _build_card_store_from_result(result: dict[str, Any]) -> dict[str, Any]:
    data = dict(result.get("data") or {})
    skills = dict(data.get("skills") or {})
    metadata = dict(result.get("metadata") or {})
    cards: dict[str, dict[str, Any]] = {}
    for skill in SKILL_ORDER:
        skill_result = skills.get(skill)
        if not isinstance(skill_result, dict):
            section = data.get(skill)
            if isinstance(section, dict):
                skill_result = {
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
        if not isinstance(skill_result, dict):
            cards[skill] = {"state": "pending", "result": None}
            continue
        status = str(skill_result.get("status") or "pending")
        cards[skill] = {
            "state": "valid" if status == "valid" else "error",
            "result": dict(skill_result),
        }
    return {
        "route": {
            "symbol": metadata.get("symbol"),
            "company_name": metadata.get("company_name"),
            "question": data.get("question"),
        },
        "cards": cards,
        "session_done": True,
    }


def render_progressive_cards(
    card_store: dict[str, Any],
    *,
    metadata: dict[str, Any] | None = None,
    trace: dict[str, Any] | None = None,
    local_context: dict[str, Any] | None = None,
) -> None:
    _ = trace, local_context
    meta = dict(metadata or {})
    route = dict(card_store.get("route") or {})
    st.markdown('<div id="pf-export-start" style="height:1px;"></div>', unsafe_allow_html=True)
    company = str(
        route.get("company_name")
        or meta.get("company_name")
        or ((_card_state_entry(card_store, "entity_info").get("result") or {}).get("data") or {}).get("company_name")
        or ((_card_state_entry(card_store, "summary").get("result") or {}).get("data") or {}).get("company_name")
        or "标的"
    )
    symbol = str(route.get("symbol") or meta.get("symbol") or "")

    # Header section with company name
    if company and company != "标的":
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.25rem;">
                <h2 style="margin:0;font-size:1.25rem;font-weight:600;letter-spacing:-0.01em;">{escape(company)}</h2>
                {f'<span style="color:var(--muted);font-size:0.875rem;font-weight:500;">{escape(symbol)}</span>' if symbol else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Single column layout for all cards (iPhone optimized)
    render_summary_card(_card_state_entry(card_store, "summary"))
    render_entity_info_card(_card_state_entry(card_store, "entity_info"), company, symbol)
    render_timeline_card(_card_state_entry(card_store, "timeline"))
    render_watch_calendar_card(_card_state_entry(card_store, "watch_calendar"))
    render_relationship_card(_card_state_entry(card_store, "relationship"))

    # Footer metadata (compact for mobile)
    if meta:
        st.markdown(
            f"""
            <div style="margin-top:1rem;padding-top:0.75rem;border-top:1px solid var(--line);font-size:0.7rem;color:var(--muted);text-align:center;">
                {escape(meta.get('generated_at', '-'))} · {escape(meta.get('symbol', '-'))}
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('<div id="pf-export-end" style="height:1px;"></div>', unsafe_allow_html=True)


def _render_failed_stock_wiki_result(result: dict[str, Any]) -> None:
    metadata = dict(result.get("metadata") or {})
    failure_code = str(metadata.get("failure_reason_code") or "UNKNOWN_UNRECOVERED")
    failure_message = str(metadata.get("failure_reason_message") or "本次执行失败。")
    failure_stage = str(metadata.get("failure_stage") or "-")
    short_circuit = bool(metadata.get("short_circuit"))
    cancelled_skills = [str(item) for item in list(metadata.get("cancelled_skills") or []) if str(item)]
    evidence = metadata.get("failure_evidence")
    evidence_text = json.dumps(evidence, ensure_ascii=False) if isinstance(evidence, (dict, list)) else str(evidence or "-")
    cancelled_text = ", ".join(cancelled_skills) if cancelled_skills else "-"
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-head">
            <div class="pf-card-title">Execution Failed</div>
            <div class="pf-card-badge">FAILED</div>
          </div>
          <div><strong>失败码：</strong>{escape(failure_code)}</div>
          <div><strong>失败阶段：</strong>{escape(failure_stage)}</div>
          <div><strong>short_circuit：</strong>{'true' if short_circuit else 'false'}</div>
          <div><strong>cancelled_skills：</strong>{escape(cancelled_text)}</div>
          <div style="margin-top:0.35rem;">{escape(failure_message)}</div>
          <div class="pf-foot">evidence: {escape(evidence_text)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_answer(result: dict[str, Any]) -> None:
    answer = str((result.get("data") or {}).get("answer") or "").strip()
    if not answer:
        answer = "当前没有可展示的回答文本。"
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-sub">PRIMARY READ</div>
          <div>{escape(answer)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _is_stock_wiki_result(result: dict[str, Any]) -> bool:
    data = dict(result.get("data") or {})
    required = {"summary", "entity_info", "timeline", "watch_calendar", "relationship"}
    return required.issubset(set(data.keys()))


def _card_badge(skill_result: dict[str, Any], default_label: str) -> str:
    status = str(skill_result.get("status") or "").lower()
    if status == "valid":
        return "Active"
    if status == "degraded":
        return "Degraded"
    if status == "error":
        return "Error"
    return default_label


def _source_footer(skill_result: dict[str, Any], fallback: str) -> str:
    sources = [dict(item) for item in list(skill_result.get("sources") or []) if isinstance(item, dict)]
    if not sources:
        return f"Source: {fallback} · Updated: -"
    source = sources[0]
    source_name = str(source.get("source") or fallback)
    updated = str(source.get("published_at") or "-")
    return f"Source: {source_name} · Updated: {updated}"


def _format_metric_value(value: Any, metric_name: str | None = None) -> str:
    """Format metric value for display. Backward compatible with optional metric_name."""
    if value is None:
        return "不可用"
    
    # Handle percentage metrics
    percent_keys = {"ret_1d", "ret_5d", "ret_20d", "vol_20d", "max_drawdown_1y"}
    if metric_name in percent_keys:
        try:
            numeric = float(value) * 100
            if metric_name in {"ret_1d", "ret_5d", "ret_20d"} and numeric > 0:
                return f"+{numeric:.2f}%"
            return f"{numeric:.2f}%"
        except (TypeError, ValueError):
            return str(value)
    
    # Handle PE/PB metrics
    if metric_name in {"pe_ttm", "pb"}:
        try:
            numeric = float(value)
            if metric_name == "pe_ttm" and numeric < 0:
                return "亏损"
            return f"{numeric:.2f}"
        except (TypeError, ValueError):
            return str(value)
    
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _summary_price_text(price_last: Any) -> str:
    """Format price text with yuan symbol."""
    if price_last is None:
        return "--"
    try:
        return f"{float(price_last):.2f}元"
    except (TypeError, ValueError):
        return str(price_last)


def _summary_sections(
    metrics: dict[str, Any],
    *,
    missing: list[str],
    error_reason: str = "",
) -> tuple[list[tuple[str, str]], list[str]]:
    """Generate key-value rows and bullet points for summary."""
    primary_keys = ("mkt_cap", "pe_ttm", "pb", "ret_1d", "ret_5d", "ret_20d")
    extra_keys = ("vol_20d", "max_drawdown_1y")
    
    metric_labels = {
        "mkt_cap": "市值",
        "pe_ttm": "市盈率",
        "pb": "市净率",
        "ret_1d": "近1日",
        "ret_5d": "近5日",
        "ret_20d": "近20日",
        "vol_20d": "20日波动",
        "max_drawdown_1y": "1年回撤",
    }
    
    kv_rows = [
        (metric_labels.get(key, key), _format_metric_value(metrics.get(key), key))
        for key in primary_keys
        if metrics.get(key) is not None
    ]
    
    if not kv_rows:
        kv_rows = [
            (metric_labels.get(key, key), _format_metric_value(value, key))
            for key, value in list(metrics.items())[:6]
            if value is not None
        ]
    
    shown_keys = {key for key in primary_keys if metrics.get(key) is not None}
    kv_rows.extend(
        [
            (metric_labels.get(key, key), _format_metric_value(metrics.get(key), key))
            for key in extra_keys
            if key in metrics and metrics.get(key) is not None and key not in shown_keys
        ]
    )
    
    bullets: list[str] = []
    if missing:
        bullets.extend(
            [f"{metric_labels.get(item, item)}: 不可用（{error_reason or '数据暂不可达'}）" for item in missing[:3]]
        )
    return kv_rows[:8], bullets[:6]


def _masked_or_default(
    *,
    skill: str,
    failure_mask: dict[str, Any],
    default_summary: str,
    default_bullets: list[str],
) -> tuple[str, list[str]]:
    reason = failure_mask.get(skill)
    if not reason:
        return default_summary, default_bullets
    return (
        "数据暂不可达，已启用失败遮罩。",
        [f"原因: {str(reason)}"],
    )


def _timeline_figure(series: list[dict[str, Any]], events: list[dict[str, Any]]) -> go.Figure:
    figure = go.Figure()
    xs = [row.get("date") for row in series]
    ys = [row.get("close") for row in series]
    figure.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            line={"width": 2.2, "color": "#4b5563"},
            name="Close",
        )
    )
    marker_xs: list[Any] = []
    marker_ys: list[Any] = []
    marker_texts: list[str] = []
    annotations: list[dict[str, Any]] = []
    
    for item in events[:4]:
        if not isinstance(item, dict):
            continue
        date_text = str(item.get("date") or "")
        title = str(item.get("title") or "").strip()
        if not date_text or not title:
            continue
        try:
            point_idx = xs.index(date_text)
        except ValueError:
            continue
        marker_xs.append(xs[point_idx])
        marker_ys.append(ys[point_idx])
        marker_texts.append(title)
        
        # Add annotation for event (capped at 2 for mobile density, positioned to avoid clipping)
        if len(annotations) < 2:
            # Alternate between top and bottom to avoid overlap
            ay_offset = -25 if len(annotations) % 2 == 0 else 25
            annotations.append({
                "x": xs[point_idx],
                "y": ys[point_idx],
                "text": _timeline_event_label(title, limit=10),
                "showarrow": True,
                "arrowhead": 2,
                "arrowsize": 1,
                "arrowwidth": 1,
                "ax": 0,
                "ay": ay_offset,
                "font": {"size": 10, "color": "#3c4043"},
                "bgcolor": "rgba(255,255,255,0.95)",
                "bordercolor": "#dadce0",
                "borderwidth": 1,
                "borderpad": 4,
                "align": "center",
            })
    
    if marker_xs:
        figure.add_trace(
            go.Scatter(
                x=marker_xs,
                y=marker_ys,
                mode="markers",
                marker={"size": 8, "color": "#ffffff", "line": {"width": 2, "color": "#bf8f8f"}},
                hovertext=marker_texts,
                hovertemplate="%{hovertext}<extra></extra>",
                name="Events",
            )
        )
    figure.update_layout(
        margin={"l": 4, "r": 4, "t": 32, "b": 4},
        height=200,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        xaxis={"showgrid": False, "zeroline": False, "showline": False, "tickfont": {"size": 9, "color": "#6b7280"}},
        yaxis={"showgrid": True, "gridcolor": "rgba(31,35,40,0.08)", "zeroline": False, "tickfont": {"size": 9, "color": "#6b7280"}},
        annotations=annotations,
        showlegend=False,
    )
    return figure


def _timeline_event_html(events: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for item in events[:4]:
        date_text = str(item.get("event_date") or item.get("date") or "").strip() or "-"
        title = _compact_text(str(item.get("title") or "").strip() or "未命名事件", limit=56)
        
        # Get sentiment if available
        sentiment = str(item.get("sentiment") or "neutral").strip().lower()
        if sentiment not in {"positive", "negative", "neutral"}:
            sentiment = "neutral"
        sentiment_text = {"positive": "正向", "negative": "负向", "neutral": "中性"}[sentiment]
        
        sentiment_html = f"<span class='pf-sentiment pf-sentiment-{sentiment}'>{sentiment_text}</span>"
        
        rows.append(
            f"<div class='pf-timeline-event'>"
            f"<div class='pf-timeline-date'>{escape(date_text)}</div>"
            f"<div style='flex:1;'>"
            f"<div class='pf-timeline-content'>{escape(title)}</div>"
            f"</div>"
            f"{sentiment_html}"
            f"</div>"
        )
    if not rows:
        rows.append("<div style='color:var(--muted);padding:0.5rem 0;'>当前没有可展示的事件。</div>")
    return "".join(rows)


def _compact_text(text: str, *, limit: int) -> str:
    compact = " ".join(str(text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[:limit] + "..."


def _timeline_event_label(text: str, limit: int = 12) -> str:
    """Compact event label for timeline chart annotations."""
    compact = " ".join(str(text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[:limit] + "..."


def _relationship_layout(nodes: list[dict[str, Any]]) -> dict[str, tuple[float, float]]:
    """Horizontal layout: center theme node, others distributed left/right."""
    grouped: dict[str, list[str]] = {}
    for item in nodes:
        node_id = str(item.get("id") or "").strip()
        if not node_id:
            continue
        grouped.setdefault(str(item.get("role") or "other"), []).append(node_id)

    positions: dict[str, tuple[float, float]] = {}
    
    # Center theme node
    if grouped.get("theme"):
        positions[grouped["theme"][0]] = (0.0, 0.0)
    
    # Left side: suppliers (arranged vertically)
    left_nodes = grouped.get("supplier", [])
    for idx, node_id in enumerate(left_nodes[:3]):  # Max 3 on each side
        y_pos = (len(left_nodes) - 1) * 0.4 / 2 - idx * 0.4 if len(left_nodes) > 1 else 0
        positions[node_id] = (-1.2, y_pos)
    
    # Right side: customers (arranged vertically)
    right_nodes = grouped.get("customer", [])
    for idx, node_id in enumerate(right_nodes[:3]):
        y_pos = (len(right_nodes) - 1) * 0.4 / 2 - idx * 0.4 if len(right_nodes) > 1 else 0
        positions[node_id] = (1.2, y_pos)
    
    # Bottom: competitors (horizontal)
    bottom_nodes = grouped.get("competitor", [])
    for idx, node_id in enumerate(bottom_nodes[:2]):
        x_pos = -0.5 + idx * 1.0 if len(bottom_nodes) > 1 else 0
        positions[node_id] = (x_pos, -0.8)
    
    # Top: others (horizontal)
    top_nodes = grouped.get("other", [])
    for idx, node_id in enumerate(top_nodes[:2]):
        x_pos = -0.5 + idx * 1.0 if len(top_nodes) > 1 else 0
        positions[node_id] = (x_pos, 0.8)
        
    return positions


def _relationship_color(role: str) -> str:
    """Soft pastel colors matching the reference style."""
    return {
        "theme": "#e8e8e8",      # Gray center
        "supplier": "#e8d5c4",   # Warm beige
        "customer": "#d4e4d1",   # Soft green
        "competitor": "#e4d4d1", # Soft pink/beige
        "other": "#d4d8e4",      # Soft blue
    }.get(role, "#e0e0e0")


def _relationship_figure(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> go.Figure:
    positions = _relationship_layout(nodes)
    figure = go.Figure()
    
    # Draw edges first (behind nodes)
    for edge in edges:
        start = positions.get(str(edge.get("from") or ""))
        end = positions.get(str(edge.get("to") or ""))
        if not start or not end:
            continue
        figure.add_trace(
            go.Scatter(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                mode="lines",
                line={"width": 1.5, "color": "rgba(150,150,150,0.4)"},
                hoverinfo="skip",
                showlegend=False,
            )
        )
    
    # Draw nodes as markers (theme is circle, others use rounded rect effect via marker symbol)
    role_order = ["supplier", "customer", "competitor", "other", "theme"]
    for role in role_order:
        role_nodes = [item for item in nodes if str(item.get("role") or "other") == role]
        if not role_nodes:
            continue
            
        xs = []
        ys = []
        texts = []
        for item in role_nodes:
            node_id = str(item.get("id") or "")
            if node_id in positions:
                pos = positions[node_id]
                xs.append(pos[0])
                ys.append(pos[1])
                texts.append(node_id)
        
        if not xs:
            continue
            
        # Theme node is circular and larger, others are smaller
        if role == "theme":
            figure.add_trace(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode="markers+text",
                    text=texts,
                    textposition="middle center",
                    textfont={"size": 11, "color": "#333", "family": "Arial, sans-serif"},
                    marker={
                        "size": 35,
                        "color": "#e8e8e8",
                        "line": {"width": 1.5, "color": "#bbb"},
                        "symbol": "circle",
                    },
                    hoverinfo="text",
                    hovertext=texts,
                    showlegend=False,
                )
            )
        else:
            # Other nodes use diamond/square shape with color
            figure.add_trace(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode="markers+text",
                    text=texts,
                    textposition="middle center",
                    textfont={"size": 9, "color": "#555", "family": "Arial, sans-serif"},
                    marker={
                        "size": 28,
                        "color": _relationship_color(role),
                        "line": {"width": 1, "color": "rgba(0,0,0,0.1)"},
                        "symbol": "diamond" if role in ["supplier", "customer"] else "square",
                    },
                    hoverinfo="text",
                    hovertext=texts,
                    showlegend=False,
                )
            )

    figure.update_layout(
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        height=220,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        xaxis={"visible": False, "range": [-1.6, 1.6], "fixedrange": True},
        yaxis={"visible": False, "range": [-1.2, 1.2], "fixedrange": True},
        showlegend=False,
        dragmode=False,
    )
    return figure


def _render_stock_wiki_cards(result: dict[str, Any]) -> None:
    data = dict(result.get("data") or {})
    metadata = dict(result.get("metadata") or {})
    failure_mask = dict(metadata.get("failure_mask") or {})
    skills = dict(data.get("skills") or {})

    summary_data = dict(data.get("summary") or {})
    entity_data = dict(data.get("entity_info") or {})
    timeline_data = dict(data.get("timeline") or {})
    calendar_data = dict(data.get("watch_calendar") or {})
    relationship_data = dict(data.get("relationship") or {})

    company = str(entity_data.get("company_name") or summary_data.get("company_name") or metadata.get("company_name") or "标的")
    st.markdown(f"<h2 class='pf-section-title'>{escape(company)}</h2>", unsafe_allow_html=True)
    st.markdown('<h2 class="pf-section-title">Stock Wiki Cards</h2>', unsafe_allow_html=True)

    # Summary
    summary_skill = dict(skills.get("summary") or {})
    metrics = dict(summary_data.get("metrics") or {})
    missing = [str(item) for item in list(summary_data.get("metrics_missing") or [])]
    data_origin = str(summary_data.get("data_origin") or "")
    network_evidence = [dict(item) for item in list(summary_data.get("network_evidence") or []) if isinstance(item, dict)]
    price_last = metrics.get("price_last")
    kv_rows = []
    for key in ("mkt_cap", "pe_ttm", "vol_20d", "pb", "ret_1d", "ret_5d"):
        if key in metrics and metrics.get(key) is not None:
            kv_rows.append((key, _format_metric_value(metrics.get(key))))
    if not kv_rows:
        kv_rows = [(key, _format_metric_value(val)) for key, val in list(metrics.items())[:6] if val is not None]
    summary_bullets = [f"{key}: {_format_metric_value(value)}" for key, value in list(metrics.items())[:4] if value is not None]
    summary_reason = str(failure_mask.get("summary") or "").strip()
    if not summary_reason and network_evidence:
        summary_reason = str(network_evidence[0].get("error") or "network").strip()
    if missing:
        summary_bullets.extend(
            [f"{item}: 不可用（{summary_reason or '数据暂不可达'}）" for item in missing[:3]]
        )
    if data_origin:
        summary_bullets.append(f"data_origin: {data_origin}")
    summary_text, summary_bullets = _masked_or_default(
        skill="summary",
        failure_mask=failure_mask,
        default_summary=str(summary_data.get("summary") or "已输出核心行情与估值指标。"),
        default_bullets=summary_bullets or ["当前无可展示的行情指标。"],
    )
    kv_html = "".join(
        f"<div><div class='pf-kv-label'>{escape(label)}</div><div class='pf-kv-value'>{escape(value)}</div></div>"
        for label, value in kv_rows[:6]
    )
    bullet_html = "".join(f"<li>{escape(item)}</li>" for item in summary_bullets[:6])
    price_text = "--" if price_last is None else f"${float(price_last):.2f}"
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-head">
            <div class="pf-card-title">Stock Summary</div>
            <div class="pf-card-badge">{escape(_card_badge(summary_skill, "Active"))}</div>
          </div>
          <div class="pf-big-num">{escape(price_text)}</div>
          <div class="pf-kv-grid">{kv_html}</div>
          <div>{escape(summary_text)}</div>
          <ul class="pf-list">{bullet_html}</ul>
          <div class="pf-foot">{escape(_source_footer(summary_skill, "AkShare"))}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # Entity
    entity_skill = dict(skills.get("entity_info") or {})
    entity_summary, entity_bullets = _masked_or_default(
        skill="entity_info",
        failure_mask=failure_mask,
        default_summary=str(entity_data.get("summary") or "暂无公司主体介绍。"),
        default_bullets=[
            f"公司: {entity_data.get('company_name') or company}",
            f"代码: {entity_data.get('symbol') or metadata.get('symbol') or '-'}",
        ],
    )
    entity_bullet_html = "".join(f"<li>{escape(item)}</li>" for item in entity_bullets)
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-head">
            <div class="pf-card-title">Entity: Who is {escape(company)}?</div>
            <div class="pf-card-badge">{escape(_card_badge(entity_skill, "Tech & Auto"))}</div>
          </div>
          <div>{escape(entity_summary)}</div>
          <ul class="pf-list">{entity_bullet_html}</ul>
          <div class="pf-foot">{escape(_source_footer(entity_skill, "kimi"))}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # Timeline
    timeline_skill = dict(skills.get("timeline") or {})
    events = [dict(item) for item in list(timeline_data.get("events") or []) if isinstance(item, dict)]
    series = [dict(item) for item in list(timeline_data.get("series") or []) if isinstance(item, dict)]
    timeline_data_origin = str(timeline_data.get("data_origin") or "")
    timeline_network_evidence = [
        dict(item) for item in list(timeline_data.get("network_evidence") or []) if isinstance(item, dict)
    ]
    timeline_summary, timeline_bullets = _masked_or_default(
        skill="timeline",
        failure_mask=failure_mask,
        default_summary=str(timeline_data.get("summary") or "近三个月价格与事件时间线。"),
        default_bullets=[str(item.get("title") or "") for item in events[:3] if str(item.get("title") or "").strip()] or ["当前没有可展示的事件。"],
    )
    if timeline_data_origin:
        timeline_bullets.append(f"data_origin: {timeline_data_origin}")
    if timeline_network_evidence:
        first = timeline_network_evidence[0]
        timeline_bullets.append(
            f"网络证据: {first.get('interface') or 'akshare'} {first.get('status') or 'error'}"
        )
    timeline_bullet_html = "".join(f"<li>{escape(item)}</li>" for item in timeline_bullets)
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-head">
            <div class="pf-card-title">Event Timeline: Price vs Key Dates</div>
            <div class="pf-card-badge">{escape(_card_badge(timeline_skill, "Price & Event"))}</div>
          </div>
          <div>{escape(timeline_summary)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    if series and "timeline" not in failure_mask:
        st.plotly_chart(_timeline_figure(series, events), use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        f"""
        <section class="pf-mobile-card" style="margin-top:-0.35rem;">
          <ul class="pf-list">{timeline_bullet_html}</ul>
          <div class="pf-foot">{escape(_source_footer(timeline_skill, "MarketWatch"))}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # Calendar
    calendar_skill = dict(skills.get("watch_calendar") or {})
    calendar_summary, calendar_bullets = _masked_or_default(
        skill="watch_calendar",
        failure_mask=failure_mask,
        default_summary=str(calendar_data.get("summary") or "近期关键事件日历。"),
        default_bullets=[],
    )
    calendar_rows = [dict(item) for item in list(calendar_data.get("items") or []) if isinstance(item, dict)][:4]
    if not calendar_rows and not calendar_bullets:
        calendar_bullets = ["当前没有可展示的日历节点。"]
    row_html = ""
    for item in calendar_rows:
        row_html += (
            "<div style='display:flex;justify-content:space-between;gap:0.5rem;margin-bottom:0.35rem;'>"
            f"<div><strong>{escape(str(item.get('date') or '-'))}</strong> {escape(str(item.get('event') or ''))}</div>"
            f"{_watch_calendar_actions_html(item.get('url'))}</div>"
        )
    if calendar_bullets:
        row_html += "".join(f"<div style='margin-bottom:0.25rem;'>• {escape(item)}</div>" for item in calendar_bullets)
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-head">
            <div class="pf-card-title">Variables: Watch Calendar</div>
            <div class="pf-card-badge">{escape(_card_badge(calendar_skill, "Upcoming"))}</div>
          </div>
          <div>{escape(calendar_summary)}</div>
          <div style="margin-top:0.45rem;">{row_html}</div>
          <div class="pf-foot">{escape(_source_footer(calendar_skill, "IR"))}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # Relationship
    relationship_skill = dict(skills.get("relationship") or {})
    rel_summary, rel_bullets = _masked_or_default(
        skill="relationship",
        failure_mask=failure_mask,
        default_summary=str(relationship_data.get("summary") or "关系图谱结果暂缺。"),
        default_bullets=[],
    )
    nodes = [dict(item) for item in list(relationship_data.get("nodes") or []) if isinstance(item, dict)]
    edges = [dict(item) for item in list(relationship_data.get("edges") or []) if isinstance(item, dict)]
    chips = "".join(
        f"<span class='pf-chip'>{escape(str(item.get('id') or '-'))}</span>"
        for item in nodes[:6]
    )
    if not chips:
        chips = "<span class='pf-chip'>nodes: 0</span><span class='pf-chip'>edges: 0</span>"
    if rel_bullets:
        chips += "".join(f"<span class='pf-chip'>{escape(item)}</span>" for item in rel_bullets)
    if bool(relationship_data.get("pending")):
        chips += "<span class='pf-chip'>状态: 正在深度分析中...</span>"
    st.markdown(
        f"""
        <section class="pf-mobile-card">
          <div class="pf-card-head">
            <div class="pf-card-title">Relationship: Connections & Influences</div>
            <div class="pf-card-badge">{escape(_card_badge(relationship_skill, "Map"))}</div>
          </div>
          <div class="pf-card-sub">{escape(rel_summary)}</div>
          <div class="pf-chip-row">{chips}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    if nodes:
        st.plotly_chart(
            _relationship_figure(nodes, edges),
            use_container_width=True,
            config={"displayModeBar": False},
            key=f"relationship-full-{len(nodes)}-{len(edges)}",
        )
    st.markdown(
        f"""
        <section class="pf-mobile-card" style="margin-top:-0.35rem;">
          <div class="pf-chip-row">{chips}</div>
          <div class="pf-foot">{escape(_source_footer(relationship_skill, "Crunchbase"))}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<h2 class="pf-section-title">Sources & Time</h2>', unsafe_allow_html=True)
    st.caption(
        f"generated_at={metadata.get('generated_at', '')} | trace_id={metadata.get('trace_id', '')} | symbol={metadata.get('symbol', '')}"
    )


def _block_html(block: dict[str, Any]) -> str:
    bullets = list(block.get("bullets") or [])
    bullet_html = "".join(f"<li>{escape(str(item))}</li>" for item in bullets)
    return f"""
        <section class="pf-mobile-card">
          <div class="pf-card-sub">{escape(str(block.get('type', '')))}</div>
          <div class="pf-card-title">{escape(str(block.get('title', '')))}</div>
          <div>{escape(str(block.get('summary', '')))}</div>
          <ul class="pf-list">{bullet_html}</ul>
        </section>
    """


def render_blocks(result: dict[str, Any]) -> None:
    blocks = list((result.get("data") or {}).get("blocks") or [])
    st.markdown('<h2 class="pf-section-title">Garden Blocks</h2>', unsafe_allow_html=True)
    if not blocks:
        st.markdown('<div class="pf-empty">当前没有可展示的 blocks。</div>', unsafe_allow_html=True)
        return
    for block in blocks:
        st.markdown(_block_html(block), unsafe_allow_html=True)


def _resolve_chart_rows(chart_spec: dict[str, Any], local_context: dict[str, Any]) -> list[dict[str, Any]]:
    data_ref = str(chart_spec.get("data_ref") or "")
    if not data_ref.startswith("local://raw_bundle/"):
        return []
    key = data_ref.replace("local://raw_bundle/", "", 1)
    raw_bundle = dict(local_context.get("raw_bundle") or {})
    rows = raw_bundle.get(key)
    return list(rows or []) if isinstance(rows, list) else []


def _line_chart(chart_spec: dict[str, Any], rows: list[dict[str, Any]]) -> go.Figure:
    figure = go.Figure()
    palette = ["#171411", "#8a8a8a", "#b8b8b8"]
    x_key = str(chart_spec.get("x_key") or "date")
    for index, y_key in enumerate(list(chart_spec.get("y_keys") or [])):
        xs = [row.get(x_key) for row in rows]
        ys = [row.get(y_key) for row in rows]
        figure.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines",
                name=str(y_key),
                line={"width": 2, "color": palette[index % len(palette)]},
            )
        )
    figure.update_layout(
        title=str(chart_spec.get("title") or ""),
        margin={"l": 20, "r": 16, "t": 40, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.88)",
        legend={"orientation": "h", "y": 1.07, "x": 0},
        font={"family": "Public Sans, sans-serif", "color": "#171411", "size": 12},
    )
    figure.update_xaxes(showgrid=False, zeroline=False)
    figure.update_yaxes(showgrid=True, gridcolor="rgba(23,20,17,0.08)", zeroline=False)
    return figure


def render_charts(result: dict[str, Any], local_context: dict[str, Any] | None = None) -> None:
    chart_index = list((result.get("data") or {}).get("chart_index") or [])
    context = dict(local_context or {})
    st.markdown('<h2 class="pf-section-title">Charts</h2>', unsafe_allow_html=True)
    if not chart_index:
        st.markdown('<div class="pf-empty">当前没有可展示的图表。</div>', unsafe_allow_html=True)
        return

    rendered = False
    for index, chart_spec in enumerate(chart_index):
        rows = _resolve_chart_rows(chart_spec, context)
        if not rows:
            continue
        figure = _line_chart(chart_spec, rows)
        chart_key = f"chart-index-{index}-{chart_spec.get('chart_id', 'chart')}"
        st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False}, key=chart_key)
        rendered = True
    if not rendered:
        st.markdown('<div class="pf-empty">图表索引存在，但当前没有可渲染的数据。</div>', unsafe_allow_html=True)


def render_references(result: dict[str, Any]) -> None:
    references = list((result.get("data") or {}).get("references") or [])
    metadata = dict(result.get("metadata") or {})
    st.markdown('<h2 class="pf-section-title">Sources & Time</h2>', unsafe_allow_html=True)
    if not references:
        st.markdown('<div class="pf-empty">当前没有引用来源。</div>', unsafe_allow_html=True)
    else:
        for reference in references[:5]:
            title = escape(str(reference.get("title") or ""))
            source = escape(str(reference.get("source") or ""))
            published_at = escape(str(reference.get("published_at") or ""))
            url = reference.get("url")
            st.markdown(
                f"""
                <section class="pf-mobile-card">
                  <div class="pf-card-sub">{escape(str(reference.get("kind", "")))}</div>
                  <div><strong>{title}</strong></div>
                  <div class="pf-foot">{source} · {published_at}</div>
                </section>
                """,
                unsafe_allow_html=True,
            )
            if url:
                st.markdown(f"[Open Source]({url})")
    st.caption(f"generated_at={metadata.get('generated_at', '')} | trace_id={metadata.get('trace_id', '')} | model={metadata.get('model', '')}")


def render_debug(trace: dict[str, Any], result: dict[str, Any], local_context: dict[str, Any] | None = None) -> None:
    metadata = dict(result.get("metadata") or {})
    with st.expander("调试信息", expanded=False):
        st.markdown("**Usage**")
        st.json(metadata.get("usage") or {})
        st.markdown("**Degrade Reason**")
        st.code(str(metadata.get("degrade_reason") or ""))
        st.markdown("**Tool Trace**")
        st.json(trace.get("tool_events") or [])
        st.markdown("**Event Log**")
        st.json(trace.get("events") or [])
        st.markdown("**Stream Events**")
        st.json(trace.get("stream_events") or [])
        st.markdown("**Local Context**")
        st.json(local_context or {})
        dump = {
            "result": result,
            "trace": trace,
            "local_context": local_context or {},
        }
        st.download_button(
            "下载诊断包 JSON",
            data=json.dumps(dump, ensure_ascii=False, indent=2),
            file_name=f"pomefi_debug_{metadata.get('trace_id', 'trace')}.json",
            mime="application/json",
        )


def render_result_card(
    *,
    result: dict[str, Any],
    trace: dict[str, Any],
    local_context: dict[str, Any] | None = None,
) -> None:
    # 这是前台最终渲染入口。
    # 这里渲染的是 Garden Card，不是自由聊天文本。
    render_status(result)
    if _is_stock_wiki_result(result):
        render_progressive_cards(
            _build_card_store_from_result(result),
            metadata=dict(result.get("metadata") or {}),
            trace=trace,
            local_context=local_context,
        )
        render_debug(trace, result, local_context=local_context)
        return
    render_answer(result)
    render_blocks(result)
    render_charts(result, local_context=local_context)
    render_references(result)
    render_debug(trace, result, local_context=local_context)
