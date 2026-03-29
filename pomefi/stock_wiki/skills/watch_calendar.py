from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Awaitable, Callable

from pomefi.budgets import BudgetLimits
from pomefi.config import KimiConfig

from .common import classify_error, make_skill_result, parse_formula_content, run_tool_grounded_json_skill

WATCH_CALENDAR_TOOL_SYSTEM_PROMPT = """
你是A股重大事件日历研究助手。
今天是 {today_text}。
必须调用 web_search，再输出证据摘要。
禁止跳过工具调用。
先根据 company_name 判断公司的 1-2 个核心行业/赛道。
行业重大事件定义如下：
- 科技/新能源车：交付数据、新品发布、技术日、电池日、监管准入、产能投放、价格调整
- 生物医药：审批节点、临床数据、医学会议
- 消费/零售：GMV、购物节、同店销售、新店计划
- 半导体/工业：产能投产、大客户订单、行业景气度
- 通用：边际变化、首次披露的财报、回购、指数纳入剔除、解禁
最多调用 3 次 web_search：
1. 行业定向搜索
2. 通用资本市场事件搜索
3. 仅在前两轮证据不足时，补 1 次高价值缺口搜索
禁止重复搜索相同意图。
未来将影响股价的重大事件，优先未来3个月；若存在时间更远但重要的事件，也可保留。
""".strip()

WATCH_CALENDAR_JSON_SYSTEM_PROMPT = """
你是A股日历抽取助手。必须输出 JSON object，不要 markdown。
schema:
{
  "today": "YYYY-MM-DD",
  "summary": "string",
  "items": [
    {
      "date": "string",
      "event": "string",
      "source": "string"
    }
  ]
}
规则：
- 只保留未来事件
- 忽略公司公告噪音（债权与流动性日常维护、合规性流程进度等）
- date 不是格式约束，而是时间表达建议；必须忠实保留证据里的时间粒度，不要强行补全
- 只到年份可写“2026年”，只到年月可写“2026年4月”，只到阶段可写“2026年初/下半年”，明确到日才写具体日期
- 禁止为了凑完整日期而默认补 06-30、12-31、月末或任意某一天
- event 必须是短标题，可以保留关键结果
- source 是四字概括：公司公告、交易所公告、政策文件、行业媒体、机构预期
- summary 只总结最重要的股价影响事件（不超过5个）
- summary 的时间范围表述必须与 items 的日期粒度一致
- 只有当事件确实都在短期内，summary 才能写“未来一个月”或“未来三个月”
- 如果 items 含“2026年”“2026年4月”“2026年初”这类 partial date，summary 不得假装成精确短期日历
""".strip()


def _normalize_date(text: str) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""
    raw = re.sub(r"\s+", "", raw)
    if "年" in raw:
        return raw
    raw = raw.replace("/", "-").replace(".", "-")
    full = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", raw)
    if full:
        y, m, d = full.groups()
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    year_month = re.search(r"(\d{4})-(\d{1,2})(?!-\d)", raw)
    if year_month:
        y, m = year_month.groups()
        return f"{y}-{m.zfill(2)}"
    year_only = re.search(r"\b(\d{4})\b", raw)
    if year_only:
        return year_only.group(1)
    return ""


def _compact_event_text(text: str) -> str:
    event = str(text or "").strip()
    if not event:
        return ""
    event = re.sub(r"[（(].*?[）)]", "", event).strip()
    event = re.sub(r"\s+", " ", event)
    return event


