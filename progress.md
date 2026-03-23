# progress.md

## Historical Summary
- 已完成 Progressive Loading、本地 fixture 前端联调、五张单卡 JSON 调试链路。`timeline` 与 `watch_calendar` 已完成 live 修复并可稳定落盘 `valid` JSON；前端 `timeline/relationship` 的 timeout 主要来自误跑 live。当前重点是继续用本地 fixture 修前端，并单独收敛 `summary`。

## 当前阶段（Phase）
- Phase: 本地 Fixture 前端联调 + Summary 单卡收敛
- 日期: 2026-03-19

## 本阶段目标
- 用本地 fixture 验收五张卡前端，不让 live timeout 干扰 UI。
- 保持 `timeline`、`watch_calendar`、`relationship` 的单卡 JSON contract 稳定。
- 把 `summary.json` 从 `error` 拉回 `valid`。

## 已完成要点
- `app.py` 已支持“使用本地 Fixture 调试”，fixture 模式直接渲染最终 payload。
- `timeline` 已修复：
  - Kimi 事件支路可从 `trace.final_content` 回收事件
  - 年份归一已修复
  - live `debug_timeline_card.py` 已成功，`timeline.json=status=valid`
  - 前端图表已改为显示全部 4 个事件空心点，hover 才显示事件名；table 也同步显示前 4 个事件
- `relationship` 前端已从 chips 升级为 map。
- `relationship` HTML 图路径已补上 `edges.relation` 文本，不再只显示节点不显示关系词。
- `relationship` HTML 图路径已把关系词从边中点文字改成白底标签，并远离中心节点，避免被中心圆盖住。
- `relationship` 图已进一步拉开几何布局：中心节点下移、上下游节点外扩、关系词沿边法线偏移，避免上半区拥挤。
- `watch_calendar` 已修复两层：
  - `items[].event` 在 skill 层压缩为短标题
  - prompt 已改为“先判断行业，再最多 3 轮 web_search”
  - date contract 已放宽为 `YYYY / YYYY-MM / YYYY-MM-DD`，禁止模型在未知具体日期时默认补月末
  - summary 已改回 Kimi 生成；当前通过 prompt 明确约束时间范围表述，不再由 skill 层拼接
  - `url` 已从 Kimi JSON 生成 contract 中移除，改为仅由 skill 层从 `web_search` tool 证据提取
  - 前端 `watch_calendar` 已新增事件链接图标：事件与 `Set Reminder` 之间显示可点击的 `🔗`
- `watch_calendar` 最新 live 结果已成功，且事件已变成前端可直接显示的短标题。
  - 已验证 partial date 已替代伪造的 `2026-06-30`
  - 已验证模型会返回 `2026年初`、`2026年4月3日`、`2026年中期` 这类自然时间表达
- `entity_info` prompt 已改为按行业切换叙事维度：
  - 高科技/制造/医药/消费/金融分别切不同描述重点
  - 明确禁止空话与伪细节
  - live `debug_entity_info_card.py` 已成功，`entity_info.json/status=valid`
- 已新增单一调试标的配置文件：
  - `config/target_stock.json`
  - 五个单卡脚本已统一读取该文件，不再各自写死 `300750/宁德时代`

## 进行中
- 本机前端验收：`timeline` 图内事件、`relationship` map、`watch_calendar` 精简日历。
- `render.py` 已切到单列移动端 + SVG timeline + HTML relationship graph；需继续做页面级验收，但当前未发现与本地 fixture 链路断开。
- 本机前端验收：`timeline` 图内 marker 与 table 事件数量一致。
- 本机前端验收：`relationship` 图中是否已显示 2-6 字中文关系词。
- 本机前端验收：`relationship` 图中的中文关系词是否不再被中心节点遮挡。
- 本机前端验收：`relationship` 上半区标签是否不再拥挤或压线。
- 本机前端验收：`watch_calendar` 的 `🔗` 图标点击跳转。
- `summary` 单卡 live 收敛。
- 已确认 `summary` 当前仍是纯 AkShare 数值卡，不包含标签 schema；标签职责属于 `entity_info`。
- `watch_calendar` summary 话术与时间范围一致性 live 复核。
- `watch_calendar` summary 仍需再收一轮：当前会把短期事件与全年节点混在一句里。
- `watch_calendar` 真实来源链接仍需再收敛：当前 live `web_search` 证据未提供可复用公开 URL，因此 item.url 为空。
- `timeline` 前端事件数量不一致排查：图内标注与表格当前使用了不同裁剪规则。
- `entity_info` 摘要字数仍可再收紧：当前 live 文案风格已改善，但仍偏长。
- 已完成一次五卡 prompt 审计：当前 drift 主要出现在 `entity_info / relationship / timeline`；`summary/watch_calendar` 未发现同类 contract 回退。
- 后续如果要支持前端切换标的，需要再决定是否让 `app.py` 也读取 `target_stock.json`。

