# Engineering Plan v1.md

## Summary
目标是在不写实现代码的前提下，给出可直接执行的工程规划规格。范围限定为单体 Streamlit MVP：`/Users/hujiawei/Documents/PomeFiDemo/app.py`、`/Users/hujiawei/Documents/PomeFiDemo/skill_engine.py`、`/Users/hujiawei/Documents/PomeFiDemo/utils.py`、`/Users/hujiawei/Documents/PomeFiDemo/mock_data.py`。  
本版本强调最小接口冻结、`output_mock.md` 字段对齐、异常可降级渲染，不引入 schema/registry。

## 1. 文件职责（冻结）

### `/Users/hujiawei/Documents/PomeFiDemo/app.py`
- 仅负责页面路由、组件布局、交互触发、结果渲染。
- 不直接请求 Akshare/Kimi。
- 仅调用 `generate_skill_card(skill_type, input_param)`。
- 负责 `quality_status` 对应的 UI 呈现策略（valid/degraded/error）。

### `/Users/hujiawei/Documents/PomeFiDemo/skill_engine.py`
- 唯一真实数据逻辑入口。
- 负责输入校验、Akshare 数据拉取、Kimi prompt 组装、LLM 调用、normalize、统一返回结构。
- 对外只暴露 `generate_skill_card`，内部细分 skill-specific 处理函数。

### `/Users/hujiawei/Documents/PomeFiDemo/utils.py`
- 纯工具函数：JSON 清洗、字段补齐、时间格式化、数值格式化、免责声明注入、文案禁词检查。
- 不包含业务路由与外部 API 调用。

### `/Users/hujiawei/Documents/PomeFiDemo/mock_data.py`
- 仅服务 Message/Chat/Profile 的静态展示数据。
- 不参与 Skill Lab 真实链路。
- 保持与 UI 组件期望字段稳定对齐。

## 2. Public API（最小冻结）

### 核心接口
- `generate_skill_card(skill_type: str, input_param) -> dict`

### 统一返回壳
- 顶层字段固定：`data`、`metadata`、`quality_status`
- `metadata` 至少包含：`generated_at`、`data_source`
- `quality_status` 枚举：`valid` / `degraded` / `error`

## 3. `generate_skill_card` 内部结构草稿（伪代码）

```text
function generate_skill_card(skill_type, input_param):
  validate skill_type in {trend_follower, fund_diagnostic, stock_diagnostic}
  validate input_param format by skill_type
  init response_shell = {data: {}, metadata: {generated_at: now, data_source: "akshare+kimi"}, quality_status: "valid"}

  try:
    raw_market_data = fetch_akshare_data_by_skill(skill_type, input_param)
  except:
    return minimal_renderable_payload(skill_type, status="degraded", reason="akshare_failed")

  prompt = build_kimi_prompt(skill_type, input_param, raw_market_data, style_constraints, output_contract)
  try:
    llm_raw = call_kimi(prompt)
    llm_json = parse_json(llm_raw)
  except:
    llm_json = {}
    mark status degraded

  normalized = normalize_skill_payload(skill_type, input_param, raw_market_data, llm_json)
  normalized = fill_missing_fields_with_NA(normalized, required_fields_by_skill)
  normalized = enforce_disclaimer_and_metadata(normalized)

  if normalized has only fallback core fields:
    status = degraded
  if unrecoverable:
    status = error with renderable minimal structure

  response_shell.data = normalized
  response_shell.quality_status = status
  return response_shell
```

## 4. 三个 Skill 详细规格

## 4.1 `trend_follower`
- 输入格式：
  - `input_param: str`
  - 约束：6位股票代码，例如 `300750`
- Akshare 数据来源函数（优先级）：
  - `stock_zh_a_hist(symbol, period="daily", ...)`：价格趋势序列
  - `stock_individual_spot_xq(symbol_with_exchange)`：当前估值相关字段（PE TTM 等）
  - `stock_individual_info_em(symbol)`：名称/行业补充
