# agent-instructions.md

## 1. 文档用途（静态）
- 本文件是项目固定系统提示、边界条件与执行规范。
- 本文件只放长期规则，不放阶段进度。
- 规则变更时更新；日常任务不频繁改动。

## 2. 固定执行契约（每次任务都要用）
- Prompt 开头固定为：
`请先读取 agent-instructions.md 和 progress.md，然后按步骤执行第 X 阶段，并更新 progress.md。`
- 执行顺序固定：先读规则 -> 再读进度 -> 再执行 -> 最后更新 `progress.md`。

## 3. 项目目标与 MVP 边界
- 目标：交付可运行的 PomeFi MVP（A 股单标的分析 + Streamlit 展示）。
- 范围内：`summary/entity_info/timeline/watch_calendar/relationship` 五卡片链路。
- 范围外：多市场扩展、复杂多 agent 编排、重型治理体系。

## 3.1 核心编码原则（最高优先级）
- 始终采用最简单、能完全解决当前任务的方案。
- 使用最少的代码行数，避免无关抽象和提前优化。
- 不添加任何多余内容；默认不写防御性 `try-except`、不补无必要的 degrade/fallback、不过度拆辅助函数。
- 让错误自然暴露，便于快速调试；禁止隐藏、掩盖或绕过真实问题。
- 写完代码后先自检：这是不是能正常工作的最小版本；删掉任一部分后是否仍然必要。

## 4. Kimi / Tool Loop / JSON Mode 硬约束
- C1: 默认 `stream=True`；非流式仅限 probe 或特例。
- C2: 结构化输出必须 `response_format={"type":"json_object"}`。
- C3: prompt 必须显式写 JSON object schema。
- C4: 禁止混用 partial mode 与 json_object。
- C5: 流式 `tool_calls` 必须按 `delta.tool_calls + index` 拼装 arguments。
- C6: assistant message 必须原样回填，禁止手搓残缺字典。
- C7: 每个 `tool_call` 必须有对应 `role=tool + tool_call_id`。
- C8: Formula body 透传模型 `function`，`arguments` 保持 JSON string。
- C9: 流结束按完整流结束语义，不只看中间 `finish_reason`。
- C10: `kimi-k2.5` 强制 `temperature=1.0`，`reasoning_content` 用 `getattr/hasattr`。

## 4.1 最终结果合同硬约束（二值）
- B1: 对用户的最终结果只能二选一：`execution_status=success` 或 `execution_status=failed`。
- B2: 禁止把 `degraded` 作为最终对外终态；`degraded` 只能作为内部过程态。
- B3: `failed` 必须返回 `failure_reason_code + failure_stage + failure_reason_message + failure_evidence`。
- B4: 恢复/重试策略只用于争取 `success`，禁止用于掩盖未恢复失败。

## 5. AkShare 硬约束（MVP版）
- A1: 在线主链路禁止全市场实时接口（如 `stock_zh_a_spot_em`）。
- A2: A 股单标的优先个股接口，禁止拿全市场接口做主路径。
- A3: 同请求同 `symbol+period` 必须去重复用，禁止重复拉数。
- A4: 所有 AkShare 请求必须有 timeout；禁止无限等待。
- A5: 异常必须分类（network/rate_limit/empty/schema）并可追踪。
- A6: 关键链路失败必须显式降级，不伪装成正常空结果。
- A7: 全量 symbol 名录接口必须缓存，禁止高频重复拉取。
- A8: 前端禁止直出 `None` 指标，必须显示“不可用 + 原因”。
- A9: 调试信息必须保留接口名/symbol/耗时/错误摘要。
- A10: `stock_individual_spot_xq` 必须做交易所前缀映射和参数校验。
- A11: soft-timeout 必须按 skill 独立计时，禁止相互挤占。
- A12: 单标的主链路优先 `stock_zh_a_hist + stock_individual_info_em`。
- A13: 解析逻辑要兼容 schema 漂移（至少 item/value 与列回退）。
- A14: 前端排障前先跑个股 probe 脚本验证接口可用性。
- A15: Eastmoney `ProxyError` 先排网络/代理，再判业务代码。

## 6. 禁止做法
- 禁止正则/字符串硬凑 JSON 作为主路径。
- 禁止把 `tool_call.function.arguments` 改 dict 后再重编码传 Formula。
- 禁止漏 append assistant 原始 message。
- 禁止 tool 条数与 tool_call 条数不一致。
- 禁止为了“稳定”回退到同步整包阻塞。
- 禁止失败时只给空数据，不给 `degrade_reason` 与错误上下文。

## 7. 第一性原理问题模型（P* 摘要版）
- P1: 单点接口可用不等于系统可用（乘法系统）。
- P2: 共享价格依赖波动会同时击穿 `summary/timeline`。
- P3: critical skill 失败会被聚合层放大为 `strict_fail`。
- P4: 超时预算不合理会造成“看起来全坏”。
- P5: 入口前置依赖（如 symbol 表加载）会引入额外脆弱点。

固定排查顺序：路由 -> 核心价格链路 -> 核心指标 -> 超时分布 -> 聚合判定。

## 8. 计划与验收最小模板（每次必须引用）
```md
# <任务标题>

## 目标
- ...

## 对齐约束
- C*: ...
- R*: ...
- A*: ...
- P*: ...

## 执行步骤
1. ...
2. ...

## 验收
- 命令: ...
- 通过标准: ...
```

## 9. 更新规则
- 本文件仅在“规则变化”时更新。
- 阶段状态、执行进展、阻塞信息一律写入 `progress.md`。
