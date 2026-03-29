# agent-instructions.md

## 1. 用途
- 只放长期规则，不放阶段进度。
- 日常小修优先走最小方案；只有规则变化时才改本文件。

## 2. 执行模式
- `lite`：默认模式。用于前端样式、小型渲染修复、单卡文案、小测试修复。
- `full`：仅用于 prompt/schema/contract 变更、live 链路排障、AkShare/Kimi 接口问题、核心模块改动。

## 3. 固定契约
- 小任务默认不必完整重读本文件。
- `lite` 只需遵守本文件第 4-7 节，并只读 `progress.md` 顶部摘要区。
- `full` 需要读完整 `agent-instructions.md` 和 `progress.md`。
- AkShare 报错先查 `docs/stock.md`。
- Kimi 报错先查 `docs/Kimi_API_Usage_Guide_v1.md`。

## 4. 核心编码原则
- 用最简单、最短、能直接解决问题的方案。
- 默认不加无必要的防御性分支、fallback、抽象层。
- 优先修真实失败路径，不用 UI 掩盖或文案遮羞。
- 写完先自检：是否还能删、是否确实必要。

## 5. Kimi / Tool 关键约束
- 结构化输出必须 `response_format={"type":"json_object"}`，且 prompt 写清 schema。
- 禁止混用 partial mode 与 json_object。
- assistant message 必须原样回填；tool message 必须带 `tool_call_id`。
- Formula body 透传模型 `function`，`arguments` 保持 JSON string。
- `kimi-k2.5` 不手动设置 `temperature`。

## 6. AkShare 关键约束
- 在线主链路禁止全市场实时接口。
- 单标的优先个股接口；同请求同 `symbol+period` 必须去重。
- 请求必须有 timeout；错误必须可分类、可追踪。
- 前端禁止直接展示 `None`；要么显示有效值，要么显示原因。

## 7. progress.md 规则
- 只有出现以下情况才更新 `progress.md`：
  - contract 改动
  - blocker 新增/解除
  - live 验证结论
  - 当前阶段或下一步发生变化
- 纯 UI 微调、spacing、颜色调整，不默认写入 `progress.md`。
- 若 `progress.md` 超过 200 行，先压缩到 100 行以内。
