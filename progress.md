# progress.md

## Historical Summary
- 已完成 Progressive Loading、本地 fixture 联调、五张单卡 JSON 调试链路。`timeline/watch_calendar/entity_info/relationship` 已能稳定产出当前 contract；`summary` 后端现已接入 AkShare 新浪 `stock_financial_abstract`，可输出近五年营收/净利润序列。

## 当前阶段（Phase）
- Phase: 本地 Fixture 前端收边 + `summary` 单卡收敛
- 日期: 2026-03-24

## 本阶段目标
- 用本地 fixture 收尾五张卡前端显示。
- 保持 `timeline/watch_calendar/relationship/entity_info` contract 稳定。
- 决定 `summary` 的近五年营收/净利润数据如何进入前端展示。

## 最近确认
- 前端 fixture 模式已稳定，页面不再依赖 live 链路才能验收。
- `timeline` 已有 `sentiment`，图和表事件数量已统一。
- `watch_calendar` 已支持短标题、自然时间表达、可选 `🔗`。
- `entity_info` 已恢复 `investment_tags`。
- `relationship` 已恢复语义化 `edges.relation`，前端 HTML 图也已开始渲染关系词。
- `watch_calendar` 两步 prompt 已压缩，保留工具约束、日期粒度和 JSON schema，不改主链路行为。
- `watch_calendar` 继续只保留 two-pass；one-pass 实验链路已判定为无价值并移除。
- `watch_calendar` 压缩 prompt 后 two-pass 仍保持 `valid`，且体感延迟未变差；但当前 live 内容更偏“业绩预期/产能规划/行业判断”，不再完全是明确公告节点。
- `watch_calendar` two-pass benchmark 已跑完：`3/3 valid`，但平均耗时约 `51.2s`，`source` 命名不稳定。
- `watch_calendar` 已回退过强约束：保留 `source` 固定，移除 `certainty`，避免和来源语义重叠。
- 已确认 `watch_calendar` 的“summary 说得更好、items 过于保守”主要出在第二阶段 JSON 抽取和本地事件压缩；现已放宽为允许“事件 + 结果短语”。
- `watch_calendar` 已移除 `date` tool；今天日期改为后端直传 prompt，只保留 `web_search` 作为必需工具。
- `watch_calendar` benchmark 现已按 run 落盘 `trace`，并静默底层过程输出；终端只保留最终 benchmark JSON。
- `watch_calendar` benchmark 现已改为落可读 `trace`：保留 query、turns、evidence preview、sources，不再暴露整段加密 tool content。
- `timeline` 已新增 Kimi-only benchmark：只看事件支路，不落 akshare/merged benchmark 结果。
- `timeline` 两步链路保留不变，但事件支路 user prompt 已压缩，删掉了和 system/schema 重复的约束。
- `timeline` 继续不使用 `date` tool；今天日期已由后端直传到两步 prompt，并明确只允许搜索/输出今天及之前的事件。
- 已修复 `timeline` benchmark 的 prompt 注入错误：`today_text` 改用安全字符串替换，不再因 JSON schema 花括号触发 `KeyError`。
- `timeline` 第一阶段事件筛选 prompt 已改成更接近 `watch_calendar` 的简洁结构，但仍保持“过去三个月、今天之前”的事件复盘口径。
- `timeline` 现已切到“过去六个月 + 最多三次 web_search”的实验配置，且窗口天数、tool budget、prompt 三处已对齐。
- `timeline` 的 AkShare 价格支路也已改成最近六个月窗口，不再只返回最近 90 条。
- `timeline` 第二步 JSON contract 已升级为 `title + content + sentiment`，暂不要求前端对齐。
- `entity_info` 已新增 Kimi-only benchmark：可多次对比行业、主业、摘要和标签稳定性。
- `entity_info` JSON contract 已扩展：新增 `core_competencies` 和 `profit_analysis`，用于拆开内部护城河与盈利质量。
- `entity_info` 已从一步直出 JSON 改成 two-pass：先 `web_search` 取证，再 `json_object` 结构化，降低标签和盈利分析乱编风险。
- `relationship` 现已新增 benchmark 脚本，可多轮对比 `summary/nodes/edges/trace`，不再只靠单次 live 判断图谱质量。
- `relationship` 的节点语义已拆分为：`company` 仅表示目标公司中心节点；`theme` 仅表示外部变量、政策、技术路线等非公司因素。
- `relationship` 第一阶段证据摘要现已强制按“上游/下游/竞争/关键变量”四行输出，降低第二阶段从自由文本抽图谱时的漂移。
- 已验证 AkShare 的新浪口径可拿到 5 年财务绝对值：`stock_financial_abstract` 可直接返回多报告期的 `营业总收入/归母净利润/净利润`，比东方财富链路更适合 `summary` 卡补 5 年财务序列。
- `summary` 后端现已真正接入 `stock_financial_abstract`：`summary.data.financial_series_5y` 已包含近五年 `report_date/year/revenue/net_profit`。
- `summary` 前端现已开始消费 `financial_series_5y`：在指标网格下方渲染“近五年营收 / 近五年净利润”竖向柱状图。

