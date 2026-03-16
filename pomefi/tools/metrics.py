from __future__ import annotations

# 这里定义 akshare_tool 的能力边界。
# metrics 白名单是为了限制模型乱造指标，不只是方便枚举。

AKSHARE_METRICS = [
    "price_last",
    "ret_1d",
    "ret_5d",
    "ret_20d",
    "vol_20d",
    "max_drawdown_1y",
    "pe_ttm",
    "pb",
    "ps_ttm",
    "pe_quantile_5y",
    "pb_quantile_5y",
    "revenue_yoy",
    "profit_yoy",
]

AKSHARE_RATE_METRICS = {
    "ret_1d",
    "ret_5d",
    "ret_20d",
    "vol_20d",
    "max_drawdown_1y",
    "pe_quantile_5y",
    "pb_quantile_5y",
    "revenue_yoy",
    "profit_yoy",
}


def get_akshare_tool_schema() -> dict[str, object]:
    # 这个 schema 是给模型看的能力面。
    # 改这里等于改模型可调用边界。
    return {
        "type": "function",
        "function": {
            "name": "akshare_tool",
            "description": (
                "金融信息抓取查询工具。用于获取 A 股标的的最新行情、估值分位数、波动率及财务增速。"
                "涉及实时价格、PE/PB/PS 估值、风险回撤或财务增速时必须调用此工具。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "A 股标的代码，例如 600519 或 300750。",
                    },
                    "metrics": {
                        "type": "array",
                        "description": "指标白名单，禁止生成未声明指标。",
                        "items": {
                            "type": "string",
                            "enum": list(AKSHARE_METRICS),
                        },
                        "minItems": 1,
                    },
                },
                "required": ["symbol", "metrics"],
            },
        },
    }
