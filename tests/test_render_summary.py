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


def test_format_metric_value_renders_rate_like_metrics_as_percent() -> None:
    assert render._format_metric_value(-0.009478672985781977, "ret_1d") == "-0.95%"
    assert render._format_metric_value(0.037506894649751876, "ret_20d") == "+3.75%"
    assert render._format_metric_value(0.006959314775160541, "ret_5d") == "+0.70%"
    assert render._format_metric_value(0.2018108445693922, "vol_20d") == "20.18%"
    assert render._format_metric_value(-25.84, "pe_ttm") == "亏损"


def test_summary_price_text_uses_yuan_not_dollar() -> None:
    assert render._summary_price_text(18.81) == "18.81元"


def test_summary_sections_include_ret_20d_and_avoid_duplicate_primary_metrics() -> None:
    kv_rows, bullets = render._summary_sections(
        {
            "price_last": 18.81,
            "ret_1d": -0.009478672985781977,
            "ret_5d": 0.006959314775160541,
            "ret_20d": 0.037506894649751876,
            "pe_ttm": -25.84,
            "pb": 2.5,
            "vol_20d": 0.2018108445693922,
            "max_drawdown_1y": -0.24473684210526325,
        },
        missing=[],
        error_reason="",
    )
    labels = [label for label, _ in kv_rows]
    assert "近20日" in labels
    assert "近1日" in labels
    assert "近5日" in labels
    assert "20日波动" in labels
    assert "1年回撤" in labels
    assert not any(item.startswith("近1日:") for item in bullets)
    assert not any(item.startswith("近5日:") for item in bullets)
    assert not any(item.startswith("近20日:") for item in bullets)
    assert not any(item.startswith("20日波动:") for item in bullets)
    assert not any(item.startswith("Data Origin:") for item in bullets)