- Kimi prompt 结构：
  - `system`：华尔街分析师语气，禁止投资建议语句，输出 JSON，不要 Markdown
  - `context`：股票基础信息 + 近5年价格摘要 + 当前估值 + 可选新闻素材
  - `required_output`：上涨原因、题材地位、新闻时间线、估值解读、结构风险、画像匹配
  - `constraints`：短句、先事实后判断、禁用“必涨/强烈推荐”
- normalize 逻辑：
  - 生成标准模块：基本信息、属性、功能目录、输入参数、上涨原因、题材地位、新闻时间线、估值（近5年）、结构风险、画像匹配、免责声明、元数据
  - 缺字段补 `N/A`
  - 新闻时间线非法日期剔除并降级

## 4.2 `fund_diagnostic`
- 输入格式：
  - `input_param: str`
  - 约束：6位基金代码，例如 `001410`
- Akshare 数据来源函数（优先级）：
  - `fund_portfolio_hold_em(symbol, date)`：前十大重仓
  - `fund_portfolio_industry_allocation_em(symbol, date)`：行业集中度
  - `fund_individual_profit_probability_xq(symbol)`：辅助风格判断（可选）
- Kimi prompt 结构：
  - `system`：同上（风格 + JSON 输出）
  - `context`：重仓表、行业配置、市值/风格推导输入、用户画像
  - `required_output`：前十大重仓、行业集中度解读、市值风格、画像匹配、风险点评
  - `constraints`：不输出投资建议，不输出营销语
- normalize 逻辑：
  - 将重仓表规范为数组对象（名称/占比/行业）
  - 行业占比统一百分比字符串格式
  - 市值风格与价值/成长风格固定双维度输出
  - 缺字段补 `N/A` 并标记 degraded

## 4.3 `stock_diagnostic`
- 输入格式：
  - `input_param: list[str|int]`
  - 约束：5只股票代码列表，例如 `[600519, 002594, 600036, 601012, 601318]`
- Akshare 数据来源函数（优先级）：
  - `stock_individual_info_em(symbol)`：行业信息
  - `stock_individual_spot_xq(symbol_with_exchange)`：估值与规模辅助字段
  - `stock_zh_a_spot_em()`：批量行情补充（可选）
- Kimi prompt 结构：
  - `system`：同上（风格 + JSON 输出）
  - `context`：每只股票行业/规模/估值摘要 + 组合聚合统计
  - `required_output`：行业集中度、市值风格、组合风险、画像匹配
  - `constraints`：先结构后风险，短句，禁投资建议
- normalize 逻辑：
  - 先做组合聚合（行业占比、规模占比、估值分布）
  - 输出固定模块：行业集中度、市值风格、组合风险、画像匹配
  - 任一成分股数据缺失时保留组合可计算部分并降级

## 5. JSON 字段对齐规则（对齐 `/Users/hujiawei/Documents/PomeFiDemo/docs/output_mock.md`）

### 5.1 对齐原则
- 对齐“模块结构与字段语义”，非逐字值对齐。
- 每个 skill 都必须覆盖其对应模块，不允许缺块渲染。
- 顶层统一壳 + skill 内部字段并存。

### 5.2 顶层统一壳（工程接口）
- `data`: skill 业务字段
- `metadata.generated_at`
- `metadata.data_source`
- `quality_status`

### 5.3 `data` 内部公共字段
- `skill_id`
- `skill_category`
- `creator`
- `attributes.investor_persona`
- `attributes.mbti`
- `features[]`
- `input_summary`
- `disclaimer`

### 5.4 每个 Skill 必需字段
- `trend_follower`：
  - `upside_reasons[]`
  - `theme_position.{level,explanation}`
  - `news_timeline[]`（`date,title`）
  - `valuation_5y.{current_pe,percentile,interpretation}`
  - `structural_risks[]`
  - `profile_match.{summary,explanation}`