## 当前下一步
1. 继续收 `relationship` 前端布局，直到关系词与节点不再互相遮挡。
2. 若继续优化 `watch_calendar`，应收紧 prompt：优先明确公告/已披露节点，并保持 `source` 固定口径。
3. 重新跑 `debug_watch_calendar_card.py`，验证移除 `date` tool 后耗时与结果质量是否保持稳定，并确认 items 保留“预计扭亏为盈”这类关键结果短语。
4. 继续验收 `summary` 柱状图的可读性，包括移动端宽度、年份标签和单位表达。
5. 如需继续收 `entity_info`，下一步看 benchmark 多轮 live 的稳定性，而不是再回到无工具链路。
6. 如需继续收 `relationship`，下一步先跑 benchmark 看多轮 `nodes/edges` 稳定性，再决定是否继续调 prompt。

## 阻塞项
- 默认代理环境仍会把 `summary` live 链路打成 `network_live_failed_cache_miss`；无代理环境下后端逻辑已验证可用。
- `relationship` 仍存在移动端布局密度问题，属于前端渲染问题，不是后端 contract 问题。

## 剩余风险
- 未开 fixture 时，前端仍可能被 live timeout 干扰。
- `watch_calendar` 的来源链接依然取决于 tool 证据是否提供可复用 URL。
- `watch_calendar` 当前虽能稳定返回，但事件类型有向“预期驱动”漂移的风险，可能削弱日历卡的可执行性。
- `watch_calendar` 当前平均 50s 级耗时偏高，不适合作为前端默认实时链路。
- 即使收紧 prompt，`source` 仍可能受模型波动影响；若这轮 live 仍不稳，下一步应改为本地规则归一，而不是继续堆 prompt。

## 最新验证结果
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/watch_calendar.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_watch_calendar_skill.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_watch_calendar.py`
  - `watch_calendar` 现在只保留 two-pass 主链路，并已新增 benchmark 脚本。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/watch_calendar.py /Users/hujiawei/Documents/PomeFiDemo/scripts/benchmark_watch_calendar.py /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_watch_calendar_card.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_watch_calendar_skill.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_watch_calendar.py`
  - `7 passed`
  - `watch_calendar` 已移除 `date` tool，今天日期改为后端直传 prompt，主链路只要求 `web_search`。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/scripts/benchmark_watch_calendar.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_watch_calendar.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_watch_calendar.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_watch_calendar_skill.py`
  - `7 passed`
  - benchmark 每轮已落 `trace`，并吞掉 live 过程输出，只保留最终结果 JSON。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/scripts/benchmark_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_timeline.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py`
  - `11 passed`
  - `timeline` 已新增仅覆盖 Kimi 事件支路的 benchmark，输出 events、sources 与可读 trace。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/timeline.py /Users/hujiawei/Documents/PomeFiDemo/scripts/benchmark_timeline.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_timeline.py`
  - `11 passed`
  - `timeline` 事件支路 prompt 已压缩，保留两步架构、搜索预算和 JSON schema，不改 contract。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/timeline.py /Users/hujiawei/Documents/PomeFiDemo/scripts/benchmark_timeline.py /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_timeline_card.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_timeline.py`
  - `11 passed`
  - `timeline` 已把今天日期改为后端直传，并在两步 prompt 中明确“只搜索/输出今天及之前、最近三个月的事件”。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/timeline.py /Users/hujiawei/Documents/PomeFiDemo/scripts/benchmark_timeline.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_timeline.py`
  - `11 passed`
  - `timeline.kimi.benchmark` 的 `KeyError: "\\n  \"summary\""` 已修复；根因是 JSON system prompt 用 `.format()` 注入日期时误解析了 schema 花括号。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/timeline.py /Users/hujiawei/Documents/PomeFiDemo/scripts/benchmark_timeline.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_timeline.py`
  - `11 passed`
  - `timeline` 第一阶段 prompt 已切到更接近 `watch_calendar` 的简洁筛选风格，但不改“过去事件”口径和 JSON contract。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/timeline.py /Users/hujiawei/Documents/PomeFiDemo/scripts/benchmark_timeline.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_timeline.py`
  - `11 passed`
  - `timeline` 的“过去六个月 + 最多三次 web_search”已真正落到代码，不再只是 prompt 文案。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/timeline.py /Users/hujiawei/Documents/PomeFiDemo/scripts/benchmark_timeline.py /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_timeline_card.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_timeline.py`
  - `11 passed`
  - `timeline` 的 AkShare 价格支路已从固定 `rows[-90:]` 改成按最近六个月窗口过滤，和事件支路对齐。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/timeline.py /Users/hujiawei/Documents/PomeFiDemo/scripts/benchmark_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_timeline.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_timeline.py`
  - `11 passed`
  - `timeline.events[]` 现已保留 `title + content + sentiment`，benchmark 也会同步展示内容摘要。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/scripts/benchmark_entity_info.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_entity_info.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_entity_info.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_debug_skill.py`
  - `4 passed`
  - `entity_info` 已新增 benchmark，输出多轮 live 的 `industry/main_business/summary_100cn/investment_tags` 与耗时统计。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/entity_info.py /Users/hujiawei/Documents/PomeFiDemo/scripts/benchmark_entity_info.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_entity_info.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_entity_info.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_debug_skill.py`
  - `4 passed`
  - `entity_info` 现已新增 `core_competencies` 与 `profit_analysis`，benchmark 同步输出这两个字段。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/entity_info.py /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/engine.py /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_skill.py /Users/hujiawei/Documents/PomeFiDemo/scripts/benchmark_entity_info.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_entity_info.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_entity_info.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_debug_skill.py`
  - `4 passed`
  - `entity_info` 已切到 `web_search -> json_object` two-pass，主流程、单卡 debug、benchmark 接线均已对齐。
