# progress.md

## 当前阶段（Phase）
- Phase: timeline 优先跑通（唯一 critical）+ trace 透传修复
- 日期: 2026-03-17

## 本阶段目标
- 以 `timeline` 作为当前唯一 critical skill，优先保证它能跑通。
- 保证 `timeline_phase` 事件能真实透传进最终 trace。
- 在 `timeline` 跑通前，不让 `summary` 的 AkShare 失败继续挡住最终结果。

## 已完成要点
- 已新增 `agent-instructions.md`，整合静态规则（Kimi/Tool loop/JSON/AkShare/P*）。
- 已产出第一性原理问题清单并形成 P1-P5 因果链。
- 已新增个股最小验证脚本 `scripts/mvp_akshare_300750.py`。
- 已给 `PLAN_GUARDRAILS.md` 与 `FIRST_PRINCIPLES_ISSUE_CHECKLIST.md` 增加归档迁移说明，避免继续作为主入口。
- 已在 `akshare_tool` 增加 `stock_zh_a_hist` 失败时的 symbol 级缓存回退，并输出 `data_origin/network_evidence`。
- 已在 `summary/timeline` 接入 `data_origin/network_evidence/akshare_calls`，避免“无解释空白”。
- 已在 `aggregator` 增加 `network_live_failed_cache_hit|miss` 失败归因，收敛 strict-fail 误判。
- 已在前端与 trace 事件中展示 `data_origin` 与网络证据摘要，且指标层不再直出 `None`。
- 已在 `agent-instructions.md` 新增 B1-B4：最终输出必须二值，禁止最终对外 `degraded`。
- 已重构 `pomefi/stock_wiki/aggregator.py`：
  - 新增 `resolve_execution_outcome()`；
  - metadata 追加 `execution_status/failure_reason_*`；
  - 最终 `quality_status` 固定映射为 `valid|error`。
- 已在 `stock_summary/timeline/orchestrator` 增加 `recovered + unrecovered_reason_code`，统一未恢复失败判定。
- 已在 `engine.py` 路由拦截路径输出标准失败合同（`ROUTING_UNRESOLVED`）。
- 已在 `render.py` 增加 failed 专用展示卡：失败码、阶段、证据；failed 时不再渲染业务成功卡。
- 已更新二值合同相关测试并通过。
- 已重构 `pomefi/stock_wiki/orchestrator.py`：
  - 新增 `orchestrator_short_circuit` 事件；
  - 核心 skill 失败后取消非关键 skill；
  - 非关键被取消时统一填充 `cancelled_due_to_critical_failure`。
- 已扩展 `aggregate_stock_wiki_payload(...)`：
  - 新增可选参数 `short_circuit/cancelled_skills`；
  - metadata 持久化短路证据。
- 已在 `engine.py` 透传短路信息到最终 payload 和 trace。
- 已在 `render.py` failed 卡新增 `short_circuit` 与 `cancelled_skills` 展示。
- 已补 `orchestrator` 快速失败测试（summary/timeline 两条路径）。
- 已重构 `pomefi/tools/akshare_tool.py`：
  - `execute()` 改为按指标懒加载，不再无条件调用 info/financial/valuation；
  - `get_cached_price_history()` 增加 key 级 singleflight，避免并发重复远程拉取；
  - `stock_zh_a_hist` 增加有限重试与退避（网络类错误）；
  - `akshare_calls/network_evidence` 追加 `dedup_hit/retry_count` 字段。
- 已在 `stock_summary` 收敛失败判定：
  - 仅当价格主链路 live/cache 都不可用时，才给 `AKSHARE_NETWORK_UNRECOVERED`；
  - 非核心接口失败不再放大为核心未恢复失败。
- 已在 `aggregator` 失败证据中补充 `akshare_calls` 片段，便于验证去重与重试是否生效。
- 已补 AkShare 专项测试：按需加载、singleflight、重试成功、非核心失败不致命。
- 已重构 `pomefi/stock_wiki/skills/timeline.py`：
  - `price_series` 与 `events_json` 改为并行执行；
  - `events_json` 改走 direct JSON 主路径，不再做二次结构化调用；
  - `timeline.trace` 新增 `phase_latency_ms/phase_status/phase_error`。
