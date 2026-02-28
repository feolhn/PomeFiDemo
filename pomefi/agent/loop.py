from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path
from typing import Any, Awaitable, Callable

from openai import AsyncOpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)
if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_TEXT)

from pomefi.budgets import BudgetTracker
from pomefi.config import KimiConfig
from pomefi.logging import EventLogger
from pomefi.tools.formula import FormulaToolClient

MAX_COMPLETION_TOKENS = 16000

LocalToolHandler = Callable[[dict[str, Any]], Any | Awaitable[Any]]


def _make_jsonable(value: Any) -> Any:
    try:
        import pandas as pd

        if isinstance(value, pd.DataFrame):
            return value.to_dict(orient="records")
        if isinstance(value, pd.Series):
            return value.to_dict()
    except Exception:
        pass

    if isinstance(value, dict):
        return {key: _make_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_make_jsonable(item) for item in value]
    return value


def _json_string(value: Any) -> str:
    return json.dumps(_make_jsonable(value), ensure_ascii=False)


def _preview_text(value: Any, limit: int = 200) -> str:
    if value is None:
        return ""
    text = value if isinstance(value, str) else _json_string(value)
    return text if len(text) <= limit else f"{text[:limit]}..."


async def _resolve_handler_result(handler: LocalToolHandler, arguments: dict[str, Any]) -> Any:
    result = handler(arguments)
    if inspect.isawaitable(result):
        return await result
    return result


