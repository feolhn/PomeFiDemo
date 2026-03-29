from __future__ import annotations

import asyncio

from pomefi.stock_wiki.skills import stock_summary


def test_get_stock_summary_from_akshare_tool(monkeypatch) -> None:
    def _fake_execute(arguments):
        assert arguments["symbol"] == "300750"
        assert arguments["include_financial_series_5y"] is True
        return {
            "__pomefi_local_tool_result__": True,
            "tool_content": {
                "metrics_data": {
                    "asof": "2026-03-15",
                    "resolved_name": "宁德时代",
                    "metrics": {"price_last": 201.5, "ret_5d": 0.03},
                    "financial_series_5y": [
                        {"report_date": "20211231", "year": "2021", "revenue": 10.0, "net_profit": 1.0},
                        {"report_date": "20221231", "year": "2022", "revenue": 11.0, "net_profit": 1.2},
                    ],
                    "notes": ["ok"],
                }
            },
        }

    monkeypatch.setattr(stock_summary, "execute_akshare_tool", _fake_execute)
    result = asyncio.run(stock_summary.get_stock_summary("300750", "宁德时代"))

    assert result["status"] == "valid"
    assert result["data"]["metrics"]["price_last"] == 201.5
    assert len(result["data"]["financial_series_5y"]) == 2
    assert result["data"]["financial_series_5y"][0]["year"] == "2021"
    assert result["sources"][0]["source"] == "AkShare"
