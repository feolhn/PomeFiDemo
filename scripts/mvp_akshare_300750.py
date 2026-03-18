from __future__ import annotations

from datetime import datetime
import json

import akshare as ak
import pandas as pd


if __name__ == "__main__":
    symbol = "300750"
    timeout = 8.0
    period = "daily"
    adjust = "qfq"
    start_date = "20250101"
    end_date = datetime.now().strftime("%Y%m%d")

    info_df = ak.stock_individual_info_em(symbol=symbol, timeout=timeout)
    assert not info_df.empty
    assert {"item", "value"}.issubset(set(info_df.columns))

    hist_df = ak.stock_zh_a_hist(
        symbol=symbol,
        period=period,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
        timeout=timeout,
    )
    assert not hist_df.empty
    assert {"日期", "收盘"}.issubset(set(hist_df.columns))

    hist_last_close = pd.to_numeric(hist_df["收盘"], errors="coerce").dropna().iloc[-1]
    asof = str(hist_df["日期"].iloc[-1])

    report = {
        "symbol": symbol,
        "info_rows": int(info_df.shape[0]),
        "info_columns": [str(col) for col in list(info_df.columns)],
        "hist_rows": int(hist_df.shape[0]),
        "hist_columns": [str(col) for col in list(hist_df.columns)],
        "hist_last_close": float(hist_last_close),
        "asof": asof,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
