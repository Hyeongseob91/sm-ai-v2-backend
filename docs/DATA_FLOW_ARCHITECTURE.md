# Multi-Agent 시스템 데이터 흐름 아키텍처

이 문서는 sm-ai-v2-backend의 Multi-Agent 시스템에서 사용자 요청이 처리되는 전체 데이터 흐름을 상세하게 설명합니다.

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [파일 구조 및 역할](#2-파일-구조-및-역할)
3. [핵심 컴포넌트](#3-핵심-컴포넌트)
4. [상세 데이터 흐름 (Step by Step)](#4-상세-데이터-흐름-step-by-step)
5. [도구 스키마 변환 흐름](#5-도구-스키마-변환-흐름)
6. [데이터 변환 요약](#6-데이터-변환-요약)

---

## 1. 시스템 개요

### 1.1 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              사용자 요청                                      │
│                    POST /v1/chat { message, session_id }                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API Layer (chat.py)                               │
│                     JSON → LangChain 메시지 변환                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               Supervisor (langgraph_supervisor.create_supervisor)           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         supervisor_node                                │  │
│  │   - LLM으로 적절한 에이전트 선택 (native tool calling)                   │  │
│  │   - handoff 도구를 통해 에이전트 위임                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                           │                                                  │
│              ┌────────────┼────────────┐                                    │
│              ▼            ▼            ▼                                    │
│        ┌──────────┐ ┌──────────┐ ┌──────────┐                              │
│        │rag_agent │ │external  │ │internal  │                              │
│        │(prebuilt)│ │_agent    │ │_agent    │                              │
│        └──────────┘ └──────────┘ └──────────┘                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              LangGraph Prebuilt Agent (create_react_agent)                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      ReAct Agent Node                                  │  │
│  │   - vLLM Native Tool Calling (--tool-call-parser openai)              │  │
│  │   - LLM이 직접 tool_calls 형식으로 응답                                 │  │
│  │   - 자동 도구 실행 및 결과 처리                                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                           │                                                  │
│                           ▼                                                  │
│              ┌───────────────────────────────────────────────────────────┐  │
│              │                    Tool Execution                          │  │
│              │   - RAGTool: 벡터 DB 검색                                   │  │
│              │   - MCP Tools: 외부 시스템 연동                              │  │
│              │   - Internal Tools: 데이터 분석                             │  │
│              └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API Layer (chat.py)                               │
│                     LangChain 메시지 → JSON 변환                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HTTP 응답                                       │
│                    { response, tool_calls, metadata }                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 주요 특징

- **Native Tool Calling**: vLLM의 `--enable-auto-tool-choice --tool-call-parser openai` 옵션 사용
- **LangGraph Prebuilt**: `create_react_agent`와 `create_supervisor` 사용으로 구현 단순화
- **JSON Schema → Pydantic 변환**: MCP 도구의 스키마를 LangChain 호환 형식으로 자동 변환
- **Multi-Agent Routing**: Supervisor가 적절한 전문 에이전트로 라우팅

---

## 2. 파일 구조 및 역할

### 2.1 프로젝트 구조

```
src/
├── api/
│   ├── main.py              # FastAPI 앱 설정
│   ├── router.py            # API Gateway 라우터
│   ├── dependencies.py      # 의존성 주입 (그래프 인스턴스)
│   └── v1/
│       ├── chat.py          # Chat API 엔드포인트
│       └── documents.py     # 문서 업로드 API
├── core/
│   ├── llm_service.py       # LLM 인스턴스 관리
│   ├── mcp_client.py        # MCP 클라이언트 (스키마 변환 포함)
│   ├── mcp_manager.py       # MCP 연결 관리
│   └── session_manager.py   # 세션 체크포인터
├── systems/
│   ├── build_graph.py       # Multi-Agent 그래프 빌더
│   ├── calling_tools.py     # 도구 로딩 함수
│   ├── agent/
│   │   ├── supervisor.py    # Supervisor 프롬프트
│   │   ├── rag_agent.py     # RAG 에이전트 생성
│   │   ├── external_agent.py # 외부 시스템 에이전트
│   │   └── internal_agent.py # 내부 처리 에이전트
│   └── rag/
│       ├── rag_tool.py      # RAG 검색 도구
│       ├── vector_store.py  # ChromaDB 연동
│       └── ingestion.py     # 문서 수집 서비스
├── schema/
│   └── api_schema.py        # API 요청/응답 스키마
└── config/
    └── settings.py          # 환경 설정
```

### 2.2 파일별 상세 역할

| 파일 | 역할 | 핵심 함수/클래스 |
|------|------|-----------------|
| `build_graph.py` | Supervisor + Agent 그래프 생성 | `build_graph()` |
| `llm_service.py` | vLLM 연결 LLM 인스턴스 | `LLMService.get_llm()` |
| `mcp_client.py` | MCP 도구 로딩 + 스키마 변환 | `json_schema_to_pydantic()`, `MCPClient` |
| `rag_agent.py` | 문서 검색 전문 에이전트 | `create_rag_agent()` |
| `external_agent.py` | MCP 도구 사용 에이전트 | `create_external_agent()` |
| `internal_agent.py` | 데이터 분석 에이전트 | `create_internal_agent()` |
| `chat.py` | Chat API 엔드포인트 | `send_message()` |

---

## 3. 핵심 컴포넌트

### 3.1 Supervisor (langgraph_supervisor)

```python
# src/systems/build_graph.py
from langgraph_supervisor import create_supervisor

workflow = create_supervisor(
    agents=[rag_agent, external_agent, internal_agent],
    model=llm,
    prompt=SUPERVISOR_PROMPT
)
```

**동작 방식**:
1. 사용자 요청 분석
2. 적합한 에이전트 선택 (LLM의 native tool calling 사용)
3. 선택된 에이전트로 작업 위임 (handoff)
4. 에이전트 결과 수집 및 최종 응답 생성

### 3.2 ReAct Agent (langgraph.prebuilt)

```python
# src/systems/agent/rag_agent.py
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=llm,
    tools=tools,
    name="rag_agent",
    prompt=RAG_AGENT_PROMPT
)
```

**동작 방식**:
1. 프롬프트와 도구 목록을 LLM에 전달
2. vLLM이 native tool_calls 형식으로 응답
3. LangGraph가 자동으로 도구 실행
4. 결과를 다시 LLM에 전달 (ReAct 루프)
5. 최종 답변 생성

### 3.3 MCP 도구 스키마 변환

```python
# src/core/mcp_client.py
def json_schema_to_pydantic(name: str, json_schema: Dict[str, Any]) -> Type[BaseModel]:
    """MCP의 JSON Schema를 Pydantic BaseModel로 변환"""
    properties = json_schema.get("properties", {})
    required = set(json_schema.get("required", []))

    type_mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    fields = {}
    for prop_name, prop_schema in properties.items():
        python_type = type_mapping.get(prop_schema.get("type", "string"), str)
        description = prop_schema.get("description", "")

        if prop_name in required:
            fields[prop_name] = (python_type, Field(..., description=description))
        else:
            fields[prop_name] = (Optional[python_type], Field(default=None, description=description))

    return create_model(f"{name}Input", **fields)
```

**역할**: MCP 서버에서 제공하는 도구의 JSON Schema를 LangChain이 이해할 수 있는 Pydantic 모델로 변환

---

## 4. 상세 데이터 흐름 (Step by Step)

### 시나리오: 사용자가 "회사 휴가 정책 알려줘"라고 질문

---

### STEP 1: HTTP 요청 수신

**위치**: `src/api/v1/chat.py:15-31`

#### 입력 (HTTP Request)
```json
POST /v1/chat HTTP/1.1
Content-Type: application/json

{
  "message": "회사 휴가 정책 알려줘",
  "session_id": "user-session-123"
}
```

#### 처리 코드
```python
@router.post("", response_model=ChatResponse)
async def send_message(request: ChatRequest, graph=Depends(get_graph)):
    config = {"configurable": {"thread_id": request.session_id}}
    inputs = {"messages": [HumanMessage(content=request.message)]}
    final_state = await graph.ainvoke(inputs, config)
```

#### 출력
```python
inputs = {
    "messages": [HumanMessage(content="회사 휴가 정책 알려줘")]
}
config = {"configurable": {"thread_id": "user-session-123"}}
```

---

### STEP 2: Supervisor 라우팅

**위치**: `langgraph_supervisor` 내부 처리

#### LLM에 전달되는 메시지
```python
[
    SystemMessage(content=SUPERVISOR_PROMPT),
    HumanMessage(content="회사 휴가 정책 알려줘")
]
```

#### LLM 응답 (Native Tool Calling)
```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [{
    "id": "call_xxx",
    "type": "function",
    "function": {
      "name": "transfer_to_rag_agent",
      "arguments": "{}"
    }
  }]
}
```

**동작**: Supervisor는 "휴가 정책" 키워드를 인식하고 `rag_agent`로 작업을 위임

---

### STEP 3: RAG Agent 실행

**위치**: `src/systems/agent/rag_agent.py` → `langgraph.prebuilt.create_react_agent`

#### Agent 초기 상태
```python
{
    "messages": [HumanMessage(content="회사 휴가 정책 알려줘")]
}
```

#### LLM에 전달되는 메시지
```python
[
    SystemMessage(content=RAG_AGENT_PROMPT),
    HumanMessage(content="회사 휴가 정책 알려줘")
]
```

#### LLM 응답 (Tool Calling)
```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [{
    "id": "call_yyy",
    "type": "function",
    "function": {
      "name": "search_knowledge_base",
      "arguments": "{\"query\": \"휴가 정책\"}"
    }
  }]
}
```

---

### STEP 4: 도구 실행 (RAGTool)

**위치**: `src/systems/rag/rag_tool.py`

#### 입력
```python
query = "휴가 정책"
```

#### 처리 코드
```python
class RAGTool(BaseTool):
    def _run(self, query: str) -> str:
        docs = vector_store.similarity_search(query)
        result = "\n\n".join([
            f"Content: {doc.page_content}\nSource: {doc.metadata.get('source')}"
            for doc in docs
        ])
        return f"[RAG Search Results]\n{result}"
```

#### 출력
```
[RAG Search Results]
Content: 연차휴가는 근속년수에 따라 차등 부여됩니다.
- 1년 미만: 월 1일
- 1년 이상: 15일
- 3년 이상: 20일
출근율 80% 이상 시 전액 부여됩니다.
Source: 인사규정.pdf
```

---

### STEP 5: 도구 결과를 LLM에 전달

**위치**: `langgraph.prebuilt.create_react_agent` 내부

#### 메시지 히스토리
```python
[
    SystemMessage(content=RAG_AGENT_PROMPT),
    HumanMessage(content="회사 휴가 정책 알려줘"),
    AIMessage(content=None, tool_calls=[...]),
    ToolMessage(
        content="[RAG Search Results]\nContent: 연차휴가는...",
        tool_call_id="call_yyy"
    )
]
```

---

### STEP 6: 최종 응답 생성

**위치**: `langgraph.prebuilt.create_react_agent` 내부

#### LLM 최종 응답
```json
{
  "role": "assistant",
  "content": "회사의 연차휴가 정책은 다음과 같습니다:\n\n- **1년 미만 근속**: 월 1일\n- **1년 이상 근속**: 연 15일\n- **3년 이상 근속**: 연 20일\n\n단, 출근율 80% 이상 시 전액 부여됩니다.\n\n출처: 인사규정.pdf",
  "tool_calls": null
}
```

---

### STEP 7: Supervisor로 결과 반환

Agent의 결과가 Supervisor로 반환되고, Supervisor는 최종 응답을 사용자에게 전달

---

### STEP 8: HTTP 응답 생성

**위치**: `src/api/v1/chat.py:36-44`

#### 처리 코드
```python
messages = final_state["messages"]
last_message = messages[-1]

return ChatResponse(
    response=last_message.content,
    tool_calls=[],
    metadata={"thread_id": request.session_id}
)
```

#### 최종 HTTP 응답
```json
{
  "response": "회사의 연차휴가 정책은 다음과 같습니다:\n\n- **1년 미만 근속**: 월 1일\n- **1년 이상 근속**: 연 15일\n- **3년 이상 근속**: 연 20일\n\n단, 출근율 80% 이상 시 전액 부여됩니다.\n\n출처: 인사규정.pdf",
  "tool_calls": [],
  "metadata": {
    "thread_id": "user-session-123"
  }
}
```

---

## 5. 도구 스키마 변환 흐름

MCP 도구가 LangChain에서 사용되기까지의 스키마 변환 과정:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MCP Server (External)                              │
│                                                                             │
│  Tool Definition:                                                           │
│  {                                                                          │
│    "name": "list_directory",                                                │
│    "description": "List files in a directory",                              │
│    "inputSchema": {                                                         │
│      "type": "object",                                                      │
│      "properties": {                                                        │
│        "path": {"type": "string", "description": "Directory path"}          │
│      },                                                                     │
│      "required": ["path"]                                                   │
│    }                                                                        │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ session.list_tools()
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MCPClient.list_tools() (mcp_client.py)                  │
│                                                                             │
│  for tool_info in result.tools:                                             │
│      input_schema = tool_info.inputSchema                                   │
│      args_schema = json_schema_to_pydantic(tool_info.name, input_schema)    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ json_schema_to_pydantic()
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 Pydantic Model (Dynamic Generation)                         │
│                                                                             │
│  class list_directoryInput(BaseModel):                                      │
│      path: str = Field(..., description="Directory path")                   │
│                                                                             │
│  # Required 필드: Field(..., description=...)                               │
│  # Optional 필드: Optional[type] = Field(default=None, description=...)      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ StructuredTool.from_function()
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LangChain StructuredTool                                 │
│                                                                             │
│  StructuredTool(                                                            │
│      name="list_directory",                                                 │
│      description="List files in a directory",                               │
│      coroutine=tool_wrapper,           # MCP 도구 호출 래퍼                   │
│      args_schema=list_directoryInput   # Pydantic 스키마                     │
│  )                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ LLM.bind_tools()
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      vLLM Native Tool Calling                               │
│                                                                             │
│  LLM Request (tools parameter):                                             │
│  {                                                                          │
│    "tools": [{                                                              │
│      "type": "function",                                                    │
│      "function": {                                                          │
│        "name": "list_directory",                                            │
│        "description": "List files in a directory",                          │
│        "parameters": {                                                      │
│          "type": "object",                                                  │
│          "properties": {"path": {"type": "string"}},                        │
│          "required": ["path"]                                               │
│        }                                                                    │
│      }                                                                      │
│    }]                                                                       │
│  }                                                                          │
│                                                                             │
│  LLM Response (tool_calls):                                                 │
│  {                                                                          │
│    "tool_calls": [{                                                         │
│      "function": {                                                          │
│        "name": "list_directory",                                            │
│        "arguments": "{\"path\": \"/home/user\"}"                            │
│      }                                                                      │
│    }]                                                                       │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 데이터 변환 요약

### 6.1 전체 데이터 변환 흐름표

| Step | 위치 | 입력 데이터 타입 | 출력 데이터 타입 | 핵심 변환 |
|------|------|----------------|----------------|----------|
| 1 | `chat.py` | HTTP JSON | `inputs: {messages: [HumanMessage]}` | JSON → LangChain 메시지 |
| 2 | `build_graph.py` | `inputs` | Supervisor 그래프 실행 | 그래프 진입 |
| 3 | Supervisor | 메시지 | Agent 선택 + 위임 | Native tool calling으로 라우팅 |
| 4 | Agent | 메시지 | Tool call 결정 | Native tool calling |
| 5 | Tool | Tool arguments | Tool result string | 실제 도구 실행 |
| 6 | Agent | Tool result | Final answer | 결과 해석 + 응답 생성 |
| 7 | Supervisor | Agent 결과 | 최종 응답 | 결과 수집 |
| 8 | `chat.py` | `final_state` | HTTP JSON | LangChain → JSON 변환 |

### 6.2 메시지 타입 흐름

```
HumanMessage (사용자 입력)
    ↓
AIMessage + tool_calls (LLM 도구 호출 결정)
    ↓
ToolMessage (도구 실행 결과)
    ↓
AIMessage (최종 응답)
```

### 6.3 Native Tool Calling vs Prompt-based 비교

현재 시스템은 **Native Tool Calling** 방식을 사용:

| 항목 | Native Tool Calling (현재) | Prompt-based |
|------|---------------------------|--------------|
| LLM 응답 형식 | `tool_calls` 배열 | 텍스트 (Action: ...) |
| 파싱 방식 | JSON 직접 사용 | 정규식 파싱 |
| 안정성 | 높음 (표준 형식) | 중간 (모델 의존) |
| vLLM 옵션 | `--enable-auto-tool-choice` 필수 | 불필요 |
| LangGraph 호환 | `create_react_agent` 직접 사용 | Custom StateGraph 필요 |

---

## 부록: 핵심 설정 요약

### vLLM 서버 옵션 (필수)
```bash
--enable-auto-tool-choice    # 자동 도구 선택 활성화
--tool-call-parser openai    # OpenAI 형식 파서
```

### LLM Service 설정
```python
ChatOpenAI(
    base_url="http://localhost:8000/v1",
    model="gpt-oss-120b"
)
```

### 에이전트 생성 패턴
```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=llm,
    tools=tools,
    name="agent_name",
    prompt=AGENT_PROMPT
)
```

### Supervisor 생성 패턴
```python
from langgraph_supervisor import create_supervisor

workflow = create_supervisor(
    agents=[agent1, agent2, agent3],
    model=llm,
    prompt=SUPERVISOR_PROMPT
)
```
