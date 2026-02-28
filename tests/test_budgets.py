from __future__ import annotations

from pomefi.budgets import BudgetLimits, BudgetTracker


def test_record_web_search_hits_search_budget() -> None:
    tracker = BudgetTracker()

    assert tracker.record_tool_call("web_search") is None
    assert tracker.record_tool_call("web_search") is None
    assert tracker.record_tool_call("web_search") is None
    assert tracker.record_tool_call("web_search") == "search_budget_exceeded"
    assert tracker.snapshot()["degrade_reason"] == "search_budget_exceeded"


def test_record_tool_call_hits_total_tool_budget() -> None:
    tracker = BudgetTracker(limits=BudgetLimits(max_tool_iterations=2))

    assert tracker.record_tool_call("akshare_tool") is None
    assert tracker.record_tool_call("date") is None
    assert tracker.record_tool_call("akshare_tool") == "budget_exceeded"


def test_record_turn_hits_total_turn_budget() -> None:
    tracker = BudgetTracker(limits=BudgetLimits(max_total_turns=1))

    assert tracker.record_turn() is None
    assert tracker.record_turn() == "budget_exceeded"


def test_record_usage_hits_soft_token_budget() -> None:
    tracker = BudgetTracker(limits=BudgetLimits(max_total_tokens_soft=100))

    assert tracker.record_usage({"total_tokens": 60}) is None
    assert tracker.record_usage({"total_tokens": 50}) == "budget_exceeded"


def test_record_retry_hits_retry_budget() -> None:
    tracker = BudgetTracker(limits=BudgetLimits(max_retry_per_failure=1))

    assert tracker.record_retry("formula:web_search") is None
    assert tracker.record_retry("formula:web_search") == "retry_exhausted"


def test_note_failure_returns_specific_reason() -> None:
    formula_tracker = BudgetTracker()
    local_tracker = BudgetTracker()

    assert formula_tracker.note_failure("formula") == "formula_error"
    assert local_tracker.note_failure("local") == "tool_error"


def test_first_degrade_reason_is_sticky() -> None:
    tracker = BudgetTracker(limits=BudgetLimits(max_search_calls=0, max_total_turns=0))

    assert tracker.record_tool_call("web_search") == "search_budget_exceeded"
    assert tracker.record_turn() == "search_budget_exceeded"
    assert tracker.snapshot()["degrade_reason"] == "search_budget_exceeded"
