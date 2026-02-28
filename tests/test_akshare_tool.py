from __future__ import annotations

import math

import pandas as pd
import pytest

from pomefi.tools import execute_akshare_tool
from pomefi.tools import akshare_tool as akshare_tool_module


def _mock_info_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"item": "股票简称", "value": "宁德时代"},
            {"item": "行业", "value": "电池"},
            {"item": "上市时间", "value": "20180611"},
        ]
    )


def _mock_price_df() -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    closes = [10.0, 10.2, 10.5, 10.8, 12.0, 12.5, 13.0, 13.5, 14.0, 15.0]
    return pd.DataFrame(
        {
            "日期": dates,
            "开盘": closes,
            "收盘": closes,
            "最高": [value + 0.3 for value in closes],
            "最低": [value - 0.3 for value in closes],
            "成交量": [1000 + index * 10 for index in range(len(closes))],
            "成交额": [10000 + index * 100 for index in range(len(closes))],
        }
    )


def _mock_pe_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2024-12-31", "2025-12-31", "2026-02-27"],
            "value": [12.0, 15.0, 18.2],
        }
    )


def _mock_pb_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2024-12-31", "2025-12-31", "2026-02-27"],
            "value": [2.0, 2.6, 3.1],
        }
    )


def _mock_spot_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"item": "市销率", "value": "4.4"},
            {"item": "市盈率(TTM)", "value": "18.2"},
        ]
    )


def _mock_financial_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "日期": ["2025-12-31"],
            "营业总收入同比增长率(%)": [12.0],
            "净利润同比增长率(%)": [8.0],
        }
    )


def _patch_akshare(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_info_em", lambda symbol: _mock_info_df())
    monkeypatch.setattr(akshare_tool_module.ak, "stock_zh_a_hist", lambda **kwargs: _mock_price_df())
    monkeypatch.setattr(
        akshare_tool_module.ak,
        "stock_zh_valuation_baidu",
        lambda symbol, indicator, period: _mock_pe_df() if indicator == "市盈率(TTM)" else _mock_pb_df(),
    )
    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_spot_xq", lambda symbol: _mock_spot_df())
    monkeypatch.setattr(akshare_tool_module.ak, "stock_financial_analysis_indicator", lambda symbol, start_year: _mock_financial_df())


def test_execute_requires_symbol() -> None:
    with pytest.raises(RuntimeError, match="non-empty symbol"):
        execute_akshare_tool({"symbol": "", "metrics": ["price_last"]})


def test_execute_requires_metrics() -> None:
    with pytest.raises(RuntimeError, match="at least one metric"):
        execute_akshare_tool({"symbol": "300750", "metrics": []})


def test_execute_rejects_unsupported_metrics() -> None:
    with pytest.raises(RuntimeError, match="Unsupported metrics"):
        execute_akshare_tool({"symbol": "300750", "metrics": ["unknown_metric"]})


def test_execute_returns_wrapped_local_tool_result(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_akshare(monkeypatch)

    result = execute_akshare_tool(
        {
            "symbol": "300750",
            "metrics": ["price_last", "ret_5d", "pe_ttm", "pb", "ps_ttm", "revenue_yoy", "profit_yoy"],
        }
    )

    metrics_data = result["tool_content"]["metrics_data"]
    local_context = result["local_context"]
    metrics = metrics_data["metrics"]

    assert result["__pomefi_local_tool_result__"] is True
    assert metrics_data["symbol"] == "300750"
    assert metrics_data["resolved_name"] == "宁德时代"
    assert local_context["chart_index"][0]["chart_id"] == "price_1y_line"
    assert "raw_bundle" in local_context
    assert math.isclose(metrics["price_last"], 15.0)
    assert math.isclose(metrics["ret_5d"], 0.25)
    assert math.isclose(metrics["pe_ttm"], 18.2)
    assert math.isclose(metrics["pb"], 3.1)
    assert math.isclose(metrics["ps_ttm"], 4.4)
    assert math.isclose(metrics["revenue_yoy"], 0.12)
    assert math.isclose(metrics["profit_yoy"], 0.08)


def test_execute_sets_none_and_notes_for_missing_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_info_em", lambda symbol: _mock_info_df())
    monkeypatch.setattr(akshare_tool_module.ak, "stock_zh_a_hist", lambda **kwargs: _mock_price_df())
    monkeypatch.setattr(
        akshare_tool_module.ak,
        "stock_zh_valuation_baidu",
        lambda symbol, indicator, period: pd.DataFrame(columns=["date", "value"]),
    )
    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_spot_xq", lambda symbol: pd.DataFrame(columns=["item", "value"]))
    monkeypatch.setattr(
        akshare_tool_module.ak,
        "stock_financial_analysis_indicator",
        lambda symbol, start_year: pd.DataFrame({"日期": ["2025-12-31"]}),
    )

    result = execute_akshare_tool({"symbol": "300750", "metrics": ["ps_ttm", "revenue_yoy", "profit_yoy"]})
    metrics_data = result["tool_content"]["metrics_data"]

    assert metrics_data["metrics"]["ps_ttm"] is None
    assert metrics_data["metrics"]["revenue_yoy"] is None
    assert metrics_data["metrics"]["profit_yoy"] is None
    assert any("revenue_yoy" in note for note in metrics_data["notes"])
    assert any("profit_yoy" in note for note in metrics_data["notes"])
