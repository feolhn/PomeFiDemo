# [归档说明] 本文件已迁移

- 主入口已迁移到 `/Users/hujiawei/Documents/PomeFiDemo/agent-instructions.md`（静态规则）与 `/Users/hujiawei/Documents/PomeFiDemo/progress.md`（动态进度）。
- 本文件保留为历史归档，不再作为每次任务的主入口。

# PomeFi 计划护栏（Kimi 对齐版）

## 1. 文档用途（强制）
本文件是 PomeFi 的“计划前置护栏文档”。  
后续每次制定任何开发计划前，必须先阅读本文件并逐条对齐。  
如计划与本文件冲突，必须先修订计划，再进入实现。  
本文件的目标是防止 Kimi/OpenAI 细节偏差导致前端无内容、工具调用错位、结构化输出失效等反复问题。

## 2. 计划前置流程（每次都要执行）
1. 必须先阅读本文件第 3 章到第 7 章，确认无冲突项。
2. 必须在新计划里显式写出“本次对齐第 3 章硬约束编号”。
3. 必须在新计划里显式写出“第 6 章实时展示检查项”。
4. 必须在计划中标明哪些模块会改动（loop / skills / ui / orchestrator）。
5. 必须在计划中给出验收命令与通过标准，禁止只写“完成后验证”。
6. 制定计划前必须阅读第 11 章 AkShare 数据源硬约束。
7. 若本次涉及金融数据抓取，计划中必须显式列出“对齐 A* 编号”。

## 3. 不可违反的 Kimi 兼容硬约束
- C1: 必须将 `stream=True` 作为默认执行路径（非流式仅限 probe、诊断脚本或明确特例）。
- C2: 所有结构化输出必须使用 `response_format={"type":"json_object"}`。
- C3: 必须在 prompt 中明确 JSON object 的字段、类型和示例。
- C4: 禁止混用 `partial mode` 与 `response_format={"type":"json_object"}`。
- C5: 流式 `tool_calls` 必须按 `delta.tool_calls + index` 增量拼装 `function.arguments`。
- C6: assistant message 必须原样 `messages.append(message)`，不得手搓残缺字典。
- C7: 每个 `tool_call` 必须有对应 `role=tool + tool_call_id`，数量和 id 必须一一对齐。
- C8: Formula 调用 body 必须透传模型返回的 `function` 载荷，`arguments` 必须保持 encoded JSON string。
- C9: 流结束判定必须按完整流结束信号（SSE 语义为 `[DONE]`），禁止只靠中间 `finish_reason`。
- C10: `kimi-k2.5` 场景必须满足参数边界：`temperature=1.0`；`reasoning_content` 读取必须使用 `hasattr/getattr`。

## 4. 流式 Tool Use 标准实现顺序
1. 发起 `chat.completions.create(..., stream=True)`。
2. 增量读取 chunk，分别处理 `delta.reasoning_content`、`delta.content`、`delta.tool_calls`。
3. 用 `index` 组装完整 `tool_calls`，补齐 `id/name/arguments`。
4. 流完整结束后得到完整 assistant message，并原样 append 到 messages。
5. 逐个执行 tool_call，将结果作为 `role=tool` 回填，`tool_call_id` 必须匹配。
6. 继续下一轮，直到无 tool_calls 且最终内容完成。
7. 全程输出结构化事件日志，供前端实时展示。

## 5. JSON Mode 标准实现顺序
1. 在 system/user prompt 中先定义 JSON object schema 和示例。
2. 调用时必须设置 `response_format={"type":"json_object"}`。
3. 接收返回后必须执行 `json.loads(message.content)`。
4. 若返回截断或不完整，必须检查是否 `finish_reason=length` 并调整 token 上限。
5. 结构化失败必须走明确降级（含 degrade_reason），禁止静默吞掉错误。
6. 禁止把文本正则修补当主路径，JSON Mode 才是主路径。

## 6. 前端实时展示最低要求
- R1: 必须实时展示 thinking（`reasoning_content` 增量）。
- R2: 必须实时展示 tool use（tool_call 参数摘要 + tool_result 摘要）。
- R3: 必须实时展示 skill progress（start/running/done/degraded）。
- R4: 必须实时展示 final output（content 增量）。
- R5: Relationship 的 pending 仅允许由真实超时触发，禁止误判。
- R6: 调试区必须展示事件流与关键状态，保证“看得到过程”。

## 7. 常见反复问题与禁止做法
- 禁止用正则/字符串硬凑 JSON 作为主路径。
- 禁止把 `tool_call.function.arguments` 先改成 dict 再重编码传 Formula。
- 禁止漏 append assistant 原始 message。
- 禁止 tool 条数与 tool_call 条数不一致。
- 禁止只靠 `finish_reason` 判断流结束。
- 禁止为了“稳”回退到同步整包阻塞返回。
- 禁止在失败时只给空数据，不给 `degrade_reason` 和错误上下文。
- 禁止前端仅展示最终卡片而隐藏执行过程（会导致“看起来没抓到数据”）。

