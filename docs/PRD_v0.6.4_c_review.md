# PRD_v0.6.4_c_review

> **版本定位**：金融花园理念下的 Agent 化金融信息卡片引擎  
> **架构基础**：增强型工具集（Tool Calls）+ 状态感知 Agent Loop  
> **设计核心**：全周期生态隐喻 + 数据闭环处理 + 成本/性能平衡  
> **核心目标**：用户任意输入问题 → 输出具备时间感知与深度逻辑的「金融花园卡片」

---

## 一、版本核心升级（对比 v0.6.1）

在 v0.6.0 的基础上，v0.6.2 针对“架构硬伤”和“工程不确定性”进行关键修正：

1. **架构进化**：从“无记忆切片”升级为“状态感知生态”。引入 `memory`（MVP 可选，稳定后接入）以支持连续修剪叙事。
2. **工具增强**：引入本地数据处理层（清洗/聚合/计算），避免 LLM 直接处理 DataFrame 崩溃。
3. **隐喻补完**：从“花期/修剪”扩展至“土壤、肥料、害虫、根系”的全生态维度。
4. **工程确定性**：引入 **Token/成本熔断** + **Eval Set（测试集）** + **Logging（显式日志）**，保障 JSON 稳定与可调试性。
5. **工具结构优化（新增）**：统一为单一 `akshare_tool`，通过 `metrics[]` 白名单（enum）声明能力；并通过 Hook 分层返回，禁止 raw_data 进入 LLM。

---

## 二、产品世界观：金融花园（Finance Garden）

理财不再是单次买卖，而是一个生态系统的维护：

- **果实（Yields/Metrics）**：关键指标（PE、收益率、分位数等）
- **花期走势（Flowering/Trend）**：价格与波动的时间轴表现
- **土壤（Soil/Macro）**：宏观背景、行业环境、政策基础
- **肥料（Fertilizer/Flow）**：资金流向、成交额、机构持仓变化
- **害虫（Pests/Risks）**：风险预警、负面舆情、财务造假嫌疑
- **根系（Roots/History）**：历史底蕴、长期基本面支撑
- **修剪建议（Pruning）**：基于现状的调仓/对冲动作（必须可追溯）

> **核心理念：Finance as Pruning（理财即修剪）**  
> 修剪必须基于生态数据闭环，而不是孤立数据切片。
> 理财不是靠单一数据拍脑袋做决策，而是像打理花园一样，结合标的的宏观环境、资金流向、核心指标、潜在风险、历史趋势等所有维度的完整数据，做出有依据、可追溯的动作。

---

## 三、整体架构设计

### 3.1 架构原则

- **有限工具**：工具总数建议 ≤ 5（降低 tool-call 漂移，提升可控性）
- **确定性优先**：复杂数据计算由程序执行，摘要和解释由 LLM 执行
- **强 JSON 输出**：结构稳定优先于文采；错误可回退但不能胡编
- **数据可追溯**：每一条数值必须能回溯到“工具→计算→摘要”的链路

### 3.2 逻辑链路

```text
User Input
  ↓
Router/Analyzer (LLM + Memory 可选)
  ↓
Tool Calls (akshare_tool + web_search + date? + memory?)
  ↓
Local Hook Handler (表格处理/聚合/指标计算/格式化)
  ↓
Data Arbitration (时间优先 + 来源标注)
  ↓
JSON Blocks (Garden Protocol)
  ↓
Front-end Rendering (chart_index 本地绘图，不进 LLM)
```

---

## 四、工具设计（Core Toolset）

> **目标**：让模型“更聪明地调用工具”，而不是“更努力地写字”。  
> 关键策略：**metrics[] 白名单（enum）+ Hook 分层返回 + 禁止 raw_data 进 LLM**。

### 4.1 工具清单（建议 ≤ 4）

1. `akshare_tool`（自定义Tool，核心金融数据）
2. `web_search`（官方Tool,事件/公告/宏观新闻）
3. `date`（官方Tool,可选：时间解析与对齐）
4. `memory`（官方Tool,可选：连续修剪记录）
5. `memory`（官方Tool,可选：连续修剪记录）

---

### 4.2 akshare_tool：用 metrics[] 白名单（enum）声明能力

#### 4.2.1 统一工具接口（示例）

