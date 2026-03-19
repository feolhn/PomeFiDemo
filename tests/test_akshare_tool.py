from __future__ import annotations

import asyncio
import math
import time
from typing import Any

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
    assert metrics_data["data_origin"] == "live"
    assert metrics_data["network_evidence"] == []


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


def test_execute_supports_nested_spot_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_info_em", lambda symbol: _mock_info_df())
    monkeypatch.setattr(akshare_tool_module.ak, "stock_zh_a_hist", lambda **kwargs: _mock_price_df())
    monkeypatch.setattr(
        akshare_tool_module.ak,
        "stock_zh_valuation_baidu",
        lambda symbol, indicator, period: _mock_pe_df() if indicator == "市盈率(TTM)" else _mock_pb_df(),
    )
    monkeypatch.setattr(
        akshare_tool_module.ak,
        "stock_individual_spot_xq",
        lambda symbol: pd.DataFrame(
            [{"data": {"quote": {"现价": "100.50", "昨收": "99.00", "市销率": "3.8"}}}]
        ),
    )
    monkeypatch.setattr(akshare_tool_module.ak, "stock_financial_analysis_indicator", lambda symbol, start_year: _mock_financial_df())

    result = execute_akshare_tool({"symbol": "300750", "metrics": ["price_last", "ret_1d", "ps_ttm"]})
    metrics = result["tool_content"]["metrics_data"]["metrics"]
    assert math.isclose(metrics["price_last"], 15.0)
    assert metrics["ret_1d"] is not None
    assert math.isclose(metrics["ps_ttm"], 3.8)


def test_execute_fallback_price_from_spot_when_history_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    akshare_tool_module._PRICE_HISTORY_CACHE.clear()
    def _info_should_not_run(symbol):
        raise RuntimeError("stock_individual_info_em should not be called for price fallback")

    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_info_em", _info_should_not_run)

    def _raise_hist(**kwargs):
        raise RuntimeError("hist offline")

    monkeypatch.setattr(akshare_tool_module.ak, "stock_zh_a_hist", _raise_hist)
    monkeypatch.setattr(
        akshare_tool_module.ak,
        "stock_zh_valuation_baidu",
        lambda symbol, indicator, period: pd.DataFrame(columns=["date", "value"]),
    )
    monkeypatch.setattr(
        akshare_tool_module.ak,
        "stock_individual_spot_xq",
        lambda symbol: pd.DataFrame(
            [
                {"item": "现价", "value": "101.2"},
                {"item": "昨收", "value": "100.0"},
            ]
        ),
    )
    monkeypatch.setattr(akshare_tool_module.ak, "stock_financial_analysis_indicator", lambda symbol, start_year: pd.DataFrame())

    result = execute_akshare_tool({"symbol": "300750", "metrics": ["price_last", "ret_1d"]})
    metrics_data = result["tool_content"]["metrics_data"]
    metrics = metrics_data["metrics"]
    assert math.isclose(metrics["price_last"], 101.2)
    assert math.isclose(metrics["ret_1d"], 0.012)
    assert metrics_data["data_origin"] == "partial"
    assert any(item.get("interface") in {"stock_zh_a_hist", "stock_zh_a_hist_tx"} for item in metrics_data["network_evidence"])
    assert any("stock_zh_a_hist failed" in note for note in metrics_data["notes"])
    assert any(call.get("interface") == "stock_zh_a_hist" for call in metrics_data.get("akshare_calls", []))
    assert not any(call.get("interface") == "stock_individual_info_em" for call in metrics_data.get("akshare_calls", []))


def test_execute_uses_cache_fallback_when_live_history_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    akshare_tool_module._PRICE_HISTORY_CACHE.clear()
    akshare_tool_module._PRICE_HISTORY_CACHE[("300750", "20240101", "20240131")] = _mock_price_df().copy()
    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_info_em", lambda symbol: _mock_info_df())
    monkeypatch.setattr(akshare_tool_module.ak, "stock_zh_a_hist", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("proxy timeout")))
    monkeypatch.setattr(
        akshare_tool_module.ak,
        "stock_zh_valuation_baidu",
        lambda symbol, indicator, period: pd.DataFrame(columns=["date", "value"]),
    )
    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_spot_xq", lambda symbol: pd.DataFrame(columns=["item", "value"]))
    monkeypatch.setattr(akshare_tool_module.ak, "stock_financial_analysis_indicator", lambda symbol, start_year: pd.DataFrame())

    result = execute_akshare_tool({"symbol": "300750", "metrics": ["price_last", "ret_1d", "ret_5d"]})
    metrics_data = result["tool_content"]["metrics_data"]
    metrics = metrics_data["metrics"]
    assert metrics["price_last"] is not None
    assert metrics_data["data_origin"] == "cache_fallback"
    assert any(item.get("status") == "cache_fallback" for item in metrics_data["network_evidence"])