## 8. 计划输出模板（每次新计划直接复制）
```md
# <计划标题>

## 目标
- ...

## 硬约束
- 对齐 PLAN_GUARDRAILS 第3章: C1, C2, ...

## 接口变更
- ...

## 执行步骤
1. ...
2. ...

## Kimi兼容检查
- [ ] C1
- [ ] C2
- [ ] C3
- [ ] C4
- [ ] C5
- [ ] C6
- [ ] C7
- [ ] C8
- [ ] C9
- [ ] C10

## 实时可视化检查
- [ ] R1
- [ ] R2
- [ ] R3
- [ ] R4
- [ ] R5
- [ ] R6

## AkShare兼容检查
- [ ] A1
- [ ] A2
- [ ] A3
- [ ] A4
- [ ] A5
- [ ] A6
- [ ] A7
- [ ] A8
- [ ] A9
- [ ] A10
- [ ] A11
- [ ] A12
- [ ] A13
- [ ] A14
- [ ] A15

## 测试与验收
- 自动化: `pytest -q`
- 手动: `python scripts/probe_moonshot_sdk.py` / `streamlit run app.py`
- 通过标准: ...

## 风险与回退
- 风险: ...
- 回退: ...
```

## 9. 验收清单（上线前逐项勾选）
- [ ] 已阅读本文件并在计划中引用第 3 章硬约束编号。
- [ ] 结构化输出均使用 JSON Mode，且 prompt 定义了 schema。
- [ ] 流式 tool_calls 组装逻辑覆盖 `delta + index`。
- [ ] assistant/tool message 回填链路已通过对齐检查。
- [ ] Formula arguments 保持 encoded string 透传。
- [ ] 前端可实时看到 thinking / tool use / skill progress / final output。
- [ ] Relationship pending 仅真实超时触发。
- [ ] 自动化测试通过，手动验收通过。
- [ ] 未在在线链路使用全市场实时接口。
- [ ] 同请求无重复 AkShare 拉数（symbol+period 去重）。
- [ ] AkShare 错误可归类并可追踪。
- [ ] 前端无 `None` 指标直出。
- [ ] timeout 为 per-skill 独立计时，不会相互挤占。
- [ ] 单标的主链路不依赖 `stock_individual_spot_xq` 才能给出核心行情。
- [ ] 已运行 `scripts/probe_akshare_spot_mvp.py` 并记录接口可用性证据。
- [ ] 若出现 Eastmoney `ProxyError`，已先排查网络/代理再判代码问题。

## 10. 变更记录
- 2026-03-16: 初版建立。固定 Kimi 兼容硬约束、实时展示最低要求、计划模板与上线验收清单。
- 2026-03-16: 新增第 11 章 AkShare 护栏（A1-A10），并扩展计划模板与验收清单。
- 2026-03-17: 新增 A11-A15（timeout 分配、单标的主链路、schema 漂移兼容、探针前置、ProxyError 排查顺序）。

## 11. AkShare 数据源硬约束（新增）
- A1: 禁止在在线请求主链路调用全市场实时接口（如 `stock_zh_a_spot_em`、`stock_us_spot_em`、`stock_hk_spot_em`）。
- A2: A 股单标的分析必须优先单 symbol 接口（如 `stock_individual_*`），禁止用全市场接口当 symbol 发现主路径。
- A3: 同一次用户请求内，同一 `symbol+period` 的行情/估值数据必须单次拉取并复用，禁止跨 skill 重复调用。
- A4: 所有 AkShare 请求必须设置 `timeout`，并有有限重试与退避；禁止无限等待。
- A5: 必须对 AkShare 异常做统一分类（至少 `network` / `rate_limit` / `empty` / `schema`），并写入 `degrade_reason`。
- A6: 关键数据链路失败时必须显式失败展示（严格失败策略），禁止把缺失值伪装成“正常空结果”。
- A7: symbol 名录类全量接口（如 `stock_info_a_code_name`）必须缓存（内存或本地快照），禁止高频重复拉取。
- A8: 前端禁止直接渲染 `None` 指标，必须转为“不可用 + 原因”。
- A9: 调试信息必须保留 AkShare 调用证据：接口名、symbol、耗时、错误摘要。
- A10: `stock_individual_spot_xq` 必须统一走交易所前缀映射（`SH/SZ/BJ`）并做参数校验。
- A11: Orchestrator 的 soft-timeout 必须按 skill 独立计时，禁止用全局 elapsed 扣减后续 skill 的 timeout 窗口。
- A12: A 股单标的主链路必须优先 `stock_zh_a_hist + stock_individual_info_em`；`stock_individual_spot_xq` 仅作补充，禁止作为硬依赖。
- A13: 对 `stock_individual_info_em` 与 `stock_individual_spot_xq` 的解析必须兼容 schema 漂移（至少兼容 `item/value` 与第一/第二列回退）。
- A14: 在前端问题排查前，必须先运行个股探针脚本（`scripts/probe_akshare_spot_mvp.py`），先确认接口可用性再改业务代码。
- A15: 若 Eastmoney 域名（`push2.eastmoney.com` / `push2his.eastmoney.com`）出现 `ProxyError`，必须先定位代理/网络问题，禁止误判为业务逻辑 bug。
