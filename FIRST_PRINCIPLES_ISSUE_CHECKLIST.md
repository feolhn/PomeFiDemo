# [归档说明] 本文件已迁移

- 主入口已迁移到 `/Users/hujiawei/Documents/PomeFiDemo/agent-instructions.md`（静态规则）与 `/Users/hujiawei/Documents/PomeFiDemo/progress.md`（动态进度）。
- 本文件保留为历史归档，不再作为每次任务的主入口。

# PomeFi 第一性原理问题清单

## 0. 系统目标（先定义“成功”）
- 目标不是“某个 AkShare 函数偶尔可用”，而是“单次请求稳定产出 5 张卡片且关键卡片可用”。
- 成功判据：`summary` 和 `timeline` 至少 `data_ready=True`，整体不触发 `strict_fail`。

## 1. 必要条件（缺一不可）
- C1：A 股 symbol 解析成功（路由必须得到 `300750` 这类代码）。
- C2：核心行情链路可达（`stock_zh_a_hist` 或等价核心价格来源必须成功）。
- C3：核心指标可构造（`price_last/ret_*` 不能全部缺失）。
- C4：并行技能在 soft-timeout 内完成（至少关键技能不能 timeout）。
- C5：聚合层不把关键失败升级为全局 `strict_fail`。

## 2. 已观测问题（按因果链）

### P1. 单点可用 ≠ 系统可用
- 现象：`mvp_akshare_300750.py` 成功，但前端请求失败。
- 根因：MVP 只验证两次单点调用；PomeFi 是多技能并发、强依赖链路的乘法系统。
- 证据：诊断包 `/Users/hujiawei/Downloads/pomefi_debug_trace_bdfdba20f101.json` 中多技能同时降级。
- 检查动作：区分“接口可用性测试”和“系统链路可用性测试”，不能互相替代。

### P2. 核心价格链路波动导致双关键技能同时失效
- 现象：`summary` 报 `summary_core_metrics_unavailable`，`timeline` 报 `price_fetch_failed`。
- 根因：两者共享历史行情依赖；同一波网络/代理失败会同时击穿。
- 证据：同一 trace 内 `stock_zh_a_hist` `ProxyError`，两技能同步失败。
- 检查动作：单请求内记录并对比 summary/timeline 的 AkShare 调用证据与时间戳。

### P3. 严格失败策略把局部失败放大为全局失败
- 现象：页面出现 `DEGRADED/ERROR`，整体体验失败。
- 根因：聚合层对 critical skill 的 `data_ready=False` 直接触发 `strict_fail`。
- 证据：`failure_mask` 包含 `summary`/`timeline` 时直接升级。
- 检查动作：逐次核对 `critical_failures` 与 `quality_status` 的对应关系。

### P4. 并发超时预算挤压非关键技能，造成“看起来全坏”
- 现象：`relationship` 5s、`entity_info` 18s、`watch_calendar` 20s timeout。
- 根因：技能并发下，LLM/tool 阶段叠加耗时，预算不足时被统一截断。
- 证据：trace 中 `timeout_soft_5s/18s/20s` 同时出现。
- 检查动作：按技能统计 `latency_ms`，先判断是“慢”还是“错”。

### P5. 入口前置依赖增加了额外脆弱点
- 现象：有时尚未进入主分析就不稳定。
- 根因：前端 symbol 解析依赖 `stock_info_a_code_name()`（全量代码表加载）。
- 证据：入口函数 `_load_stock_table()` 每次链路都依赖该数据源缓存状态。
- 检查动作：将“路由失败”与“分析失败”分层记录，避免混淆。

## 3. 第一性原理排查顺序（固定）
1. 先验证路由输出：`symbol/company_name/scope` 是否正确。
2. 再验证核心价格链路：`stock_zh_a_hist` 在当前请求是否成功。
3. 再验证核心指标：`summary` 是否拿到任一 `price_last/ret_*`。
4. 再看并发超时：哪些技能是 timeout，哪些是真异常。
5. 最后看聚合判定：是否由 `critical_failures` 触发 `strict_fail`。

## 4. 判定规则（避免误判）
- 若 MVP 成功但系统失败：优先判定为“架构链路问题”，不是“AkShare 完全不可用”。
- 若 `summary+timeline` 同时失败：优先排查共享依赖（价格历史/网络路径）。
- 若多数技能 timeout：优先排查 timeout 预算和并发策略，不先怀疑 JSON 解析。

## 5. 本清单用途
- 每次出现“脚本能跑、前端失败”时，必须按本清单顺序复盘。
- 结论必须落到具体层：路由层 / 数据层 / 并发层 / 聚合层，禁止笼统归因为“网络问题”。