class KimiAgentLoop:
    def __init__(self, *, config: KimiConfig, formula_client: FormulaToolClient):
        self.config = config
        self.formula_client = formula_client
        self.openai = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)

    async def aclose(self) -> None:
        close_method = getattr(self.openai, "close", None)
        if callable(close_method):
            await close_method()

    def _dbg(self, *args: object) -> None:
        if self.config.debug:
            print("[DEBUG]", *args)

    async def run_conversation_trace(
        self,
        *,
        user_prompt: str,
        system_prompt: str,
        local_tools: list[dict[str, Any]] | None = None,
        local_tool_handlers: dict[str, LocalToolHandler] | None = None,
        budget_tracker: BudgetTracker | None = None,
        logger: EventLogger | None = None,
    ) -> dict[str, Any]:
        local_tools = list(local_tools or [])
        local_tool_handlers = dict(local_tool_handlers or {})
        messages: list[Any] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        tools = self.formula_client.remote_tools + local_tools
        trace: dict[str, Any] = {
            "prompt": user_prompt,
            "turns": [],
            "tool_events": [],
            "local_context": {},
            "final_content": "",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "degrade_reason": None,
            "events": [],
        }

        turn_index = 0
        while True:
            if budget_tracker is not None:
                budget_reason = budget_tracker.record_turn()
                if budget_reason:
                    trace["degrade_reason"] = budget_reason
                    if logger is not None:
                        logger.emit("BUDGET_BREAKER", reason=budget_reason, state=budget_tracker.snapshot())
                        trace["events"] = logger.snapshot()
                    return trace
            if logger is not None:
                logger.emit(
                    "LLM_REQUEST",
                    turn_index=turn_index,
                    tool_count=len(tools),
                    message_count=len(messages),
                )
            self._dbg("Sending chat.completions.create ...")
            response = await self.openai.chat.completions.create(
                model=self.config.model,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                temperature=self.config.temperature,
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                stream=False,
            )
            usage_payload = None
            usage_obj = getattr(response, "usage", None)
            if usage_obj is not None:
                usage_payload = usage_obj.model_dump(exclude_none=True)
                for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                    trace["usage"][key] += int(usage_payload.get(key) or 0)
                if budget_tracker is not None:
                    budget_reason = budget_tracker.record_usage(usage_payload)
                    if budget_reason:
                        trace["degrade_reason"] = budget_reason
                        if logger is not None:
                            logger.emit("BUDGET_BREAKER", reason=budget_reason, state=budget_tracker.snapshot())

            message = response.choices[0].message
            tool_calls = list(getattr(message, "tool_calls", None) or [])
            reasoning_content = getattr(message, "reasoning_content", None)
            if logger is not None:
                logger.emit(
                    "LLM_RESPONSE",
                    turn_index=turn_index,
                    has_tool_calls=bool(tool_calls),
                    usage=usage_payload or {},
                )
            turn_entry = {
                "index": turn_index,
                "has_tool_calls": bool(tool_calls),
                "tool_names": [str(call.function.name) for call in tool_calls],
                "reasoning_present": bool(reasoning_content),
                "content_preview": _preview_text(message.content),
            }
            trace["turns"].append(turn_entry)
            self._dbg(
                "Model message received.",
                json.dumps(
                    {
                        "turn_index": turn_index,
                        "has_tool_calls": turn_entry["has_tool_calls"],
                        "tool_names": turn_entry["tool_names"],
                        "reasoning_present": turn_entry["reasoning_present"],
                    },
                    ensure_ascii=False,
                ),
            )

            messages.append(message)

            if not tool_calls:
                trace["final_content"] = str(message.content or "")
                if logger is not None:
                    trace["events"] = logger.snapshot()
                return trace

            for tool_call in tool_calls:
                tool_call_dict = tool_call.model_dump(exclude_none=True)
                function_payload = dict(tool_call_dict.get("function") or {})
                function_name = str(function_payload.get("name") or "")
                arguments_text = function_payload.get("arguments") or "{}"

                if isinstance(arguments_text, str):
                    try:
                        arguments_dict = json.loads(arguments_text)
                    except json.JSONDecodeError:
                        arguments_dict = {}
                elif isinstance(arguments_text, dict):
                    arguments_dict = arguments_text
                    arguments_text = _json_string(arguments_dict)
                    function_payload["arguments"] = arguments_text
                else:
                    arguments_dict = {}
                    arguments_text = "{}"
                    function_payload["arguments"] = arguments_text

                self._dbg(
                    f"Tool call: id={tool_call_dict.get('id')} fn={function_name} args={arguments_dict}"
                )
                if budget_tracker is not None:
                    budget_reason = budget_tracker.record_tool_call(function_name)
                    if budget_reason:
                        trace["degrade_reason"] = budget_reason
                        if logger is not None:
                            logger.emit("BUDGET_BREAKER", reason=budget_reason, state=budget_tracker.snapshot())
                            trace["events"] = logger.snapshot()
                        return trace
                if logger is not None:
                    logger.emit(
                        "RAW_TOOL_REQUEST",
                        tool_name=function_name,
                        tool_call_id=str(tool_call_dict.get("id") or ""),
                        source="local" if function_name in local_tool_handlers else "formula",
                        arguments=arguments_dict if isinstance(arguments_dict, dict) else {},
                    )

                if function_name in local_tool_handlers:
                    local_context: dict[str, Any] | None = None
                    try:
                        result = await _resolve_handler_result(local_tool_handlers[function_name], arguments_dict)
                        if isinstance(result, dict) and result.get("__pomefi_local_tool_result__") is True:
                            local_context = result.get("local_context") if isinstance(result.get("local_context"), dict) else None
                            result = result.get("tool_content")

                        jsonable_result = _make_jsonable(result)
                        try:
                            tool_content = json.dumps(jsonable_result, ensure_ascii=False)
                            jsonable_ok = True
                        except TypeError as exc:
                            jsonable_ok = False
                            if budget_tracker is not None:
                                trace["degrade_reason"] = "parse_error"
                            tool_content = json.dumps(
                                {
                                    "error": f"{function_name} result is not JSON serializable: {exc}",
                                },
                                ensure_ascii=False,
                            )
                    except Exception as exc:
                        jsonable_ok = False
                        if budget_tracker is not None:
                            trace["degrade_reason"] = budget_tracker.note_failure("local")
                        tool_content = json.dumps(
                            {
                                "error": f"Local tool call failed: {exc}",
                            },
                            ensure_ascii=False,
                        )
                    tool_event = {
                        "tool_name": function_name,
                        "tool_call_id": str(tool_call_dict.get("id") or ""),
                        "source": "local",
                        "formula_uri": None,
                        "arguments_text": str(arguments_text),
                        "arguments_dict": arguments_dict if isinstance(arguments_dict, dict) else {},
                        "jsonable_ok": jsonable_ok,
                        "local_context_keys": sorted(local_context.keys()) if local_context else [],
                        "tool_content": tool_content,
                        "tool_content_preview": _preview_text(tool_content),
                    }
                    if local_context is not None:
                        trace["local_context"][tool_event["tool_call_id"]] = local_context
                else:
                    formula_uri = self.formula_client.get_formula_uri(function_name)
                    if not formula_uri:
                        tool_content = json.dumps(
                            {
                                "error": f"No formula uri for tool '{function_name}'.",
                            },
                            ensure_ascii=False,
                        )
                    else:
                        try:
                            remote_result = await self.formula_client.call_tool(formula_uri, function_payload)
                            tool_content = str(remote_result["content"])
                        except Exception as exc:
                            if budget_tracker is not None:
                                trace["degrade_reason"] = budget_tracker.note_failure("formula")
                            tool_content = json.dumps(
                                {"error": f"Remote tool call failed: {exc}"},
                                ensure_ascii=False,
                            )

                    tool_event = {
                        "tool_name": function_name,
                        "tool_call_id": str(tool_call_dict.get("id") or ""),
                        "source": "formula",
                        "formula_uri": formula_uri,
                        "arguments_text": str(arguments_text),
                        "arguments_dict": arguments_dict if isinstance(arguments_dict, dict) else {},
                        "jsonable_ok": None,
                        "local_context_keys": [],
                        "tool_content": tool_content,
                        "tool_content_preview": _preview_text(tool_content),
                    }

                trace["tool_events"].append(tool_event)
                if logger is not None:
                    logger.emit(
                        "RAW_TOOL_RESPONSE",
                        tool_name=function_name,
                        tool_call_id=tool_event["tool_call_id"],
                        source=tool_event["source"],
                        preview=tool_event["tool_content_preview"],
                    )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_event["tool_call_id"],
                        "content": tool_content,
                    }
                )

            turn_index += 1

    async def run_conversation(
        self,
        *,
        user_prompt: str,
        system_prompt: str,
        local_tools: list[dict[str, Any]] | None = None,
        local_tool_handlers: dict[str, LocalToolHandler] | None = None,
        budget_tracker: BudgetTracker | None = None,
        logger: EventLogger | None = None,
    ) -> str:
        trace = await self.run_conversation_trace(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            local_tools=local_tools,
            local_tool_handlers=local_tool_handlers,
            budget_tracker=budget_tracker,
            logger=logger,
        )
        return str(trace["final_content"])
