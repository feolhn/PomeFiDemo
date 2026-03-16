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
          --bg: #f3f4f6;
          --card: #ffffff;
          --ink: #1f2328;
          --muted: #6b7280;
          --line: #d9dce1;
          --ok: #3f6e4f;
          --warn: #8a6d2f;
          --err: #8b3a3a;
          --pill: #eef2f7;
        }

        .stApp {
          background: var(--bg);
          color: var(--ink);
        }

        .block-container {
          max-width: 760px;
          padding-top: 1.1rem;
          padding-bottom: 2rem;
          font-family: "Public Sans", "Helvetica Neue", Arial, sans-serif;
        }

        h1, h2, h3 {
          font-family: "Public Sans", "Helvetica Neue", Arial, sans-serif !important;
          font-weight: 700 !important;
          letter-spacing: 0;
        }

        .pf-hero {
          margin-bottom: 0.4rem;
        }

        .pf-kicker {
          display: none;
        }

        .pf-subtitle {
          font-size: 0.88rem;
          color: var(--muted);
          line-height: 1.45;
          margin-top: -0.15rem;
          margin-bottom: 0.3rem;
        }

        .pf-status {
          display: inline-flex;
          align-items: center;
          border-radius: 999px;
          border: 1px solid var(--line);
          padding: 0.2rem 0.65rem;
          font-size: 0.75rem;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          background: #fff;
          margin-right: 0.45rem;
          margin-bottom: 0.5rem;
        }

        .pf-status-valid { color: var(--ok); border-color: #bfd6c4; background: #edf7ef; }
        .pf-status-degraded { color: var(--warn); border-color: #eadcae; background: #fcf7e7; }
        .pf-status-error { color: var(--err); border-color: #e5b7b7; background: #fceded; }

        .pf-section-title {
          margin-top: 0.7rem;
          margin-bottom: 0.5rem;
          font-size: 1.25rem;
        }

        .pf-mobile-card {
          border: 1px solid var(--line);
          background: var(--card);
          border-radius: 14px;
          padding: 0.75rem 0.8rem 0.65rem 0.8rem;
          margin-bottom: 0.65rem;
          box-shadow: 0 1px 2px rgba(16, 24, 40, 0.05);
        }

        .pf-card-head {
          display: flex;
          justify-content: space-between;
          gap: 0.5rem;
          align-items: center;
          margin-bottom: 0.35rem;
        }

        .pf-card-title {
          font-weight: 700;
          font-size: 1rem;
        }

        .pf-card-badge {
          border-radius: 999px;
          padding: 0.15rem 0.55rem;
          font-size: 0.72rem;
          border: 1px solid var(--line);
          background: var(--pill);
          color: #46505b;
          white-space: nowrap;
        }

        .pf-card-sub {
          font-size: 0.86rem;
          color: var(--muted);
          margin-bottom: 0.45rem;
        }

        .pf-big-num {
          font-size: 2rem;
          font-weight: 700;
          line-height: 1.05;
          margin-bottom: 0.35rem;
        }

        .pf-list {
          margin: 0.2rem 0 0.3rem 0;
          padding-left: 1.1rem;
        }

        .pf-list li {
          margin-bottom: 0.25rem;
        }

        .pf-chip-row {
          display: flex;
          flex-wrap: wrap;
          gap: 0.35rem;
          margin-top: 0.35rem;
        }

        .pf-chip {
          border-radius: 999px;
          border: 1px solid #cdd4de;
          background: #f7f9fc;
          color: #2e3a48;
          padding: 0.18rem 0.55rem;
          font-size: 0.76rem;
        }

        .pf-foot {
          border-top: 1px solid #eceff3;
          margin-top: 0.5rem;
          padding-top: 0.45rem;
          font-size: 0.78rem;
          color: var(--muted);
        }

        .pf-reminder {
          border-radius: 999px;
          border: 1px solid #d4cbe8;
          background: #f1ecfa;
          color: #5d4f87;
          padding: 0.08rem 0.5rem;
          font-size: 0.72rem;
        }

        .pf-kv-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 0.3rem 0.5rem;
          margin-bottom: 0.3rem;
        }

        .pf-kv-label {
          color: var(--muted);
          font-size: 0.75rem;
        }

        .pf-kv-value {
          font-size: 0.98rem;
          font-weight: 600;
        }

        .pf-empty {
          border: 1px dashed var(--line);
          background: #fafbfc;
          border-radius: 12px;
          padding: 0.75rem 0.8rem;
          color: var(--muted);
          margin-bottom: 0.65rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <section class="pf-hero">
          <h1>Stock Wiki</h1>
          <div class="pf-subtitle">
            生成 Summary / Entity / Timeline / Calendar / Relationship 五张卡片。
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_question_hint() -> None:
    st.caption("示例：`宁德时代怎么看？`  `300750 最近三个月关键事件`  `比亚迪的竞争对手有哪些？`")


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
    }.get(status, "pf-status-degraded")


def render_status(result: dict[str, Any]) -> None:
    status = str(result.get("quality_status") or "degraded")
    metadata = dict(result.get("metadata") or {})
    degrade_reason = str(metadata.get("degrade_reason") or "").strip()
    text = status if not degrade_reason else f"{status} · {degrade_reason}"
    st.markdown(
        f'<div class="pf-status {_status_class(status)}">{text}</div>',
        unsafe_allow_html=True,
    )
    if bool(metadata.get("strict_fail")):
        st.markdown('<div class="pf-status pf-status-error">strict_fail</div>', unsafe_allow_html=True)
        critical = list(metadata.get("critical_failures") or [])
        if critical:
            st.caption(f"关键链路失败：{', '.join(str(item) for item in critical)}")
    if bool(metadata.get("relationship_pending")):
        st.markdown('<div class="pf-status pf-status-degraded">relationship · pending</div>', unsafe_allow_html=True)
        st.caption("Relationship 正在深度分析中，已先展示其他卡片。")


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


def _format_metric_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


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
            line={"width": 2.2, "color": "#bf8f8f"},
            name="Close",
        )
    )
    annotations: list[dict[str, Any]] = []
    for item in events[:3]:
        if not isinstance(item, dict):
            continue
        date_text = str(item.get("date") or "")
        title = str(item.get("title") or "").strip()
        if not date_text or not title:
            continue
        try:
            idx = xs.index(date_text)
        except ValueError:
            continue
        annotations.append(
            {
                "x": xs[idx],
                "y": ys[idx],
                "text": title[:18],
                "showarrow": True,
                "arrowhead": 2,
                "arrowcolor": "#9a7d7d",
                "font": {"size": 10},
            }
        )
    figure.update_layout(
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        height=180,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        xaxis={"showgrid": False, "zeroline": False},
        yaxis={"showgrid": True, "gridcolor": "rgba(31,35,40,0.08)", "zeroline": False},
        annotations=annotations,
        showlegend=False,
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
    price_last = metrics.get("price_last")
    kv_rows = []
    for key in ("mkt_cap", "pe_ttm", "vol_20d", "pb", "ret_1d", "ret_5d"):
        if key in metrics and metrics.get(key) is not None:
            kv_rows.append((key, _format_metric_value(metrics.get(key))))
    if not kv_rows:
        kv_rows = [(key, _format_metric_value(val)) for key, val in list(metrics.items())[:6] if val is not None]
    summary_bullets = [f"{key}: {_format_metric_value(value)}" for key, value in list(metrics.items())[:4] if value is not None]
    if missing:
        summary_bullets.append(f"不可用: {', '.join(missing[:5])}")
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
    bullet_html = "".join(f"<li>{escape(item)}</li>" for item in summary_bullets[:4])
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
    timeline_summary, timeline_bullets = _masked_or_default(
        skill="timeline",
        failure_mask=failure_mask,
        default_summary=str(timeline_data.get("summary") or "近三个月价格与事件时间线。"),
        default_bullets=[str(item.get("title") or "") for item in events[:3] if str(item.get("title") or "").strip()] or ["当前没有可展示的事件。"],
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
            "<div class='pf-reminder'>Set Reminder</div></div>"
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
        for item in nodes[:8]
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
          <div>{escape(rel_summary)}</div>
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
    for chart_spec in chart_index:
        rows = _resolve_chart_rows(chart_spec, context)
        if not rows:
            continue
        figure = _line_chart(chart_spec, rows)
        st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})
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
        _render_stock_wiki_cards(result)
        render_debug(trace, result, local_context=local_context)
        return
    render_answer(result)
    render_blocks(result)
    render_charts(result, local_context=local_context)
    render_references(result)
    render_debug(trace, result, local_context=local_context)