- 已在 `pomefi/stock_wiki/skills/common.py` 新增 `run_tool_grounded_json_direct()`：
  - 强制 `web_search tool_call`；
  - tool 回填后直接输出 JSON object；
  - 保留 `tool_call_observed/retry_count/observed_tools`。
- 已在 `aggregator` 的 `failure_evidence` 中追加 `phase_latency_ms/phase_status/phase_error`。
- 已补 `timeline` 专项测试：
  - 并行双支路；
  - `events_json` 未恢复失败；
  - failure evidence 带 phase 级信息。
- 已确认调试下载包根结构是 `result/trace/local_context`，后续诊断统一从 `result.metadata` 与 `trace.skill_results` 读取。
- 已确认 `/Users/hujiawei/Downloads/pomefi_debug_trace_36f870702099.json` 的首个 critical fail 是 `summary`，不是 `timeline`。
- 已确认当前 `timeline` timeout placeholder 会丢失内部 `trace.phase_*`，因此还无法从诊断包判断失败在 `price_series` 还是 `events_json`。
- 已收敛 `summary` 的 AkShare 调用面：
  - 当只是为 `price_last/ret_1d` 做 fallback 时，不再额外调用 `stock_individual_info_em`；
  - `summary` 优先使用 `stock_individual_spot_xq` 做轻量回退，避免无关接口放大失败噪声。
- 已在 `orchestrator` 保留 `timeline` timeout 前的 phase 证据：
  - `trace.phase_latency_ms`
  - `trace.phase_status`
  - `trace.phase_error`
- 已补回归测试：
  - `summary` fallback 路径不再触发 `stock_individual_info_em`
  - `timeline` timeout placeholder 会保留 `phase_*`
- 已修复 `orchestrator._invoke_runner()`：
  - 对 `lambda s, n, **kw` 这类 runner 也会透传 `event_handler`
  - `timeline_phase` 不再因为 `**kwargs` 被吞掉
- 已把当前阶段的 critical 判定收窄到 `timeline`：
  - `summary` 失败不再直接触发最终 `execution_status=failed`
  - 当前用户目标改为“必须先跑通 timeline”
- 已更新回归测试：
  - `summary` 失败但 `timeline` 成功时，整体仍判定为 `success`
  - `timeline` runner 通过 `**kwargs` 仍能收到 `event_handler`
- 已读取 `/Users/hujiawei/Downloads/pomefi_debug_trace_26c2e3a13908.json`，确认：
  - `summary` 已 `valid`
  - `timeline` 是当前唯一 critical fail
  - `timeline.price_series` 已成功，失败集中在 `events_json`
  - 当前超时不是 AkShare，而是 `events_json` 未稳定触发 `web_search tool_call`
- 已重构 `timeline.events_json`：
  - 不再使用“tool + json_object 同轮”主路径
  - 改回“两阶段稳定路径”：先 `web_search` 取证，再独立做 `json_object` 结构化
  - `price_series` 并行支路保持不变
- 已复核官方手册 `docs/Kimi_API_Usage_Guide_v1.md`，确认：
  - 官方标准闭环是 `tool_calls -> role=tool -> 再继续推理`
  - `response_format=json_object` 只保证 JSON object，不保证必需 `tool_call` 稳定触发
  - 因此 `timeline` 不再尝试把 tool use 和最终 JSON 压到同一轮主路径
- 已按官方闭环进一步收紧 `timeline` 第一阶段 prompt：
  - 第一轮必须只输出 `tool_calls`
  - 第一轮禁止输出正文和 JSON
  - 仅在拿到 `tool` 结果后输出证据摘要，再进入第二阶段结构化
- 已读取 `/Users/hujiawei/Downloads/pomefi_debug_trace_643cd8c3fd1f.json`，确认：
  - `timeline.price_series` 已 `valid`
  - 第一阶段 `web_search tool_call` 与 `tool_result` 已成功
  - 第一阶段 `session_done` 已产出证据摘要
  - 当前唯一剩余失败点是第二阶段 `timeline_json`
