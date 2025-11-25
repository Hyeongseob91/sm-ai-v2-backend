from typing import List, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="The query to search for in the knowledge base.")

class RAGTool(BaseTool):
    name: str = "search_knowledge_base"
    description: str = """
    Use this tool to search for internal documents and knowledge.
    Always use this when asked about specific company policies,
    project details or internal data."""
    args_schema: Type[BaseModel] = SearchInput

    def _run(self, query: str) -> str:
        from src.systems.rag.vector_store import vector_store
        
        docs = vector_store.similarity_search(query)
        if not docs:
            return "No relevant documents found."
            
        result = "\n\n".join([f"Content: {doc.page_content}\nSource: {doc.metadata.get('source', 'Unknown')}" for doc in docs])
        return f"[RAG Search Results]\n{result}"

    async def _arun(self, query: str) -> str:
        # For now, synchronous call is fine as Chroma is local
        return self._run(query)
