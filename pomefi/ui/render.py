from __future__ import annotations

from html import escape
from typing import Any

import plotly.graph_objects as go
import streamlit as st


def inject_page_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        :root {
          --bg: #f5f2ea;
          --paper: rgba(255, 255, 255, 0.82);
          --ink: #171411;
          --muted: #5d564f;
          --line: rgba(23, 20, 17, 0.12);
          --soft: rgba(23, 20, 17, 0.05);
          --success: #244a2f;
          --warning: #7a4b16;
          --danger: #7b261e;
        }

        .stApp {
          background:
            radial-gradient(circle at top left, rgba(33, 30, 25, 0.08), transparent 28%),
            radial-gradient(circle at top right, rgba(120, 109, 96, 0.12), transparent 22%),
            linear-gradient(180deg, #f7f3eb 0%, #efe8dc 100%);
          color: var(--ink);
        }

        .block-container {
          padding-top: 2.5rem;
          padding-bottom: 3rem;
          max-width: 1160px;
        }

        h1, h2, h3 {
          font-family: "Cormorant Garamond", Georgia, serif !important;
          letter-spacing: 0.01em;
        }

        html, body, [class*="css"] {
          font-family: "IBM Plex Sans", "Avenir Next", sans-serif;
        }

        .pf-hero {
          border: 1px solid var(--line);
          background: linear-gradient(135deg, rgba(255,255,255,0.78), rgba(247,243,235,0.9));
          border-radius: 28px;
          padding: 1.5rem 1.7rem;
          box-shadow: 0 18px 60px rgba(29, 25, 20, 0.06);
          margin-bottom: 1rem;
        }

        .pf-kicker {
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 0.16em;
          color: var(--muted);
          margin-bottom: 0.4rem;
        }

        .pf-subtitle {
          font-size: 1.02rem;
          color: var(--muted);
          max-width: 48rem;
          line-height: 1.55;
        }

        .pf-status {
          display: inline-flex;
          align-items: center;
          gap: 0.35rem;
          padding: 0.28rem 0.8rem;
          border-radius: 999px;
          border: 1px solid var(--line);
          font-size: 0.82rem;
          letter-spacing: 0.04em;
          text-transform: uppercase;
          background: rgba(255,255,255,0.72);
          margin-bottom: 0.8rem;
        }

        .pf-status-valid { color: var(--success); border-color: rgba(36, 74, 47, 0.24); background: rgba(36, 74, 47, 0.08); }
        .pf-status-degraded { color: var(--warning); border-color: rgba(122, 75, 22, 0.22); background: rgba(122, 75, 22, 0.08); }
        .pf-status-error { color: var(--danger); border-color: rgba(123, 38, 30, 0.22); background: rgba(123, 38, 30, 0.08); }

        .pf-answer {
          border: 1px solid var(--line);
          background: var(--paper);
          border-radius: 24px;
          padding: 1.2rem 1.3rem;
          box-shadow: 0 14px 40px rgba(29, 25, 20, 0.05);
          margin-bottom: 1rem;
        }

        .pf-answer-label {
          font-size: 0.78rem;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--muted);
          margin-bottom: 0.55rem;
        }

        .pf-answer-text {
          font-size: 1.05rem;
          line-height: 1.7;
          color: var(--ink);
        }

        .pf-section-title {
          margin-top: 1.1rem;
          margin-bottom: 0.55rem;
          color: var(--ink);
        }

        .pf-block {
          border: 1px solid var(--line);
          background: rgba(255,255,255,0.74);
          border-radius: 22px;
          padding: 1rem 1.05rem;
          min-height: 100%;
          box-shadow: 0 10px 30px rgba(29, 25, 20, 0.04);
        }

        .pf-block-type {
          font-size: 0.76rem;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: var(--muted);
          margin-bottom: 0.35rem;
        }

        .pf-block-title {
          font-size: 1.55rem;
          margin-bottom: 0.25rem;
        }

        .pf-block-summary {
          color: var(--ink);
          line-height: 1.65;
          margin-bottom: 0.7rem;
        }

        .pf-reference {
          border-top: 1px solid var(--line);
          padding-top: 0.75rem;
          margin-top: 0.75rem;
        }

        .pf-meta {
          color: var(--muted);
          font-size: 0.92rem;
        }

        .pf-empty {
          border: 1px dashed var(--line);
          background: rgba(255,255,255,0.55);
          border-radius: 18px;
          padding: 0.9rem 1rem;
          color: var(--muted);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <section class="pf-hero">
          <div class="pf-kicker">PomeFi v0.6.4</div>
          <h1>Finance Garden</h1>
          <div class="pf-subtitle">
            不是聊天框，也不是旧技能卡。这里把研究、指标、风险和修剪建议压成一页可追溯的金融花园卡片。
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_question_hint() -> None:
    st.caption("示例：`300750 现在估值高吗？`  `宁德时代最近有什么风险？`  `今天最重要的一条 AI 新闻是什么？`")


def _status_class(status: str) -> str:
    return {
        "valid": "pf-status-valid",
        "degraded": "pf-status-degraded",
        "error": "pf-status-error",
    }.get(status, "pf-status-degraded")


def render_status(result: dict[str, Any]) -> None:
    status = str(result.get("quality_status") or "degraded")
    degrade_reason = str((result.get("metadata") or {}).get("degrade_reason") or "").strip()
    text = status if not degrade_reason else f"{status} · {degrade_reason}"
    st.markdown(
        f'<div class="pf-status {_status_class(status)}">{text}</div>',
        unsafe_allow_html=True,
    )


def render_answer(result: dict[str, Any]) -> None:
    answer = str((result.get("data") or {}).get("answer") or "").strip()
    if not answer:
        answer = "当前没有可展示的回答文本。"
    st.markdown(
        f"""
        <section class="pf-answer">
          <div class="pf-answer-label">Primary Read</div>
          <div class="pf-answer-text">{escape(answer)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _block_html(block: dict[str, Any]) -> str:
    bullets = list(block.get("bullets") or [])
    bullet_html = "".join(f"<li>{escape(str(item))}</li>" for item in bullets)
    return f"""
        <section class="pf-block">
          <div class="pf-block-type">{escape(str(block.get('type', '')))}</div>
          <div class="pf-block-title">{escape(str(block.get('title', '')))}</div>
          <div class="pf-block-summary">{escape(str(block.get('summary', '')))}</div>
          <ul>{bullet_html}</ul>
        </section>
    """


def render_blocks(result: dict[str, Any]) -> None:
    blocks = list((result.get("data") or {}).get("blocks") or [])
    st.markdown('<h2 class="pf-section-title">Garden Blocks</h2>', unsafe_allow_html=True)
    if not blocks:
        st.markdown('<div class="pf-empty">当前没有可展示的 blocks。</div>', unsafe_allow_html=True)
        return

    for start in range(0, len(blocks), 2):
        cols = st.columns(2, gap="medium")
        for col, block in zip(cols, blocks[start:start + 2]):
            with col:
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
    palette = ["#171411", "#7d7469", "#b3a79a"]
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
                line={"width": 2.3, "color": palette[index % len(palette)]},
            )
        )
    figure.update_layout(
        title=str(chart_spec.get("title") or ""),
        margin={"l": 20, "r": 16, "t": 46, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.8)",
        legend={"orientation": "h", "y": 1.1, "x": 0},
        font={"family": "IBM Plex Sans, sans-serif", "color": "#171411", "size": 12},
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
    for chart_spec in chart_index:
        rows = _resolve_chart_rows(chart_spec, context)
        if not rows:
            continue
        figure = _line_chart(chart_spec, rows)
        st.plotly_chart(figure, use_container_width=True)
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
                <section class="pf-block pf-reference">
                  <div class="pf-block-type">{escape(str(reference.get("kind", "")))}</div>
                  <div class="pf-block-summary"><strong>{title}</strong></div>
                  <div class="pf-meta">{source} · {published_at}</div>
                </section>
                """,
                unsafe_allow_html=True,
            )
            if url:
                st.markdown(f"[Open Source]({url})")
    st.caption(
        f"generated_at={metadata.get('generated_at', '')} | trace_id={metadata.get('trace_id', '')} | model={metadata.get('model', '')}"
    )


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
        st.markdown("**Local Context**")
        st.json(local_context or {})


def render_result_card(
    *,
    result: dict[str, Any],
    trace: dict[str, Any],
    local_context: dict[str, Any] | None = None,
) -> None:
    render_status(result)
    render_answer(result)
    render_blocks(result)
    render_charts(result, local_context=local_context)
    render_references(result)
    render_debug(trace, result, local_context=local_context)
