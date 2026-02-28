from __future__ import annotations

from pomefi.tools.hooks import build_chart_index, build_hook_payload, to_local_tool_result


def test_build_hook_payload_keeps_three_layers() -> None:
    payload = build_hook_payload(
        symbol="300750",
        resolved_name="宁德时代",
        asof="2026-02-27",
        metrics={"price_last": 201.5},
        notes=["ok"],
        raw_bundle={
            "price_history_1y": [{"date": "2026-02-27", "close": 201.5}],
            "valuation_5y": [{"date": "2026-02-27", "pe_ttm": 18.2, "pb": 3.1}],
        },
    )

    assert set(payload.keys()) == {"metrics_data", "chart_index", "raw_bundle"}
    assert payload["metrics_data"]["symbol"] == "300750"
    assert len(payload["chart_index"]) == 2


def test_to_local_tool_result_only_exposes_metrics_data_to_llm() -> None:
    payload = build_hook_payload(
        symbol="300750",
        resolved_name="宁德时代",
        asof="2026-02-27",
        metrics={"price_last": 201.5},
        notes=[],
        raw_bundle={
            "price_history_1y": [{"date": "2026-02-27", "close": 201.5}],
            "valuation_5y": [],
        },
    )

    result = to_local_tool_result(payload)

    assert result["__pomefi_local_tool_result__"] is True
    assert set(result["tool_content"].keys()) == {"metrics_data"}
    assert "chart_index" not in result["tool_content"]
    assert "raw_bundle" not in result["tool_content"]
    assert set(result["local_context"].keys()) == {"metrics_data", "chart_index", "raw_bundle"}


def test_build_chart_index_generates_expected_refs() -> None:
    chart_index = build_chart_index(
        {
            "price_history_1y": [{"date": "2026-02-27", "close": 201.5}],
            "valuation_5y": [{"date": "2026-02-27", "pe_ttm": 18.2, "pb": 3.1}],
        }
    )

    assert chart_index[0]["chart_id"] == "price_1y_line"
    assert chart_index[0]["data_ref"] == "local://raw_bundle/price_history_1y"
    assert chart_index[1]["chart_id"] == "valuation_5y_line"
    assert chart_index[1]["data_ref"] == "local://raw_bundle/valuation_5y"
