from typing import List
from langchain_core.tools import BaseTool
from src.config.settings import get_settings
from src.core.mcp_client import MCPClient

settings = get_settings()

class MCPManager:
    def __init__(self):
        self.clients: List[MCPClient] = []

    async def initialize(self):
        """Connect to all MCP servers defined in settings."""
        for url in settings.MCP_SERVER_URLS:
            if not url: continue
            client = MCPClient(url)
            try:
                await client.connect()
                self.clients.append(client)
            except Exception as e:
                print(f"Error connecting to {url}: {e}")

    async def get_tools(self) -> List[BaseTool]:
        all_tools = []
        for client in self.clients:
            try:
                tools = await client.list_tools()
                all_tools.extend(tools)
            except Exception as e:
                print(f"Error fetching tools from client: {e}")
        return all_tools
    
    async def cleanup(self):
        for client in self.clients:
            await client.close()

# Global instance
mcp_manager = MCPManager()
