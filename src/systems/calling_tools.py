from typing import List
from langchain_core.tools import BaseTool
from src.systems.rag.rag_tool import RAGTool
from src.core.mcp_manager import mcp_manager

async def get_rag_tools() -> List[BaseTool]:
    return [RAGTool()]

async def get_internal_tools() -> List[BaseTool]:
    # Currently empty as per plan, but structured for future internal tools
    return []

async def get_external_tools() -> List[BaseTool]:
    # External MCP Tools
    return await mcp_manager.get_tools()
