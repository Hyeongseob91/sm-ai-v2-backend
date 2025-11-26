import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model
from typing import Any, Dict, List, Type, Optional


def json_schema_to_pydantic(name: str, json_schema: Dict[str, Any]) -> Type[BaseModel]:
    """MCP의 JSON Schema를 Pydantic BaseModel로 변환

    Args:
        name: 도구 이름 (Pydantic 모델 클래스 이름에 사용)
        json_schema: MCP tool_info.inputSchema에서 가져온 JSON Schema

    Returns:
        동적으로 생성된 Pydantic BaseModel 클래스
    """
    if not json_schema or json_schema.get("type") != "object":
        # 빈 스키마인 경우 빈 모델 반환
        return create_model(f"{name}Input")

    properties = json_schema.get("properties", {})
    required = set(json_schema.get("required", []))

    # JSON Schema 타입 → Python 타입 매핑
    type_mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    fields = {}
    for prop_name, prop_schema in properties.items():
        json_type = prop_schema.get("type", "string")
        python_type = type_mapping.get(json_type, str)
        description = prop_schema.get("description", "")

        # Required 필드는 ...로, Optional은 None으로 기본값 설정
        if prop_name in required:
            fields[prop_name] = (python_type, Field(..., description=description))
        else:
            fields[prop_name] = (Optional[python_type], Field(default=None, description=description))

    return create_model(f"{name}Input", **fields)


class MCPClient:
    def __init__(self, url: str):
        self.url = url
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        # Currently supporting SSE connections
        # The sse_client context manager yields (read_stream, write_stream)
        # We then pass these to ClientSession
        print(f"Connecting to MCP server: {self.url}")
        try:
            # Note: mcp.client.sse.sse_client is an async context manager
            # We need to keep it alive.
            read_stream, write_stream = await self.exit_stack.enter_async_context(sse_client(self.url))

            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await self.session.initialize()
            print(f"Connected to MCP server: {self.url}")
        except Exception as e:
            print(f"Failed to connect to MCP server {self.url}: {e}")
            raise e

    async def list_tools(self) -> List[StructuredTool]:
        if not self.session:
            return []

        result = await self.session.list_tools()
        tools = []

        for tool_info in result.tools:
            # JSON Schema → Pydantic 변환
            input_schema = getattr(tool_info, 'inputSchema', None) or {}
            args_schema = json_schema_to_pydantic(tool_info.name, input_schema)

            # 클로저에서 tool_name 캡처
            tool_name = tool_info.name

            async def tool_wrapper(_tool_name=tool_name, **kwargs) -> str:
                """MCP 도구 호출 래퍼"""
                result = await self.session.call_tool(_tool_name, arguments=kwargs)
                return str(result)

            tool = StructuredTool.from_function(
                coroutine=tool_wrapper,
                name=tool_info.name,
                description=tool_info.description or f"MCP tool: {tool_info.name}",
                args_schema=args_schema,  # Pydantic 스키마 설정
            )
            tools.append(tool)

        return tools

    async def close(self):
        await self.exit_stack.aclose()