- `fund_diagnostic`：
  - `top10_holdings[]`（`name,weight,industry`）
  - `industry_concentration.{breakdown,interpretation}`
  - `market_cap_style.{cap_breakdown,style_breakdown,interpretation}`
  - `profile_match.{summary,explanation}`
  - `risks[]`（若无则 `N/A`）
- `stock_diagnostic`：
  - `industry_concentration.{breakdown,interpretation}`
  - `market_cap_style.{cap_breakdown,style_breakdown,interpretation}`
  - `portfolio_risks[]`
  - `profile_match.{summary,explanation}`

### 5.5 异常与补齐
- LLM 非法 JSON：保留 Akshare 可得字段 + 其余 `N/A`
- 字段缺失：仅补齐，不删除模块
- 无法恢复：返回最小可渲染结构并 `quality_status=error`

## 6. Tradeoff（架构取舍）

### 为什么不用 schema（当前阶段）
- MVP 目标是展示闭环，schema 文件与验证器会增加维护面与迭代阻力。
- 当前通过 normalize + 必填补齐即可满足稳定渲染。
- 后续若 skill 数量 >5 且跨团队协作，再引入 schema 更合算。

### 为什么不用 registry
- 当前仅3个 skill，分支路由成本低，可读性高。
- registry 会引入额外抽象层和注册生命周期管理，不符合“2-5天交付”。
- 当 skill 类型持续新增且有插件化需求时再迁移。

### 为什么单文件（每层一个主文件）
- 快速定位与面试演示友好，调用链短。
- 减少目录跳转和样板代码。
- 当前规模下，单文件复杂度可控；后续按热点函数拆分即可。

## 7. Known Risks + 缓解方案

- 风险：Akshare 接口波动/限频导致主路径失败  
  - 缓解：接口调用超时与重试上限；失败走 degraded；保留最小渲染结构。
- 风险：Kimi 输出非 JSON 或字段漂移  
  - 缓解：强约束 prompt、JSON 解析兜底、字段补齐与默认值策略。
- 风险：`output_mock.md` 示例存在局部不一致（如字段命名/样例值）  
  - 缓解：以模块语义为主，定义工程字段映射表并固定 normalize。
- 风险：图表依赖字段缺失导致前端报错  
  - 缓解：图表输入前做空值门禁；不足数据降级为说明卡片。
- 风险：文案风格偏离（情绪化或建议性表达）  
  - 缓解：prompt 加禁词与风格约束；utils 增加禁词扫描并替换。
- 风险：部署环境 secrets 配置错误  
  - 缓解：启动自检并给出明确缺失提示，不进入真实调用分支。

## 8. Test Cases & Scenarios（Planning 级）

- 主路径：
  - `trend_follower + 300750` 输出完整模块且可绘制趋势/估值图。
  - `fund_diagnostic + 001410` 输出重仓/行业/风格模块且图表可 hover。
  - `stock_diagnostic + [600519,002594,600036,601012,601318]` 输出组合分析与风险模块。
- 异常路径：
  - Akshare 失败 -> `degraded` + 可渲染。
  - Kimi 失败或 JSON 非法 -> `degraded` + 缺失字段补 `N/A`。
  - 输入非法 -> `error` + 友好错误信息。
- 对齐路径：
  - `data` 模块结构逐项比对 `output_mock.md`，不得缺块。
  - 每张卡片都必须有免责声明与元数据。

## 9. Assumptions & Defaults
- 当前阶段不写实现代码，只产出工程规划。
- 采用 `plan.md` 既有边界，不扩大产品范围。
- Akshare 函数以仓库文档中已出现接口为优先选型。
- `fund_diagnostic` 的示例值若与 mock 文案冲突，以 skill 类型和模块语义为准。
- 后续实现阶段若出现接口不可用，再替换同类数据源函数，不改变对外接口壳。