def test_execute_falls_back_to_tx_history_when_eastmoney_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    akshare_tool_module._PRICE_HISTORY_CACHE.clear()
    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_info_em", lambda symbol: _mock_info_df())
    monkeypatch.setattr(
        akshare_tool_module.ak,
        "stock_zh_a_hist",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("ProxyError: eastmoney offline")),
    )
    monkeypatch.setattr(akshare_tool_module.ak, "stock_zh_a_hist_tx", lambda **kwargs: _mock_price_df())
    monkeypatch.setattr(
        akshare_tool_module.ak,
        "stock_zh_valuation_baidu",
        lambda symbol, indicator, period: pd.DataFrame(columns=["date", "value"]),
    )
    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_spot_xq", lambda symbol: pd.DataFrame(columns=["item", "value"]))
    monkeypatch.setattr(akshare_tool_module.ak, "stock_financial_analysis_indicator", lambda symbol, start_year: pd.DataFrame())

    result = execute_akshare_tool({"symbol": "300750", "metrics": ["price_last", "ret_1d", "ret_5d"]})
    metrics_data = result["tool_content"]["metrics_data"]
    metrics = metrics_data["metrics"]

    assert metrics["price_last"] is not None
    assert metrics["ret_1d"] is not None
    assert metrics["ret_5d"] is not None
    assert metrics_data["data_origin"] == "live"
    assert any(item.get("interface") == "stock_zh_a_hist_tx" and item.get("status") == "ok" for item in metrics_data["akshare_calls"])


def test_execute_does_not_call_spot_when_not_needed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_info_em", lambda symbol: _mock_info_df())
    monkeypatch.setattr(akshare_tool_module.ak, "stock_zh_a_hist", lambda **kwargs: _mock_price_df())
    monkeypatch.setattr(
        akshare_tool_module.ak,
        "stock_zh_valuation_baidu",
        lambda symbol, indicator, period: _mock_pe_df() if indicator == "市盈率(TTM)" else _mock_pb_df(),
    )

    def _spot_should_not_run(symbol):
        raise RuntimeError("spot should not be called")

    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_spot_xq", _spot_should_not_run)
    monkeypatch.setattr(akshare_tool_module.ak, "stock_financial_analysis_indicator", lambda symbol, start_year: _mock_financial_df())

    result = execute_akshare_tool({"symbol": "300750", "metrics": ["price_last", "ret_1d", "ret_5d", "pe_ttm", "pb"]})
    metrics = result["tool_content"]["metrics_data"]["metrics"]
    assert metrics["price_last"] is not None
    assert metrics["ret_1d"] is not None
    assert metrics["pe_ttm"] is not None


def test_execute_lazy_load_skips_unneeded_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(akshare_tool_module.ak, "stock_zh_a_hist", lambda **kwargs: _mock_price_df())

    def _unexpected_info(symbol):
        raise RuntimeError("stock_individual_info_em should not be called")

    def _unexpected_financial(symbol, start_year):
        raise RuntimeError("stock_financial_analysis_indicator should not be called")

    def _unexpected_valuation(symbol, indicator, period):
        raise RuntimeError("stock_zh_valuation_baidu should not be called")

    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_info_em", _unexpected_info)
    monkeypatch.setattr(akshare_tool_module.ak, "stock_financial_analysis_indicator", _unexpected_financial)
    monkeypatch.setattr(akshare_tool_module.ak, "stock_zh_valuation_baidu", _unexpected_valuation)
    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_spot_xq", lambda symbol: pd.DataFrame(columns=["item", "value"]))

    result = execute_akshare_tool({"symbol": "300750", "metrics": ["price_last", "ret_1d", "ret_5d"]})
    metrics = result["tool_content"]["metrics_data"]["metrics"]
    assert metrics["price_last"] is not None
    assert metrics["ret_1d"] is not None
    assert metrics["ret_5d"] is not None
    interfaces = [item.get("interface") for item in result["tool_content"]["metrics_data"]["akshare_calls"]]
    assert interfaces.count("stock_zh_a_hist") >= 1
    assert "stock_individual_info_em" not in interfaces
    assert "stock_financial_analysis_indicator" not in interfaces
    assert "stock_zh_valuation_baidu" not in interfaces


