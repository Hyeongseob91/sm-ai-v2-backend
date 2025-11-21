import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from langchain_core.tools import StructuredTool
from typing import Any, List

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
            # Create a LangChain StructuredTool for each MCP tool
            async def tool_wrapper(*args, _tool_name=tool_info.name, **kwargs):
                return await self.session.call_tool(_tool_name, arguments=kwargs)
            
            # We need to construct the args_schema dynamically or just allow any args if we want to be loose
            # But LangChain prefers schemas. For now, we'll make a simple wrapper.
            # A robust implementation would convert JSON Schema to Pydantic model.
            
            tool = StructuredTool.from_function(
                coroutine=tool_wrapper,
                name=tool_info.name,
                description=tool_info.description,
                # args_schema=... # TODO: Convert tool_info.inputSchema to Pydantic
            )
            tools.append(tool)
            
        return tools

    async def close(self):
        await self.exit_stack.aclose()
