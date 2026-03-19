from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest
from pomefi.ui.render import _timeline_figure

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_wrapper(tmp_path: Path, payload: dict) -> Path:
    wrapper = tmp_path / "wiki_wrapper.py"
    wrapper.write_text(
        (
            "import sys\n"
            "from pathlib import Path\n"
            f"repo_root = Path(r\"{REPO_ROOT}\")\n"
            "if str(repo_root) not in sys.path:\n"
            "    sys.path.insert(0, str(repo_root))\n"
            "import app\n"
            "app._validate_app_config = lambda: (True, '')\n"
            f"app.run_analysis_stream = lambda question, on_event=None: {repr(payload)}\n"
            "app.main()\n"
        ),
        encoding="utf-8",
    )
    return wrapper


def test_stock_wiki_renders_five_cards(tmp_path: Path) -> None:
    payload = {
        "card": {
            "data": {
                "question": "宁德时代怎么看",
                "summary": {"summary": "价格稳中有升", "metrics": {"price_last": 201.5}},
                "entity_info": {"summary": "动力电池龙头"},
                "timeline": {"summary": "近三个月事件有两条", "events": [{"title": "事件A"}]},
                "watch_calendar": {"summary": "未来30天有财报日", "items": [{"date": "2026-03-30", "event": "年报"}]},
                "relationship": {"summary": "上下游集中", "pending": False, "nodes": [{"id": "宁德时代"}], "edges": []},
                "skills": {},
            },
            "metadata": {
                "trace_id": "trace_ui",
                "symbol": "300750",
                "relationship_pending": False,
                "partial_release": False,
                "degrade_reason": None,
            },
            "quality_status": "valid",
            "sources": [],
        },
        "trace": {"route": {}, "skill_results": {}},
        "local_context": {},
    }
    wrapper = _write_wrapper(tmp_path, payload)
    at = AppTest.from_file(wrapper)
    at.run()
    at.text_area[0].set_value("宁德时代怎么看")
    at.button[0].click().run()
    markdown_values = [item.value or "" for item in at.markdown]
    assert any("Live Execution" in value for value in markdown_values)
    assert any("Stock Wiki Cards" in value for value in markdown_values)
    assert any("Relationship" in value for value in markdown_values)


def test_stock_wiki_masks_failed_card_and_hides_none_metrics(tmp_path: Path) -> None:
    payload = {
        "card": {
            "data": {
                "question": "宁德时代怎么看",
                "summary": {
                    "summary": "核心行情暂不可达",
                    "metrics": {"price_last": None, "pe_ttm": 25.82},
                    "metrics_missing": ["price_last", "ret_1d"],
                },
                "entity_info": {"summary": "动力电池龙头", "company_name": "宁德时代", "symbol": "300750"},
                "timeline": {"summary": "价格序列失败", "events": []},
                "watch_calendar": {"summary": "暂无节点", "items": []},
                "relationship": {"summary": "上下游集中", "pending": False, "nodes": [{"id": "宁德时代"}], "edges": []},
                "skills": {
                    "summary": {"skill": "summary", "status": "error", "latency_ms": 10, "data": {"summary": "核心行情暂不可达", "metrics": {"price_last": None, "pe_ttm": 25.82}, "metrics_missing": ["price_last", "ret_1d"]}, "sources": [], "error": "price_fetch_failed", "data_ready": False, "is_critical": True},
                    "entity_info": {"skill": "entity_info", "status": "valid", "latency_ms": 10, "data": {"summary": "动力电池龙头", "company_name": "宁德时代", "symbol": "300750"}, "sources": [], "error": None, "data_ready": True, "is_critical": False},
                    "timeline": {"skill": "timeline", "status": "valid", "latency_ms": 10, "data": {"summary": "价格序列失败", "events": []}, "sources": [], "error": None, "data_ready": True, "is_critical": True},
                    "watch_calendar": {"skill": "watch_calendar", "status": "valid", "latency_ms": 10, "data": {"summary": "暂无节点", "items": []}, "sources": [], "error": None, "data_ready": True, "is_critical": False},
                    "relationship": {"skill": "relationship", "status": "valid", "latency_ms": 10, "data": {"summary": "上下游集中", "pending": False, "nodes": [{"id": "宁德时代"}], "edges": []}, "sources": [], "error": None, "data_ready": True, "is_critical": False},
                },
            },
            "metadata": {
                "trace_id": "trace_ui_mask",
                "symbol": "300750",
                "page_status": "partial",
                "critical_failures": ["summary"],
                "failure_mask": {"summary": "price_fetch_failed"},
                "relationship_pending": False,
                "partial_release": False,
                "degrade_reason": None,
                "completed_skills": ["entity_info", "timeline", "watch_calendar", "relationship"],
                "failed_skills": ["summary"],
                "pending_skills": [],
            },
            "quality_status": "degraded",
            "sources": [],
        },
        "trace": {"route": {}, "skill_results": {}},
        "local_context": {},
    }
    wrapper = _write_wrapper(tmp_path, payload)
    at = AppTest.from_file(wrapper)
    at.run()
    at.text_area[0].set_value("宁德时代怎么看")
    at.button[0].click().run()
    markdown_values = [item.value or "" for item in at.markdown]
    assert any("Stock Summary" in value for value in markdown_values)
    assert any("price_fetch_failed" in value for value in markdown_values)
    assert not any("price_last: None" in value for value in markdown_values)


def test_timeline_figure_contains_event_markers_and_annotations() -> None:
    figure = _timeline_figure(
        series=[
            {"date": "2026-03-01", "close": 100.0},
            {"date": "2026-03-05", "close": 108.0},
            {"date": "2026-03-08", "close": 106.0},
            {"date": "2026-03-10", "close": 103.0},
            {"date": "2026-03-12", "close": 109.0},
        ],
        events=[
            {"date": "2026-03-05", "title": "发布年报并上调指引"},
            {"date": "2026-03-08", "title": "公布新品进展"},
            {"date": "2026-03-10", "title": "签订大单"},
            {"date": "2026-03-12", "title": "股东大会通知"},
        ],
    )
    assert len(figure.data) == 2
    assert list(figure.data[1].x) == ["2026-03-05", "2026-03-08", "2026-03-10", "2026-03-12"]
    assert len(figure.layout.annotations) == 0
