from __future__ import annotations

import inspect
import json
import sys
from collections.abc import AsyncIterator
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
from pomefi.streaming.collector import collect_stream_events
from pomefi.streaming.events import (
    EVENT_LLM_CONTENT_DELTA,
    EVENT_LLM_REASONING_DELTA,
    EVENT_SESSION_DONE,
    EVENT_SESSION_ERROR,
    EVENT_SESSION_START,
    EVENT_TOOL_CALL,
    EVENT_TOOL_RESULT,
    make_event,
)
from pomefi.tools.formula import FormulaToolClient

# 这是项目的 tool loop 内核。
# 它统一处理 assistant / tool 多轮往返，并生成 trace。
# assistant message 回填必须保留 reasoning_content。

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


def _new_tool_call_slot() -> dict[str, Any]:
    return {
        "id": "",
        "type": "function",
        "function": {"name": "", "arguments": ""},
    }


def _normalize_arguments_text(arguments_raw: Any) -> tuple[str, dict[str, Any]]:
    if isinstance(arguments_raw, str):
        arguments_text = arguments_raw
    elif isinstance(arguments_raw, dict):
        arguments_text = _json_string(arguments_raw)
    else:
        arguments_text = "{}"

    try:
        arguments_dict = json.loads(arguments_text)
    except json.JSONDecodeError:
        arguments_dict = {}
    if not isinstance(arguments_dict, dict):
        arguments_dict = {}
    return arguments_text, arguments_dict


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

    async def run_conversation_trace_stream(
        self,
        *,
        user_prompt: str,
        system_prompt: str,
        response_format: dict[str, str] | None = None,
        local_tools: list[dict[str, Any]] | None = None,
        local_tool_handlers: dict[str, LocalToolHandler] | None = None,
        budget_tracker: BudgetTracker | None = None,
        logger: EventLogger | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        # 这是核心执行循环。
        # trace 是 assembler / debug 的事实来源。
        # local tool 和 Formula tool 都从这里统一分发。
        local_tools = list(local_tools or [])
        local_tool_handlers = dict(local_tool_handlers or {})
        messages: list[dict[str, Any]] = [
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

        yield make_event(
            EVENT_SESSION_START,
            prompt=user_prompt,
            model=self.config.model,
            tool_count=len(tools),
        )

        turn_index = 0
        try:
            while True:
                if budget_tracker is not None:
                    budget_reason = budget_tracker.record_turn()
                    if budget_reason:
                        trace["degrade_reason"] = budget_reason
                        if logger is not None:
                            logger.emit("BUDGET_BREAKER", reason=budget_reason, state=budget_tracker.snapshot())
                            trace["events"] = logger.snapshot()
                        yield make_event(EVENT_SESSION_DONE, trace=trace)
                        return

                if logger is not None:
                    logger.emit(
                        "LLM_REQUEST",
                        turn_index=turn_index,
                        tool_count=len(tools),
                        message_count=len(messages),
                    )

                self._dbg("Sending chat.completions.create stream=True ...")
                request_payload: dict[str, Any] = {
                    "model": self.config.model,
                    "messages": messages,
                    "tools": tools if tools else None,
                    "tool_choice": "auto" if tools else None,
                    "temperature": self.config.temperature,
                    "max_completion_tokens": MAX_COMPLETION_TOKENS,
                    "stream": True,
                    "stream_options": {"include_usage": True},
                }
                if response_format is not None:
                    request_payload["response_format"] = response_format

                stream = await self.openai.chat.completions.create(**request_payload)

                assistant_role = "assistant"
                content_chunks: list[str] = []
                reasoning_chunks: list[str] = []
                tool_calls_payload: list[dict[str, Any]] = []
                usage_payload: dict[str, Any] | None = None

                async for chunk in stream:
                    chunk_usage = getattr(chunk, "usage", None)
                    if chunk_usage is not None:
                        dump = getattr(chunk_usage, "model_dump", None)
                        if callable(dump):
                            usage_payload = dump(exclude_none=True)

                    choices = list(getattr(chunk, "choices", None) or [])
                    if not choices:
                        continue
                    choice = choices[0]
                    delta = getattr(choice, "delta", None)
                    if delta is None:
                        continue

                    role_delta = getattr(delta, "role", None)
                    if role_delta:
                        assistant_role = str(role_delta)

                    reasoning_delta = getattr(delta, "reasoning_content", None)
                    if reasoning_delta:
                        reasoning_piece = str(reasoning_delta)
                        reasoning_chunks.append(reasoning_piece)
                        yield make_event(
                            EVENT_LLM_REASONING_DELTA,
                            turn_index=turn_index,
                            delta=reasoning_piece,
                        )

                    content_delta = getattr(delta, "content", None)
                    if content_delta:
                        content_piece = str(content_delta)
                        content_chunks.append(content_piece)
                        yield make_event(
                            EVENT_LLM_CONTENT_DELTA,
                            turn_index=turn_index,
                            delta=content_piece,
                        )

                    delta_tool_calls = list(getattr(delta, "tool_calls", None) or [])
                    for delta_call in delta_tool_calls:
                        call_index = int(getattr(delta_call, "index", 0) or 0)
                        while len(tool_calls_payload) <= call_index:
                            tool_calls_payload.append(_new_tool_call_slot())
                        tool_call_object = tool_calls_payload[call_index]

                        call_id = getattr(delta_call, "id", None)
                        if call_id:
                            tool_call_object["id"] = str(call_id)
                        call_type = getattr(delta_call, "type", None)
                        if call_type:
                            tool_call_object["type"] = str(call_type)

                        delta_function = getattr(delta_call, "function", None)
                        if delta_function is not None:
                            fn_name = getattr(delta_function, "name", None)
                            if fn_name:
                                tool_call_object["function"]["name"] = str(fn_name)
                            fn_arguments = getattr(delta_function, "arguments", None)
                            if isinstance(fn_arguments, str):
                                tool_call_object["function"]["arguments"] += fn_arguments

                if usage_payload:
                    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                        trace["usage"][key] += int(usage_payload.get(key) or 0)
                    if budget_tracker is not None:
                        budget_reason = budget_tracker.record_usage(usage_payload)
                        if budget_reason:
                            trace["degrade_reason"] = budget_reason
                            if logger is not None:
                                logger.emit("BUDGET_BREAKER", reason=budget_reason, state=budget_tracker.snapshot())
                                trace["events"] = logger.snapshot()
                            yield make_event(EVENT_SESSION_DONE, trace=trace)
                            return

                final_content = "".join(content_chunks)
                final_reasoning = "".join(reasoning_chunks)
                final_tool_calls = [
                    call
                    for call in tool_calls_payload
                    if (call.get("id") or (call.get("function") or {}).get("name"))
                ]
                tool_names = [
                    str((call.get("function") or {}).get("name") or "")
                    for call in final_tool_calls
                    if str((call.get("function") or {}).get("name") or "")
                ]

                turn_entry = {
                    "index": turn_index,
                    "has_tool_calls": bool(final_tool_calls),
                    "tool_names": tool_names,
                    "reasoning_present": bool(final_reasoning),
                    "content_preview": _preview_text(final_content),
                }
                trace["turns"].append(turn_entry)
                if logger is not None:
                    logger.emit(
                        "LLM_RESPONSE",
                        turn_index=turn_index,
                        has_tool_calls=bool(final_tool_calls),
                        usage=usage_payload or {},
                    )

                assistant_message: dict[str, Any] = {"role": assistant_role, "content": final_content}
                if final_reasoning:
                    assistant_message["reasoning_content"] = final_reasoning
                if final_tool_calls:
                    assistant_message["tool_calls"] = final_tool_calls

                # 这里是上下文硬约束：assistant message 必须完整回填。
                messages.append(assistant_message)

                if not final_tool_calls:
                    trace["final_content"] = final_content
                    if logger is not None:
                        trace["events"] = logger.snapshot()
                    yield make_event(EVENT_SESSION_DONE, trace=trace)
                    return

                for tool_idx, tool_call in enumerate(final_tool_calls):
                    function_payload = dict(tool_call.get("function") or {})
                    function_name = str(function_payload.get("name") or "")
                    arguments_text, arguments_dict = _normalize_arguments_text(function_payload.get("arguments"))
                    function_payload["arguments"] = arguments_text

                    tool_call_id = str(tool_call.get("id") or f"call_{turn_index}_{tool_idx}")
                    source = "local" if function_name in local_tool_handlers else "formula"

                    if budget_tracker is not None:
                        budget_reason = budget_tracker.record_tool_call(function_name)
                        if budget_reason:
                            trace["degrade_reason"] = budget_reason
                            if logger is not None:
                                logger.emit("BUDGET_BREAKER", reason=budget_reason, state=budget_tracker.snapshot())
                                trace["events"] = logger.snapshot()
                            yield make_event(EVENT_SESSION_DONE, trace=trace)
                            return

                    if logger is not None:
                        logger.emit(
                            "RAW_TOOL_REQUEST",
                            tool_name=function_name,
                            tool_call_id=tool_call_id,
                            source=source,
                            arguments=arguments_dict,
                        )

                    yield make_event(
                        EVENT_TOOL_CALL,
                        turn_index=turn_index,
                        tool_name=function_name,
                        tool_call_id=tool_call_id,
                        source=source,
                        arguments_text=arguments_text,
                        arguments=arguments_dict,
                    )

                    local_context: dict[str, Any] | None = None
                    formula_uri: str | None = None
                    jsonable_ok: bool | None = None
                    tool_content = ""

                    if function_name in local_tool_handlers:
                        # __pomefi_local_tool_result__ 是 local hook 协议。
                        # 只把 tool_content 回给 LLM，local_context 留本地。
                        try:
                            result = await _resolve_handler_result(local_tool_handlers[function_name], arguments_dict)
                            if isinstance(result, dict) and result.get("__pomefi_local_tool_result__") is True:
                                maybe_context = result.get("local_context")
                                if isinstance(maybe_context, dict):
                                    local_context = maybe_context
                                result = result.get("tool_content")

                            jsonable_result = _make_jsonable(result)
                            tool_content = json.dumps(jsonable_result, ensure_ascii=False)
                            jsonable_ok = True
                        except Exception as exc:
                            jsonable_ok = False
                            if budget_tracker is not None:
                                trace["degrade_reason"] = budget_tracker.note_failure("local")
                            tool_content = json.dumps(
                                {"error": f"Local tool call failed: {exc}"},
                                ensure_ascii=False,
                            )
                    else:
                        # date / web_search 必须走 Formula，不允许本地替代。
                        formula_uri = self.formula_client.get_formula_uri(function_name)
                        if not formula_uri:
                            tool_content = json.dumps(
                                {"error": f"No formula uri for tool '{function_name}'."},
                                ensure_ascii=False,
                            )
                        else:
                            try:
                                remote_result = await self.formula_client.call_tool(formula_uri, function_payload)
                                tool_content = str(remote_result.get("content") or "")
                            except Exception as exc:
                                if budget_tracker is not None:
                                    trace["degrade_reason"] = budget_tracker.note_failure("formula")
                                tool_content = json.dumps(
                                    {"error": f"Remote tool call failed: {exc}"},
                                    ensure_ascii=False,
                                )

                    tool_event = {
                        "tool_name": function_name,
                        "tool_call_id": tool_call_id,
                        "source": source,
                        "formula_uri": formula_uri,
                        "arguments_text": arguments_text,
                        "arguments_dict": arguments_dict,
                        "jsonable_ok": jsonable_ok,
                        "local_context_keys": sorted(local_context.keys()) if local_context else [],
                        "tool_content": tool_content,
                        "tool_content_preview": _preview_text(tool_content),
                    }
                    trace["tool_events"].append(tool_event)
                    if local_context is not None:
                        trace["local_context"][tool_call_id] = local_context

                    if logger is not None:
                        logger.emit(
                            "RAW_TOOL_RESPONSE",
                            tool_name=function_name,
                            tool_call_id=tool_call_id,
                            source=source,
                            preview=tool_event["tool_content_preview"],
                        )

                    yield make_event(
                        EVENT_TOOL_RESULT,
                        turn_index=turn_index,
                        tool_name=function_name,
                        tool_call_id=tool_call_id,
                        source=source,
                        formula_uri=formula_uri,
                        content_preview=tool_event["tool_content_preview"],
                        jsonable_ok=jsonable_ok,
                        local_context_keys=tool_event["local_context_keys"],
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": tool_content,
                        }
                    )

                turn_index += 1
        except Exception as exc:
            trace["degrade_reason"] = trace.get("degrade_reason") or "loop_exception"
            if logger is not None:
                logger.emit("LOOP_EXCEPTION", error=str(exc))
                trace["events"] = logger.snapshot()
            yield make_event(
                EVENT_SESSION_ERROR,
                error=str(exc),
                trace=trace,
            )
            raise

    async def run_conversation_trace(
        self,
        *,
        user_prompt: str,
        system_prompt: str,
        response_format: dict[str, str] | None = None,
        local_tools: list[dict[str, Any]] | None = None,
        local_tool_handlers: dict[str, LocalToolHandler] | None = None,
        budget_tracker: BudgetTracker | None = None,
        logger: EventLogger | None = None,
    ) -> dict[str, Any]:
        event_stream = self.run_conversation_trace_stream(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            response_format=response_format,
            local_tools=local_tools,
            local_tool_handlers=local_tool_handlers,
            budget_tracker=budget_tracker,
            logger=logger,
        )
        _, final_trace = await collect_stream_events(event_stream)
        if final_trace is None:
            raise RuntimeError("run_conversation_trace_stream completed without session_done.")
        return final_trace

    async def run_conversation(
        self,
        *,
        user_prompt: str,
        system_prompt: str,
        response_format: dict[str, str] | None = None,
        local_tools: list[dict[str, Any]] | None = None,
        local_tool_handlers: dict[str, LocalToolHandler] | None = None,
        budget_tracker: BudgetTracker | None = None,
        logger: EventLogger | None = None,
    ) -> str:
        # 这是 trace -> final_content 的薄封装。
        trace = await self.run_conversation_trace(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            response_format=response_format,
            local_tools=local_tools,
            local_tool_handlers=local_tool_handlers,
            budget_tracker=budget_tracker,
            logger=logger,
        )
        return str(trace["final_content"])