- 已收敛 `timeline_json` 结构化阶段：
  - `build_tool_grounded_evidence()` 不再把 `MOONSHOT ENCRYPTED` 预览塞进第二阶段 prompt
  - `stream_json_object()` 在 `kimi-k2.5` 下默认通过 `extra_body={"thinking":{"type":"disabled"}}` 禁用思考
  - JSON 结构化默认 `max_completion_tokens` 从 `16000` 收紧到 `4096`
  - `timeline` 的 JSON 结构化进一步收紧到 `2048` tokens
- 已按最新要求把 `timeline` 收敛为 skill 层的价格单支路：
  - 暂停 `LLM` 事件支路
  - `timeline` 只做 live 价格抓取与折线图输出
  - 成功即显示价格折线图，失败即返回明确失败原因
- 已新增 `get_live_price_history()`：
  - 只走 live `stock_zh_a_hist`
  - 不使用价格缓存回退
  - 不返回历史缓存价格
- 已重构 `timeline`：
  - `price_series` 改用 `get_live_price_history()`
  - `events_json` 固定标记为 `skipped`
  - `trace.phase_status.events_json = skipped`
  - `summary` 改为“已抓取近三个月价格折线图；事件支路当前停用。”
- 已继续收敛 `timeline` 价格抓取路径，对齐已验证通过的 MVP 脚本：
  - 直接在 `timeline` skill 内调用 `ak.stock_zh_a_hist`
  - 参数对齐为 `period=daily / adjust=qfq / timeout=8.0`
  - `start_date` 固定为 `20250101`
  - 不再通过共享 price helper 间接取数

## 进行中
- 基于新代码重新生成诊断包，验证 `timeline.price_series` 是否能稳定 live 抓取成功并显示折线图。
- 继续以 `timeline` 为唯一 critical skill 做手动验收。

## 下一步（Next Action）
1. 运行 `streamlit run app.py`，重新生成新的诊断包。
2. 核对 `result.metadata.failure_stage` 是否仍为 `timeline`，而不是其他 skill。
3. 核对 `trace.skill_results.timeline.data.series` 是否非空。
4. 核对 `trace.skill_results.timeline.data.trace.phase_status.price_series` 是否为 `valid`。
5. 核对 `trace.skill_results.timeline.data.trace.phase_status.events_json` 是否为 `skipped`。
6. 若 `timeline` 仍失败，再只修 `price_series` live 抓取，不回头优先修其他卡片。

## 剩余边界条件/风险
- 网络或代理波动会导致 Eastmoney 接口间歇性失败。
- 单标的链路仍依赖 Eastmoney，可用性波动会影响 live run。
- 必须持续避免全市场接口误用与 `None` 指标直出。
- 二值模式会让失败暴露更直接，属于预期行为。

