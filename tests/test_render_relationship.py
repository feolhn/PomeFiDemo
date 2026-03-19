from __future__ import annotations

import importlib
import sys
import types


fake_streamlit = types.SimpleNamespace()
sys.modules.setdefault("streamlit", fake_streamlit)

render = importlib.import_module("pomefi.ui.render")
_relationship_layout = render._relationship_layout
_relationship_figure = render._relationship_figure


def test_relationship_layout_places_theme_at_center() -> None:
    positions = _relationship_layout(
        [
            {"id": "宁德时代", "role": "theme"},
            {"id": "天赐材料", "role": "supplier"},
            {"id": "特斯拉", "role": "customer"},
            {"id": "LG新能源", "role": "competitor"},
        ]
    )
    assert positions["宁德时代"] == (0.0, 0.0)
    assert positions["天赐材料"][0] < 0
    assert positions["特斯拉"][0] > 0


def test_relationship_figure_contains_edges_and_nodes() -> None:
    figure = _relationship_figure(
        nodes=[
            {"id": "宁德时代", "role": "theme"},
            {"id": "天赐材料", "role": "supplier"},
            {"id": "特斯拉", "role": "customer"},
        ],
        edges=[
            {"from": "天赐材料", "to": "宁德时代", "relation": "supplies"},
            {"from": "宁德时代", "to": "特斯拉", "relation": "supplies"},
        ],
    )
    assert len(figure.data) >= 4
    assert any(getattr(trace, "mode", "") == "lines" for trace in figure.data)
    assert any("markers+text" == getattr(trace, "mode", "") for trace in figure.data)
