from typing import List
from langchain_core.tools import BaseTool
from src.systems.rag.rag_tool import RAGTool
from src.core.mcp_manager import mcp_manager
from src.systems.internal_tools.web_search_tool import get_web_search_tools

async def get_rag_tools() -> List[BaseTool]:
    return [RAGTool()]

async def get_internal_tools() -> List[BaseTool]:
    """Get internal tools including web search capabilities."""
    tools = []
    # Add web search tools (DuckDuckGo always, Tavily if configured)
    tools.extend(get_web_search_tools())
    return tools

async def get_external_tools() -> List[BaseTool]:
    # External MCP Tools
    return await mcp_manager.get_tools()
