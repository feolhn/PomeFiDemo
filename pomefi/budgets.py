from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pomefi.protocol import DEGRADE_REASONS

# 这是软熔断层。
# 它只负责预算状态，不负责调度或 tool 选择。


@dataclass(frozen=True)
class BudgetLimits:
    max_search_calls: int = 3
    max_retry_per_failure: int = 1
    max_tool_iterations: int = 6
    max_total_turns: int = 8
    max_completion_tokens_per_call: int = 16000
    max_total_cost_rmb: float = 1.0
    max_total_tokens_soft: int = 24000


@dataclass
class BudgetState:
    search_calls: int = 0
    retry_counts: dict[str, int] = field(default_factory=dict)
    tool_iterations: int = 0
    total_turns: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_rmb: float = 0.0
    degrade_reason: str | None = None


class BudgetTracker:
    # BudgetTracker 统一累计 search/tool/turn/token/cost。
    # budget 触发后，上层应转降级，而不是继续盲跑。
    def __init__(self, limits: BudgetLimits | None = None):
        self.limits = limits or BudgetLimits()
        self.state = BudgetState()

    def _set_degrade_reason(self, reason: str) -> str:
        if reason not in DEGRADE_REASONS:
            raise ValueError(f"Unsupported degrade reason: {reason}")
        if self.state.degrade_reason is None:
            self.state.degrade_reason = reason
        return self.state.degrade_reason

    def record_turn(self) -> str | None:
        self.state.total_turns += 1
        if self.state.total_turns > self.limits.max_total_turns:
            return self._set_degrade_reason("budget_exceeded")
        return None

    def record_tool_call(self, tool_name: str) -> str | None:
        self.state.tool_iterations += 1
        if str(tool_name) == "web_search":
            self.state.search_calls += 1
            if self.state.search_calls > self.limits.max_search_calls:
                return self._set_degrade_reason("search_budget_exceeded")
        if self.state.tool_iterations > self.limits.max_tool_iterations:
            return self._set_degrade_reason("budget_exceeded")
        return None

    def record_retry(self, failure_key: str) -> str | None:
        key = str(failure_key or "unknown")
        self.state.retry_counts[key] = self.state.retry_counts.get(key, 0) + 1
        if self.state.retry_counts[key] > self.limits.max_retry_per_failure:
            return self._set_degrade_reason("retry_exhausted")
        return None

    def record_usage(self, usage: dict[str, Any] | None = None, *, estimated_cost_rmb: float = 0.0) -> str | None:
        usage = dict(usage or {})
        self.state.prompt_tokens += int(usage.get("prompt_tokens") or 0)
        self.state.completion_tokens += int(usage.get("completion_tokens") or 0)
        self.state.total_tokens += int(usage.get("total_tokens") or 0)
        self.state.total_cost_rmb += float(estimated_cost_rmb or 0.0)
        if self.state.total_tokens > self.limits.max_total_tokens_soft:
            return self._set_degrade_reason("budget_exceeded")
        if self.state.total_cost_rmb > self.limits.max_total_cost_rmb:
            return self._set_degrade_reason("budget_exceeded")
        return None

    def note_failure(self, source: str) -> str:
        source_text = str(source or "").strip().lower()
        if source_text == "formula":
            return self._set_degrade_reason("formula_error")
        return self._set_degrade_reason("tool_error")

    def note_no_progress(self) -> str:
        return self._set_degrade_reason("no_message_progress")

    def snapshot(self) -> dict[str, Any]:
        return {
            "search_calls": self.state.search_calls,
            "retry_counts": dict(self.state.retry_counts),
            "tool_iterations": self.state.tool_iterations,
            "total_turns": self.state.total_turns,
            "prompt_tokens": self.state.prompt_tokens,
            "completion_tokens": self.state.completion_tokens,
            "total_tokens": self.state.total_tokens,
            "total_cost_rmb": self.state.total_cost_rmb,
            "degrade_reason": self.state.degrade_reason,
        }
