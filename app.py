from __future__ import annotations

import json
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from skill_engine import generate_skill_card

st.set_page_config(page_title="PomeFi Demo", layout="wide")


def _render_status_badge(status: str) -> None:
    if status == "valid":
        st.success("质量状态：valid")
    elif status == "degraded":
        st.warning("质量状态：degraded（已启用降级结果）")
    else:
        st.error("质量状态：error（仅展示最小可渲染结构）")


def _dict_pct_to_items(data: dict[str, str]) -> tuple[list[str], list[float]]:
    labels, values = [], []
    for k, v in data.items():
        labels.append(k)
        values.append(float(str(v).replace("%", "")))
    return labels, values


def _render_trend_charts(data: dict[str, Any]) -> None:
    series = data.get("price_series", [])
    if series:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=[x["date"] for x in series],
                y=[x["close"] for x in series],
                mode="lines",
                name="价格",
                line={"color": "#111111", "width": 2},
                yaxis="y",
                hovertemplate="日期=%{x}<br>价格=%{y:.2f}<extra></extra>",
            )
        )

        pe_raw = data.get("valuation_5y", {}).get("current_pe")
        pe_value = None
        if isinstance(pe_raw, (int, float)):
            pe_value = float(pe_raw)
        elif isinstance(pe_raw, str):
            txt = pe_raw.replace("%", "").strip()
            if txt and txt != "N/A":
                try:
                    pe_value = float(txt)
                except Exception:
                    pe_value = None
        if pe_value is not None:
            fig.add_trace(
                go.Scatter(
                    x=[x["date"] for x in series],
                    y=[pe_value for _ in series],
                    mode="lines",
                    name="PE(当前值参照线)",
                    line={"color": "#666666", "dash": "dot"},
                    yaxis="y2",
                    hovertemplate="日期=%{x}<br>PE=%{y:.2f}<extra></extra>",
                )
            )

        fig.update_layout(
            title="价格趋势 + 估值参照",
            template="plotly_white",
            hovermode="x unified",
            legend={"orientation": "h"},
            yaxis={"title": "价格", "rangemode": "normal", "automargin": True},
            yaxis2={"title": "PE", "overlaying": "y", "side": "right", "automargin": True},
        )
        st.plotly_chart(fig, use_container_width=True)


def _render_fund_charts(data: dict[str, Any]) -> None:
    industry = data.get("industry_concentration", {}).get("breakdown", {})
    if industry:
        labels, values = _dict_pct_to_items(industry)
        pie = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.45,
                    marker={"colors": ["#111111", "#444444", "#777777", "#AAAAAA", "#DDDDDD"]},
                )
            ]
        )
        pie.update_layout(title="行业集中度")
        st.plotly_chart(pie, use_container_width=True)

    style = data.get("market_cap_style", {}).get("cap_breakdown", {})
    if style:
        labels, values = _dict_pct_to_items(style)
        bar = go.Figure(
            data=[
                go.Bar(x=labels, y=values, marker={"color": ["#111111", "#555555", "#999999"]})
            ]
        )
        bar.update_layout(title="市值风格分布", template="plotly_white")
        st.plotly_chart(bar, use_container_width=True)


def _render_stock_charts(data: dict[str, Any]) -> None:
    industry = data.get("industry_concentration", {}).get("breakdown", {})
    if industry:
        labels, values = _dict_pct_to_items(industry)
        donut = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.5,
                    marker={"colors": ["#111111", "#444444", "#777777", "#AAAAAA", "#DDDDDD"]},
                )
            ]
        )
        donut.update_layout(title="行业集中度（等权）")
        st.plotly_chart(donut, use_container_width=True)

    style = data.get("market_cap_style", {}).get("style_breakdown", {})
    if style:
        categories = list(style.keys())
        values = [float(str(v).replace("%", "")) for v in style.values()]
        radar = go.Figure()
        radar.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                name="风格分布",
                line={"color": "#222222"},
            )
        )
        radar.update_layout(title="市值风格雷达", polar={"radialaxis": {"visible": True, "range": [0, 100]}})
        st.plotly_chart(radar, use_container_width=True)


