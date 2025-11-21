# Implementation Plan - RAG & MCP Integration

## Goal Description
Implement the "Real" logic for RAG and MCP.
1.  **RAG**: Enable the agent to ingest documents (PDF/TXT) and retrieve them using vector search (ChromaDB + OpenAI Embeddings).
2.  **MCP**: Enable the agent to connect to external MCP servers (e.g., a local server providing file system or analysis tools) and use their tools dynamically.

## User Review Required
> [!IMPORTANT]
> **MCP Server**: This backend acts as an **MCP Client**. You will need a running **MCP Server** to connect to. I will assume a standard SSE-based MCP server (like the official Python SDK examples).

## Proposed Changes

### RAG System (`src/systems/rag`)
#### [NEW] `ingestion.py`
- Logic to load text/PDF files.
- Split text into chunks (RecursiveCharacterTextSplitter).
- Embed and save to ChromaDB.

#### [NEW] `vector_store.py`
- Singleton wrapper for ChromaDB client.
- Methods: `add_documents`, `similarity_search`.

#### [MODIFY] `tool.py`
- Update `RAGTool` to call `vector_store.similarity_search` instead of returning dummy data.

### MCP System (`src/core`)
#### [MODIFY] `mcp_manager.py`
- Implement `connect_to_server` using `mcp` python package (or `httpx` for SSE if using raw protocol, but SDK is better).
- **Note**: The `mcp` package is new. We will use a standard `ClientSession` over `sse_client`.

### API Layer (`src/api`)
#### [NEW] `rag_endpoints.py`
- `POST /rag/ingest`: Endpoint to upload a file and ingest it into the vector DB.

## Verification Plan
### RAG Verification
1.  Start server.
2.  Use `/rag/ingest` to upload a sample text file.
3.  Ask the Chat Agent a question about the file.
4.  Verify the agent uses `search_knowledge_base` and answers correctly.

### MCP Verification
1.  (User Action) Run a local MCP server (e.g., `npx -y @modelcontextprotocol/server-filesystem`).
2.  Configure `.env` with the MCP server URL.
3.  Ask the agent to use a tool provided by that server.