- `/Users/hujiawei/Documents/PomeFiDemo/venv/bin/python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_entity_info_card.py`
  - live 结果：`entity_info.json.status=valid`
  - 当前 live 已观测到 `2` 次 `web_search`，并成功产出 `industry/main_business/summary_100cn/core_competencies/profit_analysis/investment_tags`。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/relationship.py /Users/hujiawei/Documents/PomeFiDemo/pomefi/ui/render.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_relationship_loop.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_relationship.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_relationship_loop.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_relationship.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_relationship.py`
  - `7 passed`
  - `relationship` prompt 已去掉部分重复约束；`nodes.role` 保持小枚举，但目标公司已独立为 `company`，前端中心节点识别同步对齐。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/relationship.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_relationship_loop.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_relationship.py`
  - `4 passed`
  - `relationship` 第一阶段现已强制按“上游/下游/竞争/关键变量”固定顺序输出摘要，便于第二阶段 JSON 抽取。
- `/Users/hujiawei/Documents/PomeFiDemo/venv/bin/python` live probe
  - `stock_financial_abstract(symbol="603618")` 成功返回 `80 x 52`，包含多报告期的 `营业总收入/归母净利润/净利润`
  - `stock_financial_analysis_indicator(symbol="603618", start_year="2020")` 成功返回 `23 x 86`
  - 结论：若要给 `summary` 卡加近五年营收/净利润，优先走新浪 `stock_financial_abstract`，不必优先走东方财富。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/tools/hooks.py /Users/hujiawei/Documents/PomeFiDemo/pomefi/tools/akshare_tool.py /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/stock_summary.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_akshare_tool.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_summary.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_akshare_tool.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_summary.py`
  - `16 passed`
  - `summary` 后端已新增 `financial_series_5y`，并通过单测覆盖。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/ui/render.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_summary.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_summary.py`
  - `4 passed`
  - `summary` 卡现已把近五年营收/净利润渲染为两个 vertical bar chart。
- `env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy /Users/hujiawei/Documents/PomeFiDemo/venv/bin/python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_summary_card.py`
  - live 结果：`summary.json.status=valid`
  - `summary.data.financial_series_5y` 已返回 2020-2024 五年 `revenue/net_profit`
  - 当前问题已从“后端没有五年财务序列”转为“前端如何展示这组数据”。
- `/Users/hujiawei/Documents/PomeFiDemo/venv/bin/python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_watch_calendar_card.py`
  - live 结果：`watch_calendar.json.status=valid`
  - `observed_tools=["web_search"]`
  - tool turns 变为：第 0 轮 `2` 次 `web_search`，第 1 轮输出证据摘要，不再调用 `date` tool。
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/watch_calendar.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_watch_calendar_skill.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_watch_calendar_skill.py`
  - `6 passed`
  - `watch_calendar` 第二阶段 event 规则已放宽，不再把“预计扭亏为盈”这类结果短语裁掉。
- `python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_watch_calendar_card.py`
  - live 结果：`watch_calendar.json.status=valid`
  - 当前事件为：
    - `2026年4月底 / 2026年一季报披露，预计扭亏为盈`
    - `2026年5月 / 硅料产能丰水期恢复超产`
    - `2026年 / 光伏行业周期筑底拐点之年`
  - 结论：压缩 prompt 后主链路未退化，甚至体感更快；但结果质量更偏“预期/规划/主题判断”，若目标是严格事件日历，后续需收紧筛选口径。
- `python /Users/hujiawei/Documents/PomeFiDemo/scripts/benchmark_watch_calendar.py --runs 3`
  - `3/3 valid`
  - `avg_latency_ms=51238`
  - `source` 在三次运行中出现了：
    - `证据摘要`
    - `证据摘要-业绩披露事件`
    - `行业政策公告`
    - `公司公告/业绩预测`
- `python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/watch_calendar.py`
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_watch_calendar_skill.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_benchmark_watch_calendar.py`
  - `6 passed`
  - `watch_calendar` 已回退为更简单 contract：保留 `source`，移除 `certainty`。
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_relationship.py`
  - `3 passed`
  - `relationship` HTML 图已支持关系词标签，但仍需继续收布局。
- `pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_debug_skill.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_relationship_loop.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_entity.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_relationship.py`
  - `19 passed`
  - `entity_info/relationship/timeline` 的后端 contract 已重新对齐前端。
