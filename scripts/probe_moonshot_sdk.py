from __future__ import annotations

import asyncio
from pathlib import Path
import sys
from typing import Any

import akshare as ak

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)
if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_TEXT)

from pomefi.agent.loop import KimiAgentLoop
from pomefi.config import print_probe_env_summary, validate_probe_env_or_raise
from pomefi.tools.formula import FormulaToolClient

FORMULA_URIS = [
    "moonshot/date:latest",
    "moonshot/web-search:latest",
]

SYSTEM_PROMPT = "You are a helpful assistant."
OFFICIAL_TOOL_PROMPT = (
    "不要直接回答。必须先调用 date 获取今天日期，再调用 web_search 搜索今天最重要的一条 AI 新闻，"
    "最后用两句话总结，并在回答中包含日期。"
)
COMPANY_INFO_PROMPT = "不要直接回答。必须调用 company_info 工具查询 300750 的公司名，再用一句话总结它是什么公司。"

EXIT_OK = 0
EXIT_ENV_FAIL = 2
EXIT_OFFICIAL_TOOL_FAIL = 3
EXIT_COMPANY_INFO_FAIL = 4
EXIT_UNCLASSIFIED_FAIL = 5


def preview_text(value: Any, limit: int = 200) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= limit else f"{text[:limit]}..."


def build_company_info_tool() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "company_info",
            "description": "查询A股公司基本信息（本地 AkShare）。参数: stock_code (字符串，如 300750)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "stock_code": {"type": "string", "description": "A股代码，如 300750"},
                },
                "required": ["stock_code"],
            },
        },
    }


def get_company_info(arguments: dict[str, Any]) -> dict[str, Any]:
    stock_code = str(arguments.get("stock_code", ""))
    try:
        stock_info = ak.stock_info_a_code_name()
        company_row = stock_info[stock_info["code"] == stock_code]
        if company_row.empty:
            return {"error": f"未找到股票代码 {stock_code} 的基本信息"}

        company_name = company_row["name"].values[0]
        company_profile: Any = None
        try:
            company_profile = ak.stock_profile_cninfo(symbol=stock_code)
        except Exception as exc:
            company_profile = {"warning": f"stock_profile_cninfo failed: {exc}"}

        return {
            "stock_code": stock_code,
            "company_name": company_name,
            "company_profile": company_profile,
        }
    except Exception as exc:
        return {"error": str(exc)}


async def run_probe_case(
    agent: KimiAgentLoop,
    *,
    check_index: int,
    check_name: str,
    prompt: str,
    expected_tools: set[str],
    local_tools: list[dict[str, Any]] | None = None,
    local_tool_handlers: dict[str, Any] | None = None,
    allowed_formula_uris: set[str] | None = None,
) -> dict[str, Any]:
    trace = await agent.run_conversation_trace(
        user_prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        local_tools=local_tools,
        local_tool_handlers=local_tool_handlers,
    )
    turns = list(trace.get("turns") or [])
    tool_events = list(trace.get("tool_events") or [])
    final_content = str(trace.get("final_content") or "").strip()

    if not turns:
        raise RuntimeError("No model turns were recorded.")

    first_turn = turns[0]
    if not bool(first_turn.get("has_tool_calls")):
        raise RuntimeError("First response did not include tool_calls.")

    if len(turns) < 2:
        raise RuntimeError("Expected at least two turns for tool loop completion.")

    observed_tools = {str(event.get("tool_name") or "") for event in tool_events}
    missing_tools = expected_tools - observed_tools
    if missing_tools:
        raise RuntimeError(f"Missing expected tools: {sorted(missing_tools)}")

    if allowed_formula_uris is not None:
        formula_uris = {
            str(event.get("formula_uri"))
            for event in tool_events
            if event.get("source") == "formula" and event.get("formula_uri")
        }
        invalid_uris = formula_uris - allowed_formula_uris
        if invalid_uris:
            raise RuntimeError(f"Unexpected formula URIs used: {sorted(invalid_uris)}")

    if "company_info" in expected_tools:
        local_events = [
            event for event in tool_events if str(event.get("tool_name") or "") == "company_info"
        ]
        if not local_events:
            raise RuntimeError("company_info was not executed.")
        if not all(event.get("jsonable_ok") is True for event in local_events):
            raise RuntimeError("company_info result was not JSON serializable.")

    if not final_content:
        raise RuntimeError("Final assistant content is empty.")

    print(f"[CHECK {check_index}/3] {check_name}: PASS")
    return trace


async def main() -> int:
    try:
        config = validate_probe_env_or_raise()
    except Exception as exc:
        print(f"[CHECK 1/3] ENV_CHECK: FAIL - {exc}")
        print("[SUMMARY] all_checks_passed=false")
        return EXIT_ENV_FAIL

    print_probe_env_summary(config)
    print("[CHECK 1/3] ENV_CHECK: PASS")

    formula_client: FormulaToolClient | None = None
    agent: KimiAgentLoop | None = None
    company_info_tool = build_company_info_tool()
    try:
        formula_client = FormulaToolClient(base_url=config.base_url, api_key=config.api_key)
        try:
            await formula_client.load_tools(FORMULA_URIS)
        except Exception as exc:
            print(f"[CHECK 2/3] OFFICIAL_TOOL_LOOP: FAIL - {exc}")
            print("[SUMMARY] all_checks_passed=false")
            return EXIT_OFFICIAL_TOOL_FAIL

        agent = KimiAgentLoop(config=config, formula_client=formula_client)

        try:
            official_trace = await run_probe_case(
                agent,
                check_index=2,
                check_name="OFFICIAL_TOOL_LOOP",
                prompt=OFFICIAL_TOOL_PROMPT,
                expected_tools={"date", "web_search"},
                allowed_formula_uris=set(FORMULA_URIS),
            )
            if config.debug:
                print("[DEBUG] Official tool final content:", preview_text(official_trace["final_content"]))
        except Exception as exc:
            print(f"[CHECK 2/3] OFFICIAL_TOOL_LOOP: FAIL - {exc}")
            print("[SUMMARY] all_checks_passed=false")
            return EXIT_OFFICIAL_TOOL_FAIL

        try:
            company_trace = await run_probe_case(
                agent,
                check_index=3,
                check_name="COMPANY_INFO_LOOP",
                prompt=COMPANY_INFO_PROMPT,
                expected_tools={"company_info"},
                local_tools=[company_info_tool],
                local_tool_handlers={"company_info": get_company_info},
            )
            if config.debug:
                print("[DEBUG] Company info final content:", preview_text(company_trace["final_content"]))
        except Exception as exc:
            print(f"[CHECK 3/3] COMPANY_INFO_LOOP: FAIL - {exc}")
            print("[SUMMARY] all_checks_passed=false")
            return EXIT_COMPANY_INFO_FAIL
    except Exception as exc:
        print(f"[ERROR] Unexpected failure: {exc}")
        print("[SUMMARY] all_checks_passed=false")
        return EXIT_UNCLASSIFIED_FAIL
    finally:
        if agent is not None:
            await agent.aclose()
        if formula_client is not None:
            await formula_client.aclose()

    print("[SUMMARY] all_checks_passed=true")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