def _normalize_items(items: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in list(items or [])[:8]:
        if not isinstance(item, dict):
            continue
        event = _compact_event_text(str(item.get("event") or ""))
        if not event:
            continue
        normalized.append(
            {
                "date": _normalize_date(str(item.get("date") or "")),
                "event": event,
                "source": str(item.get("source") or "web_search"),
                "url": "",
            }
        )
    return normalized[:5]


def _valid_http_url(text: Any) -> str:
    url = str(text or "").strip()
    return url if re.match(r"^https?://", url, flags=re.IGNORECASE) else ""


def _extract_tool_urls(trace: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for event in list(trace.get("tool_events") or []):
        if not isinstance(event, dict) or str(event.get("tool_name") or "") != "web_search":
            continue
        for row in parse_formula_content(str(event.get("tool_content") or "")):
            if not isinstance(row, dict):
                continue
            url = _valid_http_url(row.get("url"))
            if not url or url in seen:
                continue
            seen.add(url)
            rows.append(
                {
                    "title": str(row.get("title") or row.get("key_claim") or "").strip(),
                    "source": str(row.get("source") or "").strip(),
                    "url": url,
                }
            )
    return rows


def _match_source_url(event_text: str, source_text: str, url_rows: list[dict[str, str]]) -> str:
    best_url = ""
    best_score = 0
    event_text = str(event_text or "").strip()
    source_text = str(source_text or "").strip()
    event_tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", event_text)[:3]
    for row in url_rows:
        title = row.get("title") or ""
        row_source = row.get("source") or ""
        score = 0
        if source_text and (source_text in row_source or source_text in title):
            score += 3
        if event_text and event_text in title:
            score += 2
        if any(token and token in title for token in event_tokens):
            score += 1
        if score > best_score:
            best_score = score
            best_url = row.get("url") or ""
    return best_url if best_score >= 3 else ""


def _attach_item_urls(items: list[dict[str, Any]], trace: dict[str, Any]) -> list[dict[str, Any]]:
    url_rows = _extract_tool_urls(trace)
    if not url_rows:
        return items
    enriched: list[dict[str, Any]] = []
    for item in items:
        row = dict(item)
        row["url"] = _match_source_url(row.get("event"), row.get("source"), url_rows)
        enriched.append(row)
    return enriched


async def get_watch_calendar(
    symbol: str,
    company_name: str,
    *,
    config: KimiConfig,
    formula_client: Any,
    event_handler: Callable[[dict[str, Any]], Any | Awaitable[Any]] | None = None,
) -> dict[str, Any]:
    query_name = company_name or symbol
    today_text = datetime.now().strftime("%Y-%m-%d")
    probe = await run_tool_grounded_json_skill(
        symbol=symbol,
        company_name=query_name,
        config=config,
        formula_client=formula_client,
        tool_system_prompt=WATCH_CALENDAR_TOOL_SYSTEM_PROMPT.format(today_text=today_text),
        tool_user_prompts=[
            (
                f"标的：{query_name}({symbol})。"
                f"今天是 {today_text}。"
                "不要直接回答。按 system prompt 里的行业规则调用 web_search；"
                "query 必须覆盖时间意图词（未来、即将、计划、预计、将于、时间表）和股价影响事件词。"
                "拿到结果后立刻输出简短证据摘要，禁止重复 query。"
            ),
            (
                f"标的：{query_name}({symbol})。"
                f"今天是 {today_text}。"
                "不要直接回答。必须先调用 web_search，再输出不超过120字的证据摘要。"
                "若未调用工具，或 web_search 超过 3 次，或重复搜索相同意图，本轮视为失败。"
            ),
        ],
        json_system_prompt=WATCH_CALENDAR_JSON_SYSTEM_PROMPT,
        json_user_prompt_builder=lambda evidence_text, _trace: (
            f"标的：{query_name}({symbol})。"
            f"今天是 {today_text}。"
            "基于下列 tool-grounded 证据摘要，抽取未来将影响股价的重大事件 JSON。"
            "优先未来90天；若存在更远但已明确公告的重要事件，也可保留。\n"
            "date 按证据原样保留时间粒度，不要补默认日期；summary 必须与 items 的真实日期粒度一致，禁止把 partial date 事件写成“未来一个月”。\n"
            "source 只能从固定集合中选，不能自由命名。\n"
            f"{evidence_text}"
        ),
        event_scope="watch_calendar",
        required_tools={"web_search"},
        event_handler=event_handler,
        disable_tool_thinking=True,
        tool_budget_limits=BudgetLimits(
            max_search_calls=3,
            max_tool_iterations=6,
            max_total_turns=6,
        ),
        json_max_completion_tokens=1536,
    )
    return _watch_calendar_from_probe(
        probe=probe,
        symbol=symbol,
        company_name=company_name,
        today_text=today_text,
    )


def _watch_calendar_from_probe(
    *,
    probe: dict[str, Any],
    symbol: str,
    company_name: str,
    today_text: str,
) -> dict[str, Any]:
    trace = dict(probe.get("tool_trace") or {})
    trace_payload = {
        "tool_call_required": True,
        "tool_call_observed": bool(probe.get("tool_call_observed")),
        "retry_count": int(probe.get("retry_count") or 0),
        "observed_tools": list(probe.get("observed_tools") or []),
        "turns": list(trace.get("turns") or []),
        "tool_events": list(trace.get("tool_events") or []),
        "degrade_reason": trace.get("degrade_reason"),
    }
    sources = [dict(item) for item in list(probe.get("sources") or []) if isinstance(item, dict)]

    if probe.get("error"):
        return make_skill_result(
            status="degraded",
            data={
                "symbol": symbol,
                "company_name": company_name,
                "today": today_text,
                "items": [],
                "summary": "暂未抓到可靠的近期节点。",
                "trace": trace_payload,
            },
            sources=sources,
            error=str(probe.get("error") or "watch_calendar_tool_grounding_failed"),
            error_category=classify_error(str(probe.get("error") or "")),
            data_ready=False,
            is_critical=False,
        )

    payload = dict(probe.get("content_json") or {})
    items = _attach_item_urls(_normalize_items(payload.get("items")), trace)
    payload_today_text = _normalize_date(str(payload.get("today") or "")) or today_text
    summary_text = str(payload.get("summary") or "").strip()
    if not summary_text:
        summary_text = "已提取未来将影响股价的重大事件。"
    if not items:
        summary_text = "暂未抓到可靠的近期节点。"

    return make_skill_result(
        status="valid" if items else "degraded",
        data={
            "symbol": symbol,
            "company_name": company_name,
            "today": payload_today_text,
            "items": items,
            "summary": summary_text,
            "trace": trace_payload,
        },
        sources=sources,
        error=None if items else "calendar_empty",
        error_category=None if items else "empty",
        data_ready=bool(items),
        is_critical=False,
    )
