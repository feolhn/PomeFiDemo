from __future__ import annotations

from pomefi.stock_wiki.skills.watch_calendar import (
    _attach_item_urls,
    _compact_event_text,
    _normalize_date,
    _normalize_items,
)


def test_compact_event_text_strips_detail_suffix() -> None:
    text = "2025年度股东大会（日期待定，预计4月18日前召开）：审议2025年年报、利润分配预案等17项议案"
    assert _compact_event_text(text) == "2025年度股东大会：审议2025年年报、利润分配预案等17项议案"


def test_normalize_items_keeps_compact_event_only() -> None:
    items = _normalize_items(
        [
            {
                "date": "2026-04-18",
                "event": "2025年度股东大会（日期待定）：审议年报和分红预案",
                "source": "公告",
            }
        ]
    )
    assert items[0]["event"] == "2025年度股东大会：审议年报和分红预案"
    assert "certainty" not in items[0]


def test_compact_event_text_keeps_key_result_phrase() -> None:
    text = "2026年一季报披露：预计扭亏为盈"
    assert _compact_event_text(text) == "2026年一季报披露：预计扭亏为盈"


def test_normalize_date_keeps_year_month_without_fake_day() -> None:
    assert _normalize_date("2026-06") == "2026-06"


def test_normalize_date_keeps_year_only_without_fake_month_day() -> None:
    assert _normalize_date("2027") == "2027"


def test_attach_item_urls_uses_tool_evidence_only() -> None:
    items = [
        {
            "date": "2026年4月3日",
            "event": "2025年度股东大会召开",
            "source": "宁德时代公告",
            "url": "",
        }
    ]
    trace = {
        "tool_events": [
            {
                "tool_name": "web_search",
                "tool_content": """
                [
                  {
                    "title": "宁德时代：2025年度股东大会通知",
                    "source": "宁德时代公告",
                    "url": "https://www.cninfo.com.cn/example"
                  }
                ]
                """,
            }
        ]
    }
    enriched = _attach_item_urls(items, trace)
    assert enriched[0]["url"] == "https://www.cninfo.com.cn/example"
