from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

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
                "skills": {},
            },
            "metadata": {
                "trace_id": "trace_ui_mask",
                "symbol": "300750",
                "strict_fail": True,
                "critical_failures": ["summary"],
                "failure_mask": {"summary": "price_fetch_failed"},
                "relationship_pending": False,
                "partial_release": False,
                "degrade_reason": "AKSHARE_NETWORK_UNRECOVERED",
                "execution_status": "failed",
                "failure_reason_code": "AKSHARE_NETWORK_UNRECOVERED",
                "failure_reason_message": "核心行情链路未恢复",
                "failure_stage": "summary",
                "failure_evidence": {"skill": "summary", "error": "price_fetch_failed"},
                "short_circuit": True,
                "cancelled_skills": ["entity_info", "watch_calendar", "relationship"],
            },
            "quality_status": "error",
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
    assert any("Execution Failed" in value for value in markdown_values)
    assert any("AKSHARE_NETWORK_UNRECOVERED" in value for value in markdown_values)
    assert any("short_circuit" in value for value in markdown_values)
    assert any("cancelled_skills" in value for value in markdown_values)
    assert not any("price_last: None" in value for value in markdown_values)
