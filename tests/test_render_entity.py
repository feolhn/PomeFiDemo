from __future__ import annotations

import importlib
import sys
import types


class _FakeStreamlit:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def markdown(self, content: str, unsafe_allow_html: bool = False) -> None:
        self.calls.append(content)


fake_streamlit = _FakeStreamlit()
sys.modules["streamlit"] = fake_streamlit  # Force replace

render = importlib.import_module("pomefi.ui.render")
render_module = render  # Save for reload in tests


def test_render_entity_info_card_hides_company_and_symbol_but_shows_tags() -> None:
    # Re-import render module to pick up the current fake_streamlit
    import importlib
    render = importlib.reload(render_module)
    fake_streamlit.calls.clear()
    render.render_entity_info_card(
        {
            "state": "valid",
            "result": {
                "data": {
                    "company_name": "隆基绿能",
                    "symbol": "601012",
                    "summary": "内部画像摘要",
                    "investment_tags": ["上证50", "北向重仓", "BC电池"],
                }
            },
        },
        "隆基绿能",
        "601012",
    )
    html = "\n".join(fake_streamlit.calls)
    assert "公司:" not in html
    assert "代码:" not in html
    assert "上证50" in html
    assert "北向重仓" in html
    assert "BC电池" in html
