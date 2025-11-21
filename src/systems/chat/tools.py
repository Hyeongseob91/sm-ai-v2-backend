from typing import List
from langchain_core.tools import BaseTool
from src.systems.rag.tool import RAGTool
from src.core.mcp_manager import mcp_manager

async def get_all_tools() -> List[BaseTool]:
    # Internal Tools
    tools = [RAGTool()]
    
    # External MCP Tools
    mcp_tools = await mcp_manager.get_tools()
    tools.extend(mcp_tools)
    
    return tools
