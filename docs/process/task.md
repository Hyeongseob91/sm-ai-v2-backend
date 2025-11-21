# Task List: sm-ai-v2-back

## Project Initialization
- [ ] Create project directory structure (src/api, src/config, src/core, etc.)
- [ ] Create `pyproject.toml` with dependencies (FastAPI, LangGraph, MCP, etc.)
- [ ] Create `README.md` with project overview

## Core Infrastructure
- [x] Implement `src/config` (Settings management)
- [x] Implement `src/core/llm_service.py` (LLM Client Factory)
- [x] Implement `src/core/mcp_manager.py` (MCP Client connection manager)
- [x] Implement `src/models` (Base Pydantic models)

## System Implementation: RAG
- [x] Implement `src/systems/rag/ingestion.py` (Document loader & splitter)
- [x] Implement `src/systems/rag/vector_store.py` (ChromaDB wrapper)
- [x] Update `src/systems/rag/tool.py` to use real Vector Store
- [x] Add API endpoint for document upload (`src/api/rag_endpoints.py`)

## System Implementation: MCP Integration
- [x] Implement `src/core/mcp_client.py` (Connect to SSE MCP Server)
- [x] Update `src/core/mcp_manager.py` to manage active connections
- [x] Update `src/systems/chat/tools.py` to dynamically load MCP tools


## System Implementation: Chat Agent (LangGraph)
- [x] Implement `src/systems/chat/graph.py` (Main LangGraph definition)
- [x] Implement `src/systems/chat/agent.py` (Agent node logic)
- [x] Implement `src/systems/chat/tools.py` (Tool binding logic including MCP)

## API Layer
- [x] Implement `src/api/main.py` (FastAPI app)
- [x] Implement `src/api/routers` (Chat and RAG endpoints)

## Verification
- [x] Verify server startup
- [x] Verify dependency installation