#### 4.2.1.1 官方工具调用
使用 Kimi 官方 `Formula` 工具（内置脚本引擎集合）

写法重点：
- URI 组成：通常由三个部分组成，格式为 `namespace/name:tag`。例如：`moonshot/web-search:latest`
- 对于 `$web_search` 这种特殊内置工具，其名称通常以 `$` 为前缀

JSON 写法示例：

```json
{
  "tools": [
    {
      "type": "builtin_function",
      "function": {
        "name": "web_search" 
      },
      "builtin_function": {
        "name": "moonshot/web-search:latest"
      }
    }
  ]
}
```

#### 4.2.1.2 非官方工具/自定义工具调用
写法重点：
- 工具声明要放在 tools[] 中
- 自定义工具用 type="function"
- name/description 放在 function 下
- parameters 必须是 JSON Schema（type/object/properties/required）
- metrics 用 enum 白名单，避免模型乱造指标

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "akshare_tool",
        "description": "金融信息抓取查询工具。用于获取股票、指数、基金、商品等各类金融标的的最新行情、估值分位数、波动率及财务增速。注意：涉及实时价格、PE/PB估值、风险回撤时必须调用此工具，严禁使用联网搜索推断数值。",
        "parameters": {
          "type": "object",
          "properties": {
            "symbol": {
              "type": "string",
              "description": "标的代码，例如：600519"
            },
            "metrics": {
              "type": "array",
              "description": "指标白名单（用途速记）：price_last=最新价；ret_1d/5d/20d=近1/5/20日收益；vol_20d=20日波动率；max_drawdown_1y=近1年最大回撤；pe_ttm/pb/ps_ttm=当前估值；pe_quantile_5y/pb_quantile_5y=5年估值分位数；revenue_yoy/profit_yoy=营收/利润同比增速。",
              "items": {
                "type": "string",
                "enum": [
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
                  "profit_yoy"
                ]
              },
              "minItems": 1
            }
          },
          "required": ["symbol", "metrics"]
        }
      }
    }
  ]
}
```

#### 4.2.2 metrics[] 白名单（enum）设计

- **目的**：把“能力声明”写进工具 schema，避免拆分多个工具、也避免 LLM 发明不存在的指标。
- **原则**：
  - `metrics` 必须是 **枚举**，不可自由拼接字符串
  - 每个 metric 都有：数据源、计算方式、所需字段、频率、默认窗口、输出类型

**示例枚举（节选）**：

- `price_last`：最新价（需带时间戳）
- `ret_1d` / `ret_5d` / `ret_20d`
- `vol_20d`：20 日年化波动率（基于收盘价）
- `max_drawdown_1y`
- `pe_ttm` / `pb` / `ps_ttm`
- `pe_quantile_5y` / `pb_quantile_5y`
- `revenue_yoy` / `profit_yoy`（若数据可得）

> 完整 enum 列表以产品侧维护的 schema 为准；PRD 要求：**必须可版本化**（v0.6.2 固化一版）。

---

### 4.3 Hook 分层返回（必须实现）

#### 4.3.1 核心约束

- **禁止**：任何 “raw_data 历史数组 / DataFrame / 超长明细” 进入 LLM 上下文（防 token 浪费与误请求）
- **允许**：raw_data 只在本地 Hook 与前端可见（用于绘图/调试）

#### 4.3.2 Hook 返回结构（规范）

> 该 JSON 字符串应放在 role: "tool" 消息的 content 字段中。
> 仅将 metrics_data 序列化为字符串传给 Kimi，chart_index 存储在本地后端上下文。

- **注意**：规范化建议：务必保持 Tool 定义中的 enum 字段名与 Hook 返回的 JSON Key 完全一致

```json
{
  "metrics_data": {
    "asof": "2026-02-26",
    "symbol": "600519",
    "metrics": {
      "price_last": 1234.5,
      "ret_20d": 0.083,
      "pe_quantile_5y": 0.72
    },
    "notes": ["pe_quantile_5y 基于近5年日频 PE_TTM 分位数计算"]
  },
  "chart_index": [
    {"chart_id": "px_1y", "type": "line", "data_ref": "local://series/close_1y"},
    {"chart_id": "pe_5y", "type": "line", "data_ref": "local://series/pe_ttm_5y"}
  ]
}
```

- `metrics_data`：**唯一**进入 LLM（用于 insight）
- `chart_index`：直接流向前端绘图（**不进入 LLM**）

---

### 4.4 system prompt 强约束（必须写入）

当用户问题涉及以下内容，**不得**使用 web_search 推断数值，**必须**调用 `akshare_tool`：

- 实时行情/价格/涨跌幅/收益率
- 估值（PE/PB/PS、分位数）
- 波动率/回撤/风险指标
- 财务指标（营收/利润/同比等）

并且：

- LLM 只能基于 `metrics_data` 生成结论
- 若缺失指标：必须补充 tool_call 或明确“数据不足，无法计算”

---

### 4.5 web_search：环境感知（官方工具库，多次但受预算控制）

- 允许多次搜索（建议 ≤ 3），用于对冲信息偏见（利好/利空平衡）
- 输出必须结构化：`title / source / published_at / key_claim / url`
- 必须提供可追溯时间戳（用于冲突仲裁）

> 重点：上下文保留：在返回搜索结果时，必须完整保留 assistant 消息中的 tool_calls 和 reasoning_content。

---

### 4.6 数据冲突仲裁（Time-Priority）

当 `akshare_tool` 与 `web_search` 结果冲突时：

1. **时间戳更新者优先**
2. 同一时间范围内：以 **官方公告/监管披露** 权重最高
3. 必须在卡片中标注：**数据来源 + 时间**

---

## 五、金融花园卡片协议（Garden Protocol）

### 5.1 Block 类型（生态化扩展）

- **Soil（土壤/宏观）**：宏观/政策/行业环境（text + 关键引用）
- **Flowering（花期/趋势）**：价格/估值/波动走势（chart via `chart_index`）
- **Yields（果实/指标）**：核心指标（metric）
- **Fertilizer（肥料/资金）**：资金面/成交/持仓（metric/chart）
- **Pests（害虫/风险）**：风险清单（list）
- **Roots（根系/历史）**：长期结构（text/metric）
- **Pruning（修剪/建议）**：动作建议（text，必须引用上面的指标与风险）

### 5.2 约束标准

- **Block 数量**：推荐 2–6；复杂问题可扩展至 8，但必须保持信息密度
- **Insight**：取消字数限制；要求“去废话、重逻辑、可追溯”
- **新闻条数**：不强制 3 条；上限 5 条；无重大新闻可少于 3 条或并入 Soil

---

## 六、Agent Loop 与性能控制

### 6.1 自省与容错（Self-Correction）

- Tool Call 报错（超时、解析失败、缺字段）→ **自动重试一次**
- 二次失败 → 执行 `fallback_assemble()` 输出“部分残缺卡片”，并写明失败原因
- 严禁死循环

### 6.2 熔断机制（Token/Cost Limit）

- 取消固定循环次数
- 设置阈值（示例）：
  - 单请求 Token 上限：5000
  - 或 成本上限：1 RMB
- 超过阈值 → 强制 `assemble()` 汇总当前最优结果

---

## 七、开发与工程化要求

### 7.1 显式日志流（Logging Strategy）

必须记录：

- `RAW_TOOL_REQUEST`
- `RAW_TOOL_RESPONSE`（允许落盘/压缩，但不得喂给 LLM）
- Token/成本统计
- 仲裁决策日志（为何选某个时间戳）

### 7.2 稳定性保障（Eval Set）

- 建立 20 个“黄金问题”测试集：行情、估值、跨行业对比、争议标的、无新闻情境
- 每次 Prompt/Schema 变更后必须跑批，验证：
  - JSON 结构完整性
  - 字段准确率
  - tool-call 命中率（特别是 akshare 强制项）

### 7.3 开发路径

1. Codex 生成 `.py`（模块化）
2. 复制到 `ipynb`（带日志调试）
3. Eval Set 跑批（稳定性回归）
4. Streamlit/前端渲染（`chart_index` 本地绘图）

---

## 八、可实施性标准总结

- **所有数值来自工具**：指标必须由 `akshare_tool` + `Hook` 计算产生
- **LLM 不碰 raw_data**：只读 `metrics_data`
- **chart 不入上下文**：`chart_index` 直通前端
- **冲突可仲裁**：Time-Priority + 来源标注
- **循环可熔断**：Token/成本阈值兜底
- **调试可见**：日志与测试集是工程标配

---

*PRD Version: v0.6.4_c_review* 
