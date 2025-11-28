"""
Web Search Tool - DuckDuckGo (free) with optional Tavily (API key required)

Option A Implementation:
- Primary: DuckDuckGo Search (free, no API key)
- Optional: Tavily Search (enhanced, requires TAVILY_API_KEY)
"""
import os
from typing import Type, Optional, List
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class WebSearchInput(BaseModel):
    """Input for web search tool."""
    query: str = Field(description="The search query to find information on the web.")
    max_results: int = Field(default=5, description="Maximum number of search results to return (1-10).")


class DuckDuckGoSearchTool(BaseTool):
    """Web search tool using DuckDuckGo (free, no API key required)."""

    name: str = "web_search"
    description: str = """
    Use this tool to search the web for current information, news, facts, or any real-time data.
    This is useful for questions about recent events, current prices, weather, or any information
    that might not be in the knowledge base.
    """
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        """Execute web search using DuckDuckGo."""
        try:
            from duckduckgo_search import DDGS

            max_results = min(max(1, max_results), 10)

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            if not results:
                return f"No results found for: {query}"

            formatted_results = []
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                body = result.get('body', 'No description')
                href = result.get('href', '')
                formatted_results.append(f"{i}. **{title}**\n   {body}\n   URL: {href}")

            return f"[Web Search Results for: {query}]\n\n" + "\n\n".join(formatted_results)

        except Exception as e:
            return f"Web search failed: {str(e)}"

    async def _arun(self, query: str, max_results: int = 5) -> str:
        """Async execution (uses sync for now)."""
        return self._run(query, max_results)


class TavilySearchTool(BaseTool):
    """Web search tool using Tavily API (enhanced results, requires API key)."""

    name: str = "web_search_tavily"
    description: str = """
    Use this tool for enhanced web search with better relevance and AI-powered results.
    Requires TAVILY_API_KEY to be configured. Falls back to DuckDuckGo if unavailable.
    """
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        """Execute web search using Tavily API."""
        api_key = os.getenv("TAVILY_API_KEY")

        if not api_key:
            # Fallback to DuckDuckGo
            ddg_tool = DuckDuckGoSearchTool()
            return ddg_tool._run(query, max_results)

        try:
            from tavily import TavilyClient

            max_results = min(max(1, max_results), 10)

            client = TavilyClient(api_key=api_key)
            response = client.search(query, max_results=max_results)

            results = response.get('results', [])

            if not results:
                return f"No results found for: {query}"

            formatted_results = []
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                content = result.get('content', 'No description')
                url = result.get('url', '')
                score = result.get('score', 0)
                formatted_results.append(
                    f"{i}. **{title}** (relevance: {score:.2f})\n   {content}\n   URL: {url}"
                )

            return f"[Tavily Search Results for: {query}]\n\n" + "\n\n".join(formatted_results)

        except Exception as e:
            # Fallback to DuckDuckGo on error
            ddg_tool = DuckDuckGoSearchTool()
            fallback_result = ddg_tool._run(query, max_results)
            return f"[Tavily failed, using DuckDuckGo fallback]\n\n{fallback_result}"

    async def _arun(self, query: str, max_results: int = 5) -> str:
        """Async execution (uses sync for now)."""
        return self._run(query, max_results)


def get_web_search_tools() -> List[BaseTool]:
    """
    Get available web search tools.

    Returns:
        - DuckDuckGoSearchTool: Always available (free, no API key)
        - TavilySearchTool: Only if TAVILY_API_KEY is configured
    """
    tools = [DuckDuckGoSearchTool()]

    # Add Tavily if API key is configured
    if os.getenv("TAVILY_API_KEY"):
        tools.append(TavilySearchTool())

    return tools