def _render_skill_lab_page() -> None:
    st.subheader("Skill Lab")
    st.caption("选择一个 Skill 进入详情页")

    skill_items = [
        ("trend_follower", "趋势跟踪"),
        ("fund_diagnostic", "基金诊断"),
        ("stock_diagnostic", "个股诊断"),
    ]
    for skill_id, display_name in skill_items:
        if st.button(f"{display_name}（{skill_id}）", key=f"open_{skill_id}", use_container_width=True):
            st.session_state["selected_skill"] = skill_id
            st.session_state["page"] = "skll_widget"
            st.rerun()


def _render_skll_widget_page() -> None:
    skill = st.session_state.get("selected_skill")
    if skill not in {"trend_follower", "fund_diagnostic", "stock_diagnostic"}:
        st.warning("未选择 Skill，已返回 Skill Lab。")
        st.session_state["page"] = "skill_lab"
        st.rerun()
        return

    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("返回 Skill Lab", key="back_to_skill_lab"):
            st.session_state["page"] = "skill_lab"
            st.rerun()
    with col_title:
        st.subheader(f"skll_widget · {skill}")

    default_input = {
        "trend_follower": "300750",
        "fund_diagnostic": "001410",
        "stock_diagnostic": "600519,002594,600036,601012,601318",
    }[skill]
    input_key = f"skill_input_{skill}"
    if input_key not in st.session_state:
        st.session_state[input_key] = default_input

    if skill == "trend_follower":
        st.caption("热门公司")
        company_options = [
            ("贵州茅台", "600519"),
            ("宁德时代", "300750"),
            ("东方财富", "300059"),
        ]
        labels = [f"{name}（{code}）" for name, code in company_options]
        selected = st.radio("公司快捷选择", labels, horizontal=True, label_visibility="collapsed")
        selected_code = dict(zip(labels, [code for _, code in company_options]))[selected]
        if st.button("使用该公司代码", key="use_company_code"):
            st.session_state[input_key] = selected_code

    elif skill == "fund_diagnostic":
        st.caption("热门基金")
        fund_options = [
            ("华泰柏瑞沪深 300ETF", "510300"),
            ("华夏国证半导体芯片 ETF", "159995"),
            ("南方中证申万有色金属 ETF", "512400"),
        ]
        labels = [f"{name}（{code}）" for name, code in fund_options]
        selected = st.radio("基金快捷选择", labels, horizontal=False, label_visibility="collapsed")
        selected_code = dict(zip(labels, [code for _, code in fund_options]))[selected]
        if st.button("使用该基金代码", key="use_fund_code"):
            st.session_state[input_key] = selected_code

    input_text = st.text_input("输入参数", key=input_key)
    stream_box = st.empty()

    if st.button("生成 Skill 卡片", type="primary"):
        if skill == "stock_diagnostic":
            payload_input: Any = [x.strip() for x in input_text.split(",") if x.strip()]
        else:
            payload_input = input_text.strip()

        with st.spinner("生成中..."):
            stream_box.info("正在流式生成分析内容...")

            def on_stream(text: str) -> None:
                preview = text[-800:]
                stream_box.code(preview, language="text")

            result = generate_skill_card(
                skill,
                payload_input,
                stream_mode=True,
                stream_callback=on_stream,
            )
            stream_box.empty()
            st.session_state[f"last_result_{skill}"] = result

    result = st.session_state.get(f"last_result_{skill}")
    if result:
        _render_status_badge(result["quality_status"])
        data = result["data"]

        st.markdown(f"**Skill ID**: `{data.get('skill_id', 'N/A')}`")
        st.markdown(f"**分类**: {data.get('skill_category', 'N/A')}")
        st.markdown(f"**创建者**: {data.get('creator', 'N/A')}")
        if result["quality_status"] == "error" and data.get("fetch_error") == "抓取失败":
            st.error("抓取失败")
        else:
            if skill == "trend_follower":
                _render_trend_charts(data)
            elif skill == "fund_diagnostic":
                _render_fund_charts(data)
            else:
                _render_stock_charts(data)

        st.markdown("### 结构化输出（JSON）")
        st.code(json.dumps(result, ensure_ascii=False, indent=2), language="json")
        st.caption(data.get("disclaimer", ""))


def main() -> None:
    st.title("PomeFi Skill Lab")
    if "page" not in st.session_state:
        st.session_state["page"] = "skill_lab"
    if "selected_skill" not in st.session_state:
        st.session_state["selected_skill"] = None

    if st.session_state["page"] == "skll_widget":
        _render_skll_widget_page()
    else:
        _render_skill_lab_page()


if __name__ == "__main__":
    main()
