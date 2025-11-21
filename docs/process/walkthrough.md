# Walkthrough - sm-ai-v2-back

## Accomplished Work
We have successfully built a **Multi-Modal AI Agent Backend** integrating LLM, RAG, and MCP.

### Architecture Overview
- **`src/core`**:
    - `LLMService`: Unified interface for OpenAI/Anthropic.
    - `MCPManager`: Manages connections to external tools (MCP).
- **`src/systems/rag`**:
    - `VectorStore`: ChromaDB wrapper for knowledge persistence.
    - `IngestionService`: Handles PDF/Text upload and indexing.
    - `RAGTool`: Allows the Agent to autonomously search knowledge.
- **`src/systems/chat`**:
    - `LangGraph`: Orchestrates the Agent's decision-making loop (Plan -> Tool -> Answer).

### Key Features
1.  **RAG (Retrieval-Augmented Generation)**:
    - Upload documents via `POST /v1/rag/ingest`.
    - Agent automatically searches for relevant info during chat.
2.  **MCP (Model Context Protocol)**:
    - Connects to external MCP servers (e.g., Filesystem, Code Interpreter).
    - Tools are dynamically loaded and exposed to the Agent.
3.  **Agentic Workflow**:
    - Uses LangGraph to manage state and tool execution loops.

## How to Verify

### 1. Run the Backend
```bash
uv run uvicorn src.api.main:app --reload
```

### 2. Run the Test MCP Server
```bash
uv run uvicorn tools.mcp_server:app --port 8001
```

### 3. Test Scenarios (Swagger UI: http://127.0.0.1:8000/docs)

#### Scenario A: RAG
1.  **Ingest**: Upload a PDF to `/v1/rag/ingest`.
2.  **Chat**: Ask "What is in the document I just uploaded?"
3.  **Result**: Agent searches ChromaDB and summarizes the content.

#### Scenario B: MCP
1.  **Chat**: Ask "List the files in the current directory."
2.  **Result**: Agent calls the `list_directory` tool from the MCP server and lists files.

## Next Steps
- Add more MCP servers for advanced capabilities (e.g., Database access, Web search).
- Implement a frontend to interact with this powerful backend.