## 最新验证结果（命令 + 结论）
- 命令:
`python /Users/hujiawei/Documents/PomeFiDemo/scripts/mvp_akshare_300750.py > /Users/hujiawei/Downloads/mvp_akshare_300750_result.json`
- 结论: 成功（非降级）；个股基础信息与历史行情可拉取，输出字段完整。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo`
- 结论: 通过（`52 passed, 2 skipped`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_akshare_tool.py`
- 结论: 通过（`13 passed`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_orchestrator.py`
- 结论: 通过（`9 passed`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py`
- 结论: 通过（`3 passed`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_orchestrator.py`
- 结论: 通过（`9 passed`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo`
- 结论: 通过（`54 passed, 2 skipped`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_orchestrator.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_ui_smoke.py`
- 结论: 通过（`9 passed, 1 skipped`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_orchestrator.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_ui_smoke.py`
- 结论: 通过（`8 passed, 1 skipped`）。
- 命令:
`python -m py_compile app.py pomefi/tools/akshare_tool.py pomefi/tools/hooks.py pomefi/stock_wiki/skills/stock_summary.py pomefi/stock_wiki/skills/timeline.py pomefi/stock_wiki/orchestrator.py pomefi/stock_wiki/aggregator.py pomefi/stock_wiki/engine.py pomefi/ui/render.py`
- 结论: 通过（无语法错误）。
- 命令:
`读取 /Users/hujiawei/Downloads/pomefi_debug_trace_36f870702099.json`
- 结论:
  - 调试包根结构为 `result/trace/local_context`
  - `execution_status=failed`
  - `failure_stage=summary`
  - `failure_reason_code=AKSHARE_NETWORK_UNRECOVERED`
  - `timeline` 仍 timeout，但 `trace.phase_*` 未保留
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_akshare_tool.py`
- 结论: 通过（`13 passed`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_orchestrator.py`
- 结论: 通过（`10 passed`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo`
- 结论: 通过（`55 passed, 2 skipped`）。
- 命令:
`读取 /Users/hujiawei/Downloads/pomefi_debug_trace_9ec7890448b5.json`
- 结论:
  - `execution_status=failed`
  - `failure_stage=summary`
  - `failure_reason_code=AKSHARE_NETWORK_UNRECOVERED`
  - `timeline` 仍 timeout，且 `trace.phase_*` 仍未落盘
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_orchestrator.py`
- 结论: 通过（`11 passed`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo`
- 结论: 通过（`56 passed, 2 skipped`）。
- 命令:
`读取 /Users/hujiawei/Downloads/pomefi_debug_trace_26c2e3a13908.json`
- 结论:
  - `execution_status=failed`
  - `failure_stage=timeline`
  - `failure_reason_code=TIMELINE_TIMEOUT_UNRECOVERED`
  - `timeline.price_series=valid`
  - `timeline.events_json` 未产出 phase 结果，但事件流显示模型持续 reasoning/content，未稳定触发 `web_search tool_call`
- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py`
- 结论: 通过（无语法错误）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py`
- 结论: 通过（`3 passed`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_orchestrator.py`
- 结论: 通过（`11 passed`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo`
- 结论: 通过（`56 passed, 2 skipped`）。
- 命令:
`读取 /Users/hujiawei/Documents/PomeFiDemo/docs/Kimi_API_Usage_Guide_v1.md`
- 结论:
  - 官方推荐的是多步 `tool_calls` 闭环
  - 未证明“tool use + json_object 同轮”是稳定主路径
  - `timeline` 应继续使用“两阶段稳定路径”
- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/timeline.py`
- 结论: 通过（无语法错误）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_orchestrator.py`
- 结论: 通过（`14 passed`）。
- 命令:
`读取 /Users/hujiawei/Downloads/pomefi_debug_trace_643cd8c3fd1f.json`
- 结论:
  - `execution_status=failed`
  - `failure_stage=timeline`
  - `failure_reason_code=TIMELINE_TIMEOUT_UNRECOVERED`
  - `timeline.price_series=valid`
  - 第一阶段 `web_search tool_call/tool_result/session_done` 已成功
  - 第二阶段 `timeline_json` 只有 `llm_reasoning_delta`，没有 `llm_content_delta` 与 `structured_json_done`
- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/common.py /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/structured.py /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_structured_json_mode.py`
- 结论: 通过（无语法错误）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_structured_json_mode.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_orchestrator.py`
- 结论: 通过（`15 passed`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo`
- 结论: 通过（`56 passed, 2 skipped`）。
- 命令:
`读取 /Users/hujiawei/Downloads/pomefi_debug_trace_67a247db911d.json`
- 结论:
  - `execution_status=failed`
  - `failure_stage=timeline`
  - `timeline.price_series=error`
  - `phase_error.price_series` 为 live `stock_zh_a_hist` 抓取失败
  - 当前首要目标应切换为“先把价格折线图稳定抓取显示”
- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/tools/akshare_tool.py /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py`
- 结论: 通过（无语法错误）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_orchestrator.py`
- 结论: 通过（`14 passed`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo`
- 结论: 通过（`56 passed, 2 skipped`）。
- 命令:
`读取 /Users/hujiawei/Downloads/pomefi_debug_trace_9b29cfc845f7.json`
- 结论:
  - `execution_status=failed`
  - `failure_stage=timeline`
  - `timeline.price_series=error`
  - 当前失败已收敛为 live `stock_zh_a_hist` 抓取失败
  - `events_json=skipped`，说明 `timeline` 已完全进入价格单支路模式
- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/timeline.py`
- 结论: 通过（无语法错误）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_orchestrator.py`
- 结论: 通过（`14 passed`）。
- 命令:
`pytest -q /Users/hujiawei/Documents/PomeFiDemo`
- 结论: 通过（`56 passed, 2 skipped`）。

## 阻塞项（如有）
- 仍缺新的手动诊断包，暂时无法确认“价格单支路 + live-only”是否已让 `timeline` 折线图稳定显示。
