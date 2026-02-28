from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from streamlit.testing.v1 import AppTest

import app

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_wrapper(tmp_path: Path, *, body: str) -> Path:
    wrapper = tmp_path / "app_wrapper.py"
    script = (
        "import sys\n"
        "from pathlib import Path\n\n"
        f"repo_root = Path(r\"{REPO_ROOT}\")\n"
        "if str(repo_root) not in sys.path:\n"
        "    sys.path.insert(0, str(repo_root))\n\n"
        "import app\n\n"
        f"{body.strip()}\n"
    )
    wrapper.write_text(script, encoding="utf-8")
    return wrapper


def test_resolve_symbol_prefers_code_and_name(monkeypatch) -> None:
    monkeypatch.setattr(
        app,
        "_load_stock_table",
        lambda: [
            {"code": "300750", "name": "宁德时代"},
            {"code": "600519", "name": "贵州茅台"},
        ],
    )

    assert app.resolve_symbol("300750 现在估值高吗") == ("300750", "宁德时代")
    assert app.resolve_symbol("宁德时代") == ("300750", "宁德时代")
    assert app.resolve_symbol("我想看宁德时代最近有什么风险") == ("300750", "宁德时代")


def test_app_renders_empty_state(tmp_path: Path) -> None:
    wrapper = _write_wrapper(
        tmp_path,
        body="""
app._validate_app_config = lambda: (True, '')
app.main()
""",
    )

    at = AppTest.from_file(wrapper)
    at.run()

    markdown_values = [item.value or "" for item in at.markdown]
    assert any("Finance Garden" in value for value in markdown_values)
    assert any("这里会出现新的金融花园卡片" in value for value in markdown_values)


def test_app_renders_valid_payload_after_submit(tmp_path: Path, sample_result_card_input: dict) -> None:
    valid_payload = {
        "card": {
            "data": {
                "question": sample_result_card_input["question"],
                "answer": sample_result_card_input["answer"],
                "blocks": [
                    {"id": "y", "type": "yields", "title": "果实", "summary": "指标", "bullets": ["最新价: 201.50"], "metric_refs": [], "reference_ids": ["ref_1"], "chart_ids": []},
                    {"id": "p", "type": "pests", "title": "害虫", "summary": "风险", "bullets": ["波动率偏高"], "metric_refs": [], "reference_ids": ["ref_1"], "chart_ids": []},
                    {"id": "r", "type": "pruning", "title": "修剪建议", "summary": "先看估值和盈利斜率", "bullets": ["先观察"], "metric_refs": [], "reference_ids": ["ref_1"], "chart_ids": []},
                ],
                "chart_index": [],
                "references": [
                    {"id": "ref_1", "title": "电池行业新闻", "source": "新华社", "published_at": "2026-02-27T08:00:00+08:00", "url": "https://example.com", "kind": "web_search"}
                ],
            },
            "metadata": {
                "generated_at": "2026-02-27T00:00:00+00:00",
                "trace_id": "trace_123",
                "model": "kimi-k2.5",
                "used_tools": ["akshare_tool", "web_search"],
                "sources": ["新华社"],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                "degrade_reason": None,
            },
            "quality_status": "valid",
        },
        "trace": {"tool_events": [], "events": [], "local_context": {}},
        "local_context": {},
    }
    wrapper = _write_wrapper(
        tmp_path,
        body=f"""
app._validate_app_config = lambda: (True, '')
app.run_analysis = lambda question: {repr(valid_payload)}
app.main()
""",
    )

    at = AppTest.from_file(wrapper)
    at.run()
    at.text_area[0].set_value("300750 现在估值高吗？")
    at.button[0].click().run()

    markdown_values = [item.value or "" for item in at.markdown]
    assert any("valid" in value for value in markdown_values)
    assert any("先看估值和盈利斜率" in value for value in markdown_values)
    assert any("新华社" in value for value in markdown_values)


def test_app_renders_degraded_payload_without_chart(tmp_path: Path) -> None:
    degraded_payload = {
        "card": {
            "data": {
                "question": "美股英伟达怎么看",
                "answer": "当前版本只支持 A 股单标的与宏观/新闻类问题。",
                "blocks": [
                    {"id": "y", "type": "yields", "title": "果实", "summary": "降级", "bullets": ["当前不支持"], "metric_refs": [], "reference_ids": [], "chart_ids": []},
                    {"id": "p", "type": "pests", "title": "害虫", "summary": "降级", "bullets": ["unsupported_scope"], "metric_refs": [], "reference_ids": [], "chart_ids": []},
                    {"id": "r", "type": "pruning", "title": "修剪建议", "summary": "请换 A 股问题", "bullets": ["换问题"], "metric_refs": [], "reference_ids": [], "chart_ids": []},
                ],
                "chart_index": [],
                "references": [],
            },
            "metadata": {
                "generated_at": "2026-02-27T00:00:00+00:00",
                "trace_id": "trace_456",
                "model": "kimi-k2.5",
                "used_tools": [],
                "sources": [],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "degrade_reason": "unsupported_scope",
            },
            "quality_status": "degraded",
        },
        "trace": {"tool_events": [], "events": [], "local_context": {}},
        "local_context": {},
    }
    wrapper = _write_wrapper(
        tmp_path,
        body=f"""
app._validate_app_config = lambda: (True, '')
app.run_analysis = lambda question: {repr(degraded_payload)}
app.main()
""",
    )

    at = AppTest.from_file(wrapper)
    at.run()
    at.text_area[0].set_value("美股英伟达怎么看")
    at.button[0].click().run()

    markdown_values = [item.value or "" for item in at.markdown]
    assert any("degraded" in value for value in markdown_values)
    assert any("当前没有可展示的图表" in value or "图表索引存在" in value for value in markdown_values)


def test_app_shows_config_error(tmp_path: Path) -> None:
    wrapper = _write_wrapper(
        tmp_path,
        body="""
app._validate_app_config = lambda: (False, '配置错误')
app.main()
""",
    )

    at = AppTest.from_file(wrapper)
    at.run()

    assert len(at.error) == 1
    assert at.error[0].value == "配置错误"