def test_get_cached_price_history_singleflight_dedup(monkeypatch: pytest.MonkeyPatch) -> None:
    akshare_tool_module._PRICE_HISTORY_CACHE.clear()
    akshare_tool_module._PRICE_HISTORY_INFLIGHT.clear()
    call_count = {"n": 0}

    def _slow_hist(**kwargs):
        _ = kwargs
        call_count["n"] += 1
        time.sleep(0.2)
        return _mock_price_df()

    monkeypatch.setattr(akshare_tool_module.ak, "stock_zh_a_hist", _slow_hist)

    async def _run() -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]]]:
        logs1: list[dict[str, Any]] = []
        logs2: list[dict[str, Any]] = []
        result1, result2 = await asyncio.gather(
            asyncio.to_thread(akshare_tool_module.get_cached_price_history, "300750", call_logs=logs1),
            asyncio.to_thread(akshare_tool_module.get_cached_price_history, "300750", call_logs=logs2),
        )
        return result1, result2, logs1, logs2

    hist1, hist2, logs1, logs2 = asyncio.run(_run())
    assert call_count["n"] == 1
    assert not hist1.empty and not hist2.empty
    all_logs = [item for item in logs1 + logs2 if item.get("interface") == "stock_zh_a_hist"]
    remote_hits = [item for item in all_logs if not bool(item.get("dedup_hit")) and item.get("status") == "ok"]
    dedup_hits = [item for item in all_logs if bool(item.get("dedup_hit")) and item.get("status") == "ok"]
    assert len(remote_hits) == 1
    assert len(dedup_hits) >= 1


def test_get_cached_price_history_retries_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    akshare_tool_module._PRICE_HISTORY_CACHE.clear()
    akshare_tool_module._PRICE_HISTORY_INFLIGHT.clear()
    call_count = {"n": 0}

    def _flaky_hist(**kwargs):
        _ = kwargs
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("ProxyError('Unable to connect to proxy')")
        return _mock_price_df()

    monkeypatch.setattr(akshare_tool_module.ak, "stock_zh_a_hist", _flaky_hist)
    logs: list[dict[str, Any]] = []
    history_df = akshare_tool_module.get_cached_price_history("300750", call_logs=logs)
    assert call_count["n"] == 2
    assert not history_df.empty
    assert any(item.get("status") == "error" and int(item.get("retry_count") or 0) == 0 for item in logs)
    assert any(item.get("status") == "ok" and int(item.get("retry_count") or 0) == 1 for item in logs)


def test_stock_profile_schema_fallback_for_non_item_value_columns(monkeypatch: pytest.MonkeyPatch) -> None:
    akshare_tool_module._PRICE_HISTORY_CACHE.clear()
    monkeypatch.setattr(
        akshare_tool_module.ak,
        "stock_individual_info_em",
        lambda symbol: pd.DataFrame(
            [
                {"项目": "股票简称", "值": "宁德时代"},
                {"项目": "行业", "值": "电池"},
                {"项目": "最新价", "值": "409.8"},
            ]
        ),
    )
    monkeypatch.setattr(akshare_tool_module.ak, "stock_zh_a_hist", lambda **kwargs: pd.DataFrame())
    monkeypatch.setattr(
        akshare_tool_module.ak,
        "stock_zh_valuation_baidu",
        lambda symbol, indicator, period: pd.DataFrame(columns=["date", "value"]),
    )
    monkeypatch.setattr(akshare_tool_module.ak, "stock_individual_spot_xq", lambda symbol: pd.DataFrame(columns=["item", "value"]))
    monkeypatch.setattr(akshare_tool_module.ak, "stock_financial_analysis_indicator", lambda symbol, start_year: pd.DataFrame())

    result = execute_akshare_tool({"symbol": "300750", "metrics": ["price_last", "ps_ttm"]})
    metrics_data = result["tool_content"]["metrics_data"]
    assert metrics_data["resolved_name"] == "宁德时代"
    assert math.isclose(metrics_data["metrics"]["price_last"], 409.8)
