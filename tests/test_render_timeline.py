from __future__ import annotations

import importlib
import sys
import types


fake_streamlit = types.SimpleNamespace()
sys.modules.setdefault("streamlit", fake_streamlit)

render = importlib.import_module("pomefi.ui.render")
_timeline_event_html = render._timeline_event_html
_timeline_event_label = render._timeline_event_label
_timeline_figure = render._timeline_figure


def test_timeline_event_label_compacts_long_text() -> None:
    assert _timeline_event_label("签订大单") == "签订大单"
    assert _timeline_event_label("这是一个很长很长很长很长很长很长的标题需要被压缩用于图内标注").endswith("...")


def test_timeline_event_html_renders_dates_and_titles() -> None:
    html = _timeline_event_html(
        [
            {"event_date": "2026-03-05", "title": "发布年报"},
            {"date": "2026-03-10", "title": "签订大单"},
        ]
    )
    assert "2026-03-05" in html
    assert "发布年报" in html
    assert "签订大单" in html


def test_timeline_figure_contains_event_markers_and_annotations() -> None:
    figure = _timeline_figure(
        series=[
            {"date": "2026-03-01", "close": 100.0},
            {"date": "2026-03-05", "close": 108.0},
            {"date": "2026-03-10", "close": 103.0},
        ],
        events=[
            {"date": "2026-03-05", "title": "发布年报并上调指引"},
            {"date": "2026-03-10", "title": "签订大单"},
        ],
    )
    assert len(figure.data) == 2
    assert list(figure.data[1].x) == ["2026-03-05", "2026-03-10"]
    assert len(figure.layout.annotations) == 2


def test_timeline_figure_caps_visible_annotations_for_mobile_density() -> None:
    figure = _timeline_figure(
        series=[
            {"date": "2026-03-01", "close": 100.0},
            {"date": "2026-03-05", "close": 108.0},
            {"date": "2026-03-10", "close": 103.0},
            {"date": "2026-03-15", "close": 110.0},
        ],
        events=[
            {"date": "2026-03-01", "title": "事件一"},
            {"date": "2026-03-05", "title": "事件二"},
            {"date": "2026-03-10", "title": "事件三"},
        ],
    )
    assert len(figure.layout.annotations) == 2