## 下一步（Next Action）
1. 运行 `streamlit run /Users/hujiawei/Documents/PomeFiDemo/app.py`
2. 开启“使用本地 Fixture 调试”
3. 验收：
   - `timeline` 是否正常显示事件标注
   - `timeline` 是否显示全部 4 个事件空心点，hover 才出现事件名
   - `relationship` 是否正常显示 map
   - `watch_calendar` 是否只显示短标题，不再带议案细节
   - `watch_calendar` 每个事件右侧是否有 `🔗`，点击能跳转到对应来源
   - `watch_calendar` summary 是否不再错误写成“未来一个月重点关注...”
   - `timeline` 图内事件数与表格事件数是否已统一
4. 运行 `python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_summary_card.py`
5. 检查新的 `debug_outputs/stock_wiki/summary.json` 是否已变成 `status=valid`

## 剩余边界条件/风险
- 若未开启 fixture 模式，前端仍可能重新触发 live timeout。
- 当前环境下 `streamlit` smoke 自动化仍有跳过，本机手动验收仍是主路径。
- `summary` 仍是当前唯一未完全收敛的单卡。

## 最新验证结果（命令 + 结论）
- 命令:
`sed -n '1,260p' /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/stock_summary.py`
`python - <<'PY' ...读取 debug_outputs/stock_wiki/summary.json ... PY`
- 结论:
  - `summary` 当前后端实现没有 LLM prompt，也没有 `investment_tags/summary_tags`
  - `summary.json` 当前 schema 只有：`metrics/metrics_missing/notes/akshare_calls/data_origin/network_evidence/recovered/unrecovered_reason_code/summary`
  - 之前加标签的是 `entity_info`，不是 `summary`

- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/ui/render.py /Users/hujiawei/Documents/PomeFiDemo/app.py`
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_summary.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_entity.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_relationship.py`
- 结论:
  - `render.py` 当前语法正常，最小渲染回归通过（`6 passed`）
  - `app.py` 仍通过 `debug_outputs/stock_wiki/{summary,entity_info,timeline,watch_calendar,relationship}.json` 组装本地 fixture payload
  - `render.py` 不直接读取 `config/target_stock.json`；该文件只影响五个 debug 脚本产出的 JSON

- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/ui/render.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_relationship.py`
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_relationship.py`
- 结论:
  - 当前页面走的 `relationship` HTML 图路径此前只渲染节点，不渲染 `edges.relation`
  - 已补上 SVG 边与边中点中文关系词
  - 已新增 HTML 字符串级测试锁住关系词渲染（`3 passed`）

- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/ui/render.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_relationship.py`
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_relationship.py`
- 结论:
  - 截图暴露的问题不是无 relation，而是 relation 放在边中点后被中心节点遮挡
  - 现已改成白底关系标签，并把位置偏向非 theme 节点
  - 关系图最小回归仍通过（`3 passed`）

- 命令:
`/Users/hujiawei/Documents/PomeFiDemo/venv/bin/python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_timeline_card.py`
- 结论:
  - live 成功，`timeline.json=status=valid`
  - merged 结果包含事件，`series.event_desc` 已写入

- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/ui/render.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_ui_smoke.py`
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_stock_wiki_ui_smoke.py`
- 结论:
  - 语法通过
  - `timeline` 图表现已去掉默认 annotation，改为 4 个空心点 + hover 文案
  - `timeline` table 现已同步展示前 4 个事件，不再出现图里 2 条、表里 3 条的不一致
  - 当前测试环境无 `streamlit`，因此 UI smoke 被跳过（`1 skipped`）

- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/ui/render.py`
- 结论:
  - 语法通过
  - `timeline` 折线颜色已改为深灰色
  - 事件空心圆点颜色保持不变

- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/watch_calendar.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_watch_calendar_skill.py`
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_watch_calendar_skill.py`
- 结论:
  - 通过（`4 passed`）
  - `watch_calendar` 事件标题已压缩为前端短标题
  - prompt 已切到“行业定向 + 最多 3 轮 web_search”
  - `date` 现支持 `YYYY / YYYY-MM / YYYY-MM-DD`，不会再把 partial date 归一成空字符串
  - `summary` 现由 Kimi 在 JSON 阶段生成；prompt 已明确约束时间范围表述必须与 items 的日期粒度一致

- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/ui/render.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_watch_calendar.py`
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_watch_calendar.py`
- 结论:
  - 语法通过
  - `watch_calendar` 前端已在事件右侧保留 `Set Reminder`，并新增中间的可点击 `🔗` 图标
  - 当前测试环境无 `streamlit`，因此该渲染测试被跳过（`1 skipped`）

- 命令:
`/Users/hujiawei/Documents/PomeFiDemo/venv/bin/python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_watch_calendar_card.py`
- 结论:
  - live 成功，`watch_calendar.json=status=valid`
  - 当前事件为短标题，不再输出股东大会议案细节
  - 未知具体日期时，现已输出自然时间表达，不再统一补成 `2026-06-30`
  - 当前 live 样例包括：`2026年4月3日`、`2026年初`、`2026年底`、`2026年中期`
  - `url` 已不再由模型生成；当前 live 中未提取到可验证公开链接，因此 item.url 为空，前端不应显示 `🔗`

- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/entity_info.py /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_entity_info_card.py`
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_debug_skill.py`
`/Users/hujiawei/Documents/PomeFiDemo/venv/bin/python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_entity_info_card.py`
- 结论:
  - 语法通过，`test_debug_skill.py` 通过（`3 passed`）
  - sandbox 内运行会因 Codex 代理环境返回 `Connection error.`
  - 沙箱外 live 成功，`entity_info` 当前为 `status=valid`
  - 新文案已按行业叙事输出，更接近 Equity Research 风格
  - `investment_tags` 已重新恢复到后端 contract

- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/entity_info.py /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/relationship.py /Users/hujiawei/Documents/PomeFiDemo/pomefi/stock_wiki/skills/timeline.py`
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_debug_skill.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_relationship_loop.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_skills_timeline.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_entity.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_render_relationship.py`
- 结论:
  - 已恢复 `entity_info` 的 `investment_tags` contract
  - 已恢复 `relationship` 的语义化 `edges.relation`
  - 已恢复 `timeline.events[].sentiment`
  - 最小回归通过（`19 passed`）

- 命令:
`/Users/hujiawei/Documents/PomeFiDemo/venv/bin/python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_entity_info_card.py`
`/Users/hujiawei/Documents/PomeFiDemo/venv/bin/python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_relationship_card.py`
`/Users/hujiawei/Documents/PomeFiDemo/venv/bin/python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_timeline_card.py`
`python - <<'PY' ...读取三份最新 JSON ... PY`
- 结论:
  - `entity_info.json` 已重新包含 `investment_tags`
  - `relationship.json` 已重新包含语义化关系边，如“构成成本 / 供应硅料 / 价格竞争 / 驱动盈利 / 加速出清”
  - `timeline.json` 已重新包含 `sentiment`
  - 当前前端已具备消费这三类字段的能力，不存在新的 contract 断裂

- 命令:
`python -m py_compile /Users/hujiawei/Documents/PomeFiDemo/scripts/target_stock.py /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_summary_card.py /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_entity_info_card.py /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_timeline_card.py /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_watch_calendar_card.py /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_relationship_card.py`
`pytest -q /Users/hujiawei/Documents/PomeFiDemo/tests/test_target_stock.py /Users/hujiawei/Documents/PomeFiDemo/tests/test_debug_skill.py`
- 结论:
  - 已新增 `config/target_stock.json`
  - 五个单卡脚本统一读取该文件
  - 最小回归通过（`5 passed`）

## 阻塞项（如有）
- 仍需要重跑 `python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_summary_card.py`，确认 `summary` 是否已恢复为 `valid`
