from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_wrapper(tmp_path: Path) -> Path:
    wrapper = tmp_path / "app_progressive_wrapper.py"
    wrapper.write_text(
        (
            "import sys\n"
            "from pathlib import Path\n\n"
            f"repo_root = Path(r\"{REPO_ROOT}\")\n"
            "if str(repo_root) not in sys.path:\n"
            "    sys.path.insert(0, str(repo_root))\n\n"
            "import app\n\n"
            "app._validate_app_config = lambda: (True, '')\n"
            "def _fake_run(question, on_event=None):\n"
            "    if on_event is not None:\n"
            "        on_event({'type': 'route_resolved', 'route': {'symbol': '300750', 'company_name': '宁德时代'}})\n"
            "        on_event({'type': 'skill_start', 'skill': 'summary'})\n"
            "        on_event({'type': 'skill_result_ready', 'skill': 'summary', 'result': {'skill': 'summary', 'status': 'valid', 'latency_ms': 12, 'data': {'summary': '价格稳中有升', 'metrics': {'price_last': 201.5}}, 'sources': [], 'error': None, 'error_category': None, 'data_ready': True, 'is_critical': False}})\n"
            "        on_event({'type': 'skill_start', 'skill': 'timeline'})\n"
            "    return {'card': {'data': {'question': question, 'summary': {'summary': '价格稳中有升', 'metrics': {'price_last': 201.5}}, 'entity_info': {'summary': '动力电池龙头'}, 'timeline': {'summary': '时间线仍在生成中', 'series': [], 'events': []}, 'watch_calendar': {'summary': '等待中', 'items': []}, 'relationship': {'summary': '等待中', 'pending': True, 'nodes': [], 'edges': []}, 'skills': {'summary': {'skill': 'summary', 'status': 'valid', 'latency_ms': 12, 'data': {'summary': '价格稳中有升', 'metrics': {'price_last': 201.5}}, 'sources': [], 'error': None, 'error_category': None, 'data_ready': True, 'is_critical': False}, 'entity_info': {'skill': 'entity_info', 'status': 'error', 'latency_ms': 0, 'data': {'summary': '等待中'}, 'sources': [], 'error': 'not_started', 'error_category': 'pending', 'data_ready': False, 'is_critical': False}, 'timeline': {'skill': 'timeline', 'status': 'error', 'latency_ms': 0, 'data': {'summary': '时间线仍在生成中', 'series': [], 'events': []}, 'sources': [], 'error': 'not_started', 'error_category': 'pending', 'data_ready': False, 'is_critical': True}, 'watch_calendar': {'skill': 'watch_calendar', 'status': 'error', 'latency_ms': 0, 'data': {'summary': '等待中', 'items': []}, 'sources': [], 'error': 'not_started', 'error_category': 'pending', 'data_ready': False, 'is_critical': False}, 'relationship': {'skill': 'relationship', 'status': 'error', 'latency_ms': 0, 'data': {'summary': '等待中', 'pending': True, 'nodes': [], 'edges': []}, 'sources': [], 'error': 'not_started', 'error_category': 'pending', 'data_ready': False, 'is_critical': False}}}, 'metadata': {'trace_id': 'trace_progressive', 'symbol': '300750', 'company_name': '宁德时代', 'page_status': 'partial', 'completed_skills': ['summary'], 'failed_skills': [], 'pending_skills': ['timeline', 'entity_info', 'watch_calendar', 'relationship']}, 'quality_status': 'degraded', 'sources': []}, 'trace': {'route': {'symbol': '300750', 'company_name': '宁德时代'}, 'skill_results': {}}, 'local_context': {}}\n"
            "app.run_analysis_stream = _fake_run\n"
            "app.main()\n"
        ),
        encoding="utf-8",
    )
    return wrapper


def test_app_renders_progressive_cards(tmp_path: Path) -> None:
    wrapper = _write_wrapper(tmp_path)
    at = AppTest.from_file(wrapper)
    at.run()
    at.text_area[0].set_value("宁德时代怎么看")
    at.button[0].click().run()

    markdown_values = [item.value or "" for item in at.markdown]
    assert any("Stock Summary" in value for value in markdown_values)
    assert any("201.50" in value for value in markdown_values)
    assert any("Event Timeline: Price vs Key Dates" in value for value in markdown_values)
    assert any("卡片正在生成中" in value for value in markdown_values)


def test_app_reads_local_fixture_dir(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_payloads = {
        "summary": {"skill": "summary", "status": "valid", "data": {"symbol": "300750", "company_name": "宁德时代", "summary": "价格稳中有升", "metrics": {"price_last": 201.5}}, "sources": [], "error": None, "data_ready": True, "is_critical": False},
        "entity_info": {"skill": "entity_info", "status": "valid", "data": {"symbol": "300750", "company_name": "宁德时代", "summary": "动力电池龙头"}, "sources": [], "error": None, "data_ready": True, "is_critical": False},
        "timeline": {"skill": "timeline", "status": "valid", "data": {"symbol": "300750", "company_name": "宁德时代", "summary": "近三个月价格序列", "series": [{"date": "2026-03-01", "close": 1.0}], "events": []}, "sources": [], "error": None, "data_ready": True, "is_critical": True},
        "watch_calendar": {"skill": "watch_calendar", "status": "error", "data": {"symbol": "300750", "company_name": "宁德时代", "summary": "当前卡片执行失败。", "items": []}, "sources": [], "error": "calendar_failed", "data_ready": False, "is_critical": False},
        "relationship": {"skill": "relationship", "status": "valid", "data": {"symbol": "300750", "company_name": "宁德时代", "summary": "上下游集中", "pending": False, "nodes": [{"id": "宁德时代"}], "edges": []}, "sources": [], "error": None, "data_ready": True, "is_critical": False},
    }
    for name, result in fixture_payloads.items():
        (fixture_dir / f"{name}.json").write_text(
            json.dumps({"skill": name, "symbol": "300750", "company_name": "宁德时代", "result": result, "trace": {"events": []}}, ensure_ascii=False),
            encoding="utf-8",
        )

    wrapper = tmp_path / "app_fixture_wrapper.py"
    wrapper.write_text(
        (
            "import os\n"
            "import sys\n"
            "from pathlib import Path\n\n"
            f"repo_root = Path(r\"{REPO_ROOT}\")\n"
            "if str(repo_root) not in sys.path:\n"
            "    sys.path.insert(0, str(repo_root))\n\n"
            f"os.environ['POMEFI_LOCAL_FIXTURE_DIR'] = r'{fixture_dir}'\n"
            "import app\n"
            "app.main()\n"
        ),
        encoding="utf-8",
    )
    at = AppTest.from_file(wrapper)
    at.run()
    at.text_area[0].set_value("宁德时代怎么看")
    at.button[0].click().run()
    markdown_values = [item.value or "" for item in at.markdown]
    assert any("Stock Summary" in value for value in markdown_values)
    assert any("201.50" in value for value in markdown_values)
    assert any("calendar_failed" in value for value in markdown_values)
