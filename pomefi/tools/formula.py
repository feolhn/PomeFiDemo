from __future__ import annotations

import json
from typing import Any

import httpx

# 这是 Moonshot Formula 协议适配层。
# 它只负责 remote tools 发现和 fiber 调用。
# 这里不做业务判断，也不做结果装配。


def _json_string(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


class FormulaToolClient:
    def __init__(self, *, base_url: str, api_key: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.http = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=timeout,
        )
        self._remote_tools: list[dict[str, Any]] = []
        self._tool_to_uri: dict[str, str] = {}

    @property
    def remote_tools(self) -> list[dict[str, Any]]:
        return list(self._remote_tools)

    @property
    def tool_to_uri(self) -> dict[str, str]:
        return dict(self._tool_to_uri)

    async def aclose(self) -> None:
        await self.http.aclose()

    async def load_tools(self, formula_uris: list[str]) -> list[dict[str, Any]]:
        # 这里建立 tool_name -> formula_uri 映射。
        # 这是 remote tool 注册入口，供 tool loop 后续分发使用。
        tools: list[dict[str, Any]] = []
        tool_to_uri: dict[str, str] = {}

        for uri in formula_uris:
            response = await self.http.get(f"/formulas/{uri}/tools")
            response.raise_for_status()
            payload = response.json()
            uri_tools = payload.get("tools", payload)
            if not isinstance(uri_tools, list):
                raise RuntimeError(f"Unexpected tools payload for {uri}: {payload}")

            for tool in uri_tools:
                tools.append(tool)
                if isinstance(tool, dict) and tool.get("type") == "function":
                    function_name = (tool.get("function") or {}).get("name")
                    if function_name:
                        tool_to_uri[str(function_name)] = uri

        self._remote_tools = tools
        self._tool_to_uri = tool_to_uri
        return self.remote_tools

    def get_formula_uri(self, tool_name: str) -> str | None:
        return self._tool_to_uri.get(tool_name)

    async def call_tool(self, formula_uri: str, function_payload: dict[str, Any]) -> dict[str, Any]:
        # 这里必须保持官方 Formula body 格式。
        # arguments 必须是 JSON string，不要回写成 dict 继续下传。
        function_name = str(function_payload.get("name") or "")
        arguments_text = function_payload.get("arguments") or "{}"
        if not isinstance(arguments_text, str):
            arguments_text = _json_string(arguments_text)

        body = {
            "name": function_name,
            "arguments": arguments_text,
        }
        response = await self.http.post(f"/formulas/{formula_uri}/fibers", json=body)
        response.raise_for_status()
        fiber = response.json()
        context = fiber.get("context") if isinstance(fiber, dict) else {}
        context = context if isinstance(context, dict) else {}
        content = context.get("output") or context.get("encrypted_output")

        if content is None:
            content = _json_string(
                {
                    "error": fiber.get("error") or context.get("error") or "Formula tool returned no output.",
                    "fiber_status": fiber.get("status"),
                }
            )
        elif not isinstance(content, str):
            content = _json_string(content)

        return {"fiber": fiber, "content": content}
