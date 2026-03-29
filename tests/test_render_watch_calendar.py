from __future__ import annotations

import pytest

pytest.importorskip("streamlit")
from pomefi.ui.render import _watch_calendar_actions_html


def test_watch_calendar_actions_html_includes_link_when_url_present() -> None:
    html = _watch_calendar_actions_html("https://example.com/event")
    assert "href='https://example.com/event'" in html
    assert "🔗" in html
    assert "Set Reminder" in html


def test_watch_calendar_actions_html_keeps_reminder_when_url_missing() -> None:
    html = _watch_calendar_actions_html("")
    assert "href=" not in html
    assert "Set Reminder" in html
