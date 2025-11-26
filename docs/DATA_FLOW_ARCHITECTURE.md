# Multi-Agent 시스템 데이터 흐름 아키텍처

이 문서는 sm-ai-v2-backend의 Multi-Agent 시스템에서 사용자 요청이 처리되는 전체 데이터 흐름을 상세하게 설명합니다.

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [파일 구조 및 역할](#2-파일-구조-및-역할)
3. [핵심 데이터 타입](#3-핵심-데이터-타입)
4. [상세 데이터 흐름 (Step by Step)](#4-상세-데이터-흐름-step-by-step)
5. [데이터 변환 요약](#5-데이터-변환-요약)
6. [기존 구조 vs 새 구조 비교](#6-기존-구조-vs-새-구조-비교)

---

## 1. 시스템 개요

### 1.1 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              사용자 요청                                  │
│                    POST /v1/chat { message, session_id }                │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API Layer (chat.py)                           │
│                     JSON → LangChain 메시지 변환                          │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Supervisor (supervisor.py)                          │
│              ┌─────────────────────────────────────────┐                │
│              │      supervisor_route_node              │                │
│              │   - LLM으로 적절한 에이전트 선택          │                │
│              │   - "Delegate: agent_name" 파싱          │                │
│              └─────────────────────────────────────────┘                │
│                           │                                             │
│              ┌────────────┼────────────┐                                │
│              ▼            ▼            ▼                                │
│        ┌──────────┐ ┌──────────┐ ┌──────────┐                          │
│        │rag_agent │ │external  │ │internal  │                          │
│        │          │ │_agent    │ │_agent    │                          │
│        └──────────┘ └──────────┘ └──────────┘                          │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Custom ReAct Agent (nodes.py)                        │
│              ┌─────────────────────────────────────────┐                │
│              │         call_model 노드                  │                │
│              │   - LLM 호출 (prompt-based)              │                │
│              │   - ToolCallParser로 응답 파싱           │                │
│              └─────────────────────────────────────────┘                │
│                           │                                             │
│                           ▼                                             │
│              ┌─────────────────────────────────────────┐                │
│              │        execute_tool 노드                │                │
│              │   - 도구 실행 (RAGTool, MCP 등)          │                │
│              │   - 결과를 Observation으로 포맷팅        │                │
│              └─────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API Layer (chat.py)                           │
│                     LangChain 메시지 → JSON 변환                          │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              HTTP 응답                                   │
│                    { response, tool_calls, metadata }                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 주요 특징

- **Prompt-based Tool Calling**: API 레벨 도구 바인딩 대신 프롬프트 기반 도구 호출
- **Open Source 모델 호환**: gpt-oss-120b 등 vLLM 서빙 모델에서 안정적 동작
- **ReAct 패턴**: Thought → Action → Observation 사이클
- **Multi-Agent Routing**: Supervisor가 적절한 전문 에이전트로 라우팅

---

## 2. 파일 구조 및 역할

### 2.1 새로 생성된 파일

```
src/systems/react/
├── __init__.py          # 모듈 export
├── state.py             # 상태 타입 정의 (AgentState, SupervisorState)
├── tool_parser.py       # 도구 호출 파싱 로직 (ToolCallParser)
├── nodes.py             # StateGraph 노드 (call_model, execute_tool)
├── agent_builder.py     # 에이전트 생성 (create_custom_react_agent)
└── supervisor.py        # Supervisor 생성 (create_custom_supervisor)
```

### 2.2 파일별 상세 역할

| 파일 | 역할 | 핵심 클래스/함수 | 입력 | 출력 |
|------|------|-----------------|------|------|
| `__init__.py` | 모듈 export | `create_custom_react_agent`, `create_custom_supervisor` | - | - |
| `state.py` | 상태 타입 정의 | `AgentState`, `SupervisorState` (TypedDict) | - | - |
| `tool_parser.py` | 텍스트에서 도구 호출 추출 | `ToolCallParser.parse()` | LLM 응답 텍스트 | `(tool_call, final_answer)` |
| `nodes.py` | StateGraph 노드 구현 | `build_call_model_node()`, `build_execute_tool_node()` | `AgentState` | 상태 업데이트 dict |
| `agent_builder.py` | ReAct 에이전트 생성 | `create_custom_react_agent()` | LLM, tools, prompt | `CustomReactAgent` |
| `supervisor.py` | Supervisor 생성 | `create_custom_supervisor()` | agents, LLM, prompt | `StateGraph` |

### 2.3 수정된 파일

| 파일 | 변경 전 | 변경 후 |
|------|--------|--------|
| `src/systems/agent/rag_agent.py` | `langgraph.prebuilt.create_react_agent` | `src.systems.react.create_custom_react_agent` |
| `src/systems/agent/external_agent.py` | `langgraph.prebuilt.create_react_agent` | `src.systems.react.create_custom_react_agent` |
| `src/systems/agent/internal_agent.py` | `langgraph.prebuilt.create_react_agent` | `src.systems.react.create_custom_react_agent` |
| `src/systems/build_graph.py` | `langgraph_supervisor.create_supervisor` | `src.systems.react.create_custom_supervisor` |

---

## 3. 핵심 데이터 타입

### 3.1 AgentState (에이전트 상태)

```python
class AgentState(TypedDict):
    """Custom ReAct Agent의 상태"""

    messages: Annotated[List[BaseMessage], add_messages]
    # 대화 메시지 히스토리
    # add_messages reducer: 새 메시지가 기존 리스트에 추가됨

    iteration: int
    # 현재 ReAct 루프 반복 횟수 (0부터 시작)

    max_iterations: int
    # 최대 반복 횟수 (기본값: 10, 무한 루프 방지)

    agent_name: str
    # 에이전트 식별자 ("rag_agent", "external_agent", "internal_agent")

    pending_tool_call: Optional[Dict[str, Any]]
    # 파싱된 도구 호출 정보
    # 예: {"name": "search_knowledge_base", "args": {"query": "휴가 정책"}}
    # None이면 도구 호출 대기 없음

    should_stop: bool
    # 종료 플래그 (True면 에이전트 루프 종료)
```

### 3.2 SupervisorState (Supervisor 상태)

```python
class SupervisorState(TypedDict):
    """Custom Supervisor의 상태"""

    messages: Annotated[List[BaseMessage], add_messages]
    # 대화 메시지 히스토리

    current_agent: Optional[str]
    # 현재 선택된 에이전트 이름
    # None: 아직 선택 안됨
    # "rag_agent" 등: 해당 에이전트로 라우팅
    # "__end__": 종료 신호

    agent_outputs: Dict[str, str]
    # 각 에이전트의 실행 결과
    # 예: {"rag_agent": "회사의 연차휴가 정책은..."}

    iteration: int
    # 라우팅 반복 횟수

    max_iterations: int
    # 최대 라우팅 횟수 (기본값: 5)
```

### 3.3 LangChain 메시지 타입

```python
from langchain_core.messages import (
    BaseMessage,      # 모든 메시지의 기본 클래스
    HumanMessage,     # 사용자 입력
    AIMessage,        # AI 응답
    SystemMessage,    # 시스템 프롬프트
    ToolMessage       # 도구 실행 결과 (현재 미사용, HumanMessage로 대체)
)
```

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
    # request 객체:
    # - request.message = "회사 휴가 정책 알려줘"
    # - request.session_id = "user-session-123"

    # LangGraph 설정 (세션 관리용)
    config = {"configurable": {"thread_id": request.session_id}}

    # LangChain 메시지 형식으로 변환
    inputs = {"messages": [HumanMessage(content=request.message)]}
```

#### 출력
```python
inputs = {
    "messages": [
        HumanMessage(content="회사 휴가 정책 알려줘")
    ]
}

config = {
    "configurable": {
        "thread_id": "user-session-123"
    }
}
```

---

### STEP 2: Supervisor 초기 상태 생성

**위치**: `src/systems/react/supervisor.py:72-94`

#### 입력
```python
inputs = {"messages": [HumanMessage(content="회사 휴가 정책 알려줘")]}
```

#### 처리 코드
```python
class CustomSupervisor:
    async def ainvoke(self, inputs: dict, config: Optional[dict] = None) -> dict:
        full_state = {
            "messages": inputs.get("messages", []),  # 입력에서 복사
            "current_agent": None,                    # 아직 에이전트 미선택
            "agent_outputs": {},                      # 에이전트 결과 없음
            "iteration": 0,                           # 첫 번째 반복
            "max_iterations": self.max_iterations     # 기본값 5
        }
        return await self.graph.ainvoke(full_state, config)
```

#### 출력 (SupervisorState 초기값)
```python
SupervisorState = {
    "messages": [
        HumanMessage(content="회사 휴가 정책 알려줘")
    ],
    "current_agent": None,
    "agent_outputs": {},
    "iteration": 0,
    "max_iterations": 5
}
```

---

### STEP 3: Supervisor 라우팅 노드 실행

**위치**: `src/systems/react/supervisor.py:167-233`

#### 입력 (SupervisorState)
```python
state = {
    "messages": [HumanMessage(content="회사 휴가 정책 알려줘")],
    "current_agent": None,
    "agent_outputs": {},
    "iteration": 0,
    "max_iterations": 5
}
```

#### 처리 코드
```python
async def supervisor_route_node(state: SupervisorState) -> Dict[str, Any]:
    iteration = state.get("iteration", 0)  # 0

    # LLM에 전달할 메시지 구성
    messages: List[BaseMessage] = [
        SystemMessage(content=system_prompt)  # ROUTING_PROMPT_TEMPLATE
    ] + list(state["messages"])

    # LLM 호출
    response = await model.ainvoke(messages)
    response_text = response.content

    # 응답 파싱 (정규식)
    delegate_match = re.search(r'Delegate:\s*(\w+)', response_text, re.IGNORECASE)
    final_match = re.search(r'Final Answer:\s*(.+)', response_text, re.DOTALL)
```

#### LLM에 전달되는 messages
```python
[
    SystemMessage(content="""당신은 멀티 에이전트 시스템의 supervisor입니다.

    [SUPERVISOR_PROMPT 내용]

    ## 사용 가능한 에이전트
    - rag_agent: Agent: rag_agent
    - external_agent: Agent: external_agent
    - internal_agent: Agent: internal_agent

    ## 라우팅 규칙
    사용자의 요청을 분석하여 가장 적합한 에이전트를 선택하세요.

    응답 형식:
    1. 에이전트에게 작업을 위임할 때:
    ```
    Delegate: [에이전트_이름]
    Task: [해당 에이전트가 수행할 작업 설명]
    ```

    2. 모든 작업이 완료되어 최종 답변을 제공할 때:
    ```
    Final Answer: [사용자에게 전달할 완성된 답변]
    ```
    """),

    HumanMessage(content="회사 휴가 정책 알려줘")
]
```

#### LLM 응답 예시
```
회사 휴가 정책에 대한 질문은 내부 문서 검색이 필요합니다.

Delegate: rag_agent
Task: 회사 휴가 정책 관련 문서를 검색하여 정보를 제공
```

#### 응답 파싱 결과
```python
delegate_match = re.search(r'Delegate:\s*(\w+)', response_text, re.IGNORECASE)
# delegate_match.group(1) = "rag_agent"

final_match = re.search(r'Final Answer:\s*(.+)', response_text, re.DOTALL)
# final_match = None (Final Answer가 없으므로)
```

#### 출력 (상태 업데이트)
```python
return {
    "messages": [AIMessage(content="회사 휴가 정책에 대한 질문은 내부 문서 검색이 필요합니다.\n\nDelegate: rag_agent\nTask: 회사 휴가 정책 관련 문서를 검색하여 정보를 제공")],
    "current_agent": "rag_agent",
    "iteration": 1  # 0 → 1
}
```

#### 상태 머지 후 SupervisorState
```python
SupervisorState = {
    "messages": [
        HumanMessage(content="회사 휴가 정책 알려줘"),
        AIMessage(content="회사 휴가 정책에 대한 질문은...")  # add_messages로 추가
    ],
    "current_agent": "rag_agent",  # None → "rag_agent"
    "agent_outputs": {},
    "iteration": 1,  # 0 → 1
    "max_iterations": 5
}
```

---

### STEP 4: 조건부 라우팅 (route_next)

**위치**: `src/systems/react/supervisor.py:286-296`

#### 입력
```python
state = {
    "current_agent": "rag_agent",
    "iteration": 1,
    "max_iterations": 5
}
```

#### 처리 코드
```python
def route_next(state: SupervisorState) -> str:
    current_agent = state.get("current_agent", "__end__")  # "rag_agent"
    iteration = state.get("iteration", 0)                   # 1
    max_iter = state.get("max_iterations", max_iterations)  # 5

    if current_agent == "__end__" or iteration >= max_iter:
        return "end"
    return "agent"  # ← 이 경로로 분기
```

#### 출력
```python
"agent"  # → execute_agent_node로 이동
```

---

### STEP 5: 에이전트 실행 노드

**위치**: `src/systems/react/supervisor.py:235-284`

#### 입력 (SupervisorState)
```python
state = {
    "messages": [
        HumanMessage(content="회사 휴가 정책 알려줘"),
        AIMessage(content="회사 휴가 정책에 대한 질문은...")
    ],
    "current_agent": "rag_agent",
    "agent_outputs": {},
    "iteration": 1,
    "max_iterations": 5
}
```

#### 처리 코드
```python
async def execute_agent_node(state: SupervisorState) -> Dict[str, Any]:
    agent_name = state.get("current_agent")  # "rag_agent"

    agent = agent_map.get(agent_name)  # CustomReactAgent 인스턴스

    # 원본 사용자 메시지만 추출 (AIMessage 제외)
    user_messages = [
        m for m in state["messages"]
        if isinstance(m, HumanMessage)
    ]
    # user_messages = [HumanMessage(content="회사 휴가 정책 알려줘")]

    inputs = {"messages": user_messages}

    # 에이전트 호출
    result = await agent.ainvoke(inputs)
```

#### agent.ainvoke에 전달되는 데이터
```python
inputs = {
    "messages": [
        HumanMessage(content="회사 휴가 정책 알려줘")
    ]
}
```

---

### STEP 6: CustomReactAgent 초기 상태 생성

**위치**: `src/systems/react/agent_builder.py:72-94`

#### 입력
```python
inputs = {"messages": [HumanMessage(content="회사 휴가 정책 알려줘")]}
```

#### 처리 코드
```python
class CustomReactAgent:
    async def ainvoke(self, inputs: dict, config: Optional[dict] = None) -> dict:
        full_state = {
            "messages": inputs.get("messages", []),
            "iteration": 0,
            "max_iterations": self.max_iterations,  # 10
            "agent_name": self.name,                 # "rag_agent"
            "pending_tool_call": None,
            "should_stop": False
        }
        return await self.graph.ainvoke(full_state, config)
```

#### 출력 (AgentState 초기값)
```python
AgentState = {
    "messages": [
        HumanMessage(content="회사 휴가 정책 알려줘")
    ],
    "iteration": 0,
    "max_iterations": 10,
    "agent_name": "rag_agent",
    "pending_tool_call": None,
    "should_stop": False
}
```

---

### STEP 7: Agent의 call_model 노드 (1회차)

**위치**: `src/systems/react/nodes.py:39-101`

#### 입력 (AgentState)
```python
state = {
    "messages": [HumanMessage(content="회사 휴가 정책 알려줘")],
    "iteration": 0,
    "max_iterations": 10,
    "agent_name": "rag_agent",
    "pending_tool_call": None,
    "should_stop": False
}
```

#### 처리 코드
```python
async def call_model(state: AgentState) -> Dict[str, Any]:
    messages = state["messages"]
    iteration = state.get("iteration", 0)  # 0

    # LLM에 전달할 메시지 구성
    full_messages: List[BaseMessage] = [
        SystemMessage(content=system_prompt)
    ] + list(messages)

    # LLM 호출
    response = await llm.ainvoke(full_messages)
    response_text = response.content

    # 응답 파싱
    tool_call, final_answer = parser.parse(response_text)
```

#### system_prompt 내용
`create_react_system_prompt()` 함수에서 생성됨:

```
당신은 내부 지식 기반 검색 전문가입니다.

## 역할
- 회사 정책, 프로젝트 문서, 내부 데이터에 대한 질문에 답변합니다.
- 업로드된 문서에서 관련 정보를 검색합니다.

[... RAG_AGENT_PROMPT 전체 내용 ...]

## 도구 사용 방법

사용 가능한 도구:
- search_knowledge_base: Use this tool to search for internal documents and knowledge...
  Arguments: query: The query to search for in the knowledge base.

도구를 사용하려면 다음 형식으로 응답하세요:
```
Thought: [현재 상황과 다음 행동에 대한 생각]
Action: [도구_이름]
Action Input: {"인자명": "값"}
```

최종 답변을 제공할 때는:
```
Thought: [최종 분석]
Final Answer: [사용자에게 전달할 완성된 답변]
```

중요 규칙:
1. Thought는 항상 Action이나 Final Answer 전에 작성하세요.
2. Action Input은 반드시 유효한 JSON 형식이어야 합니다.
3. 사용 가능한 도구 목록에 없는 도구는 사용하지 마세요.
```

#### LLM에 전달되는 messages
```python
[
    SystemMessage(content="당신은 내부 지식 기반 검색 전문가입니다...[위 내용]"),
    HumanMessage(content="회사 휴가 정책 알려줘")
]
```

#### LLM 응답 예시
```
Thought: 회사 휴가 정책에 대한 질문입니다. 내부 문서에서 관련 정보를 검색해야 합니다.
Action: search_knowledge_base
Action Input: {"query": "휴가 정책"}
```

#### ToolCallParser.parse() 처리

**위치**: `src/systems/react/tool_parser.py`

```python
# 정규식 패턴
TOOL_CALL_PATTERNS = [
    r'Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\n\s*Action Input:\s*(\{.*?\})',
    ...
]

# 매칭 결과
match = re.search(pattern, response_text, re.DOTALL)
# match.group(1) = "search_knowledge_base"
# match.group(2) = '{"query": "휴가 정책"}'

tool_call = {
    "name": "search_knowledge_base",
    "args": {"query": "휴가 정책"}
}
final_answer = None
```

#### 출력 (상태 업데이트)
```python
return {
    "messages": [AIMessage(content="Thought: 회사 휴가 정책에 대한 질문입니다...\nAction: search_knowledge_base\nAction Input: {\"query\": \"휴가 정책\"}")],
    "should_stop": False,
    "pending_tool_call": {"name": "search_knowledge_base", "args": {"query": "휴가 정책"}},
    "iteration": 1
}
```

#### 상태 머지 후 AgentState
```python
AgentState = {
    "messages": [
        HumanMessage(content="회사 휴가 정책 알려줘"),
        AIMessage(content="Thought: 회사 휴가 정책에 대한 질문입니다...\nAction: search_knowledge_base\nAction Input: {\"query\": \"휴가 정책\"}")
    ],
    "iteration": 1,
    "max_iterations": 10,
    "agent_name": "rag_agent",
    "pending_tool_call": {"name": "search_knowledge_base", "args": {"query": "휴가 정책"}},
    "should_stop": False
}
```

---

### STEP 8: Agent 조건부 라우팅 (should_continue)

**위치**: `src/systems/react/nodes.py:179-195`

#### 입력
```python
state = {
    "should_stop": False,
    "pending_tool_call": {"name": "search_knowledge_base", "args": {"query": "휴가 정책"}}
}
```

#### 처리 코드
```python
def should_continue(state: AgentState) -> str:
    if state.get("should_stop", False):      # False → 계속
        return "end"

    if state.get("pending_tool_call"):       # 있음! → tools로 분기
        return "tools"

    return "end"
```

#### 출력
```python
"tools"  # → execute_tool 노드로 이동
```

---

### STEP 9: Agent의 execute_tool 노드

**위치**: `src/systems/react/nodes.py:119-174`

#### 입력 (AgentState)
```python
state = {
    "messages": [...],
    "pending_tool_call": {"name": "search_knowledge_base", "args": {"query": "휴가 정책"}},
    ...
}
```

#### 처리 코드
```python
async def execute_tool(state: AgentState) -> Dict[str, Any]:
    tool_call = state.get("pending_tool_call")
    # {"name": "search_knowledge_base", "args": {"query": "휴가 정책"}}

    tool_name = tool_call.get("name", "")   # "search_knowledge_base"
    tool_args = tool_call.get("args", {})   # {"query": "휴가 정책"}

    tool = tools_by_name[tool_name]  # RAGTool 인스턴스

    # 도구 실행
    result = await tool._arun(**tool_args)
    # 실제 호출: await tool._arun(query="휴가 정책")

    # 결과 포맷팅
    observation_msg = f"Observation: {result}"

    return {
        "messages": [HumanMessage(content=observation_msg)],
        "pending_tool_call": None
    }
```

#### RAGTool 실행

**위치**: `src/systems/rag/rag_tool.py`

```python
class RAGTool(BaseTool):
    def _run(self, query: str) -> str:
        from src.systems.rag.vector_store import vector_store

        # 벡터 DB에서 유사 문서 검색
        docs = vector_store.similarity_search(query)
        # docs = [Document(page_content="연차휴가는...", metadata={"source": "인사규정.pdf"})]

        if not docs:
            return "No relevant documents found."

        result = "\n\n".join([
            f"Content: {doc.page_content}\nSource: {doc.metadata.get('source', 'Unknown')}"
            for doc in docs
        ])
        return f"[RAG Search Results]\n{result}"
```

#### 도구 실행 결과
```
[RAG Search Results]
Content: 연차휴가는 근속년수에 따라 차등 부여됩니다.
- 1년 미만: 월 1일
- 1년 이상: 15일
- 3년 이상: 20일
출근율 80% 이상 시 전액 부여됩니다.
Source: 인사규정.pdf
```

#### 출력 (상태 업데이트)
```python
return {
    "messages": [HumanMessage(content="Observation: [RAG Search Results]\nContent: 연차휴가는 근속년수에 따라 차등 부여됩니다...\nSource: 인사규정.pdf")],
    "pending_tool_call": None  # 클리어
}
```

#### 상태 머지 후 AgentState
```python
AgentState = {
    "messages": [
        HumanMessage(content="회사 휴가 정책 알려줘"),
        AIMessage(content="Thought: ...\nAction: search_knowledge_base\nAction Input: {...}"),
        HumanMessage(content="Observation: [RAG Search Results]\nContent: 연차휴가는...")
    ],
    "iteration": 1,
    "max_iterations": 10,
    "agent_name": "rag_agent",
    "pending_tool_call": None,  # 클리어됨
    "should_stop": False
}
```

---

### STEP 10: Agent의 call_model 노드 (2회차)

**위치**: `src/systems/react/nodes.py:39-101`

#### 입력 (AgentState)
```python
state = {
    "messages": [
        HumanMessage(content="회사 휴가 정책 알려줘"),
        AIMessage(content="Thought: ...\nAction: search_knowledge_base\nAction Input: {...}"),
        HumanMessage(content="Observation: [RAG Search Results]\nContent: 연차휴가는...")
    ],
    "iteration": 1,
    "pending_tool_call": None,
    "should_stop": False
}
```

#### LLM에 전달되는 messages
```python
[
    SystemMessage(content="당신은 내부 지식 기반 검색 전문가입니다..."),
    HumanMessage(content="회사 휴가 정책 알려줘"),
    AIMessage(content="Thought: ...\nAction: search_knowledge_base\nAction Input: {...}"),
    HumanMessage(content="Observation: [RAG Search Results]\nContent: 연차휴가는...")
]
```

#### LLM 응답 예시
```
Thought: 검색 결과를 바탕으로 회사 휴가 정책을 정리하여 답변하겠습니다.
Final Answer: 회사의 연차휴가 정책은 다음과 같습니다:

- **1년 미만 근속**: 월 1일
- **1년 이상 근속**: 연 15일
- **3년 이상 근속**: 연 20일

단, 출근율 80% 이상 시 전액 부여됩니다.

출처: 인사규정.pdf
```

#### ToolCallParser.parse() 처리
```python
# 정규식 패턴
FINAL_ANSWER_PATTERNS = [
    r'(?:Final Answer|최종 답변|답변|Answer):\s*(.+?)(?:\n\n|\n(?=Thought:)|$)',
    ...
]

# 매칭 결과
final_match = re.search(pattern, response_text, re.DOTALL)
# final_match.group(1) = "회사의 연차휴가 정책은 다음과 같습니다:..."

tool_call = None
final_answer = "회사의 연차휴가 정책은 다음과 같습니다:..."
```

#### 출력 (상태 업데이트)
```python
return {
    "messages": [AIMessage(content="회사의 연차휴가 정책은 다음과 같습니다:\n\n- **1년 미만 근속**: 월 1일...")],
    "should_stop": True,  # ← 종료 플래그!
    "pending_tool_call": None,
    "iteration": 2
}
```

#### 상태 머지 후 AgentState
```python
AgentState = {
    "messages": [
        HumanMessage(content="회사 휴가 정책 알려줘"),
        AIMessage(content="Thought: ...\nAction: search_knowledge_base\nAction Input: {...}"),
        HumanMessage(content="Observation: [RAG Search Results]\nContent: 연차휴가는..."),
        AIMessage(content="회사의 연차휴가 정책은 다음과 같습니다:\n\n- **1년 미만 근속**: 월 1일...")
    ],
    "iteration": 2,
    "max_iterations": 10,
    "agent_name": "rag_agent",
    "pending_tool_call": None,
    "should_stop": True  # 종료!
}
```

---

### STEP 11: Agent 조건부 라우팅 → END

#### 입력
```python
state = {"should_stop": True, "pending_tool_call": None}
```

#### 처리
```python
def should_continue(state: AgentState) -> str:
    if state.get("should_stop", False):  # True!
        return "end"
```

#### 출력
```python
"end"  # → Agent 그래프 종료
```

---

### STEP 12: Agent 실행 완료 → Supervisor로 복귀

**위치**: `src/systems/react/supervisor.py:264-276`

#### Agent 반환값
```python
{
    "messages": [
        HumanMessage(content="회사 휴가 정책 알려줘"),
        AIMessage(content="Thought: ..."),
        HumanMessage(content="Observation: ..."),
        AIMessage(content="회사의 연차휴가 정책은 다음과 같습니다:...")
    ],
    ...
}
```

#### execute_agent_node에서 결과 처리
```python
result = await agent.ainvoke(inputs)

# 결과 추출 (마지막 AIMessage의 content)
if result.get("messages"):
    output = result["messages"][-1].content
    # output = "회사의 연차휴가 정책은 다음과 같습니다:..."
else:
    output = "No response from agent"

return {
    "messages": [AIMessage(content=f"[{agent_name}] {output}")],
    "agent_outputs": {
        **state.get("agent_outputs", {}),
        agent_name: output
    }
}
```

#### 출력 (Supervisor 상태 업데이트)
```python
return {
    "messages": [AIMessage(content="[rag_agent] 회사의 연차휴가 정책은 다음과 같습니다:...")],
    "agent_outputs": {
        "rag_agent": "회사의 연차휴가 정책은 다음과 같습니다:..."
    }
}
```

#### 상태 머지 후 SupervisorState
```python
SupervisorState = {
    "messages": [
        HumanMessage(content="회사 휴가 정책 알려줘"),
        AIMessage(content="회사 휴가 정책에 대한 질문은...\nDelegate: rag_agent..."),
        AIMessage(content="[rag_agent] 회사의 연차휴가 정책은 다음과 같습니다:...")
    ],
    "current_agent": "rag_agent",
    "agent_outputs": {
        "rag_agent": "회사의 연차휴가 정책은 다음과 같습니다:..."
    },
    "iteration": 1,
    "max_iterations": 5
}
```

---

### STEP 13: Supervisor 라우팅 노드 (2회차)

**위치**: `src/systems/react/supervisor.py:167-233`

#### 입력 (SupervisorState)
이전 에이전트 결과가 포함된 상태

#### LLM에 전달되는 messages
```python
[
    SystemMessage(content="당신은 멀티 에이전트 시스템의 supervisor입니다..."),
    HumanMessage(content="회사 휴가 정책 알려줘"),
    AIMessage(content="회사 휴가 정책에 대한 질문은...\nDelegate: rag_agent..."),
    AIMessage(content="[rag_agent] 회사의 연차휴가 정책은 다음과 같습니다:..."),
    SystemMessage(content="\n\n이전 에이전트 결과:\n- rag_agent: 회사의 연차휴가 정책은...")
]
```

#### LLM 응답 예시
```
에이전트가 성공적으로 회사 휴가 정책 정보를 찾았습니다.

Final Answer: 회사의 연차휴가 정책은 다음과 같습니다:

- **1년 미만 근속**: 월 1일
- **1년 이상 근속**: 연 15일
- **3년 이상 근속**: 연 20일

단, 출근율 80% 이상 시 전액 부여됩니다.

출처: 인사규정.pdf
```

#### 응답 파싱
```python
final_match = re.search(r'Final Answer:\s*(.+)', response_text, re.DOTALL | re.IGNORECASE)
# final_match.group(1) = "회사의 연차휴가 정책은 다음과 같습니다:..."
```

#### 출력 (상태 업데이트)
```python
return {
    "messages": [AIMessage(content="회사의 연차휴가 정책은 다음과 같습니다:\n\n- **1년 미만 근속**: 월 1일...")],
    "current_agent": "__end__",  # 종료 신호!
    "iteration": 2
}
```

---

### STEP 14: Supervisor 조건부 라우팅 → END

#### 입력
```python
state = {"current_agent": "__end__", "iteration": 2, "max_iterations": 5}
```

#### 처리
```python
def route_next(state: SupervisorState) -> str:
    current_agent = state.get("current_agent", "__end__")  # "__end__"

    if current_agent == "__end__" or iteration >= max_iter:
        return "end"  # ← 이 경로!
```

#### 출력
```python
"end"  # → Supervisor 그래프 종료
```

---

### STEP 15: 최종 상태 반환

#### Supervisor 최종 반환값
```python
{
    "messages": [
        HumanMessage(content="회사 휴가 정책 알려줘"),
        AIMessage(content="회사 휴가 정책에 대한 질문은...\nDelegate: rag_agent..."),
        AIMessage(content="[rag_agent] 회사의 연차휴가 정책은..."),
        AIMessage(content="회사의 연차휴가 정책은 다음과 같습니다:\n\n- **1년 미만 근속**: 월 1일...")
    ],
    "current_agent": "__end__",
    "agent_outputs": {"rag_agent": "회사의 연차휴가 정책은..."},
    "iteration": 2,
    "max_iterations": 5
}
```

---

### STEP 16: HTTP 응답 생성

**위치**: `src/api/v1/chat.py:36-44`

#### 처리 코드
```python
final_state = await graph.ainvoke(inputs, config)

# 메시지 리스트에서 마지막 메시지 추출
messages = final_state["messages"]
last_message = messages[-1]
# last_message = AIMessage(content="회사의 연차휴가 정책은 다음과 같습니다:...")

return ChatResponse(
    response=last_message.content,
    tool_calls=[],
    metadata={"thread_id": request.session_id}
)
```

#### 최종 HTTP 응답
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "response": "회사의 연차휴가 정책은 다음과 같습니다:\n\n- **1년 미만 근속**: 월 1일\n- **1년 이상 근속**: 연 15일\n- **3년 이상 근속**: 연 20일\n\n단, 출근율 80% 이상 시 전액 부여됩니다.\n\n출처: 인사규정.pdf",
  "tool_calls": [],
  "metadata": {
    "thread_id": "user-session-123"
  }
}
```

---

## 5. 데이터 변환 요약

### 5.1 전체 데이터 변환 흐름표

| Step | 위치 | 입력 데이터 타입 | 출력 데이터 타입 | 핵심 변환 |
|------|------|----------------|----------------|----------|
| 1 | `chat.py` | HTTP JSON `{message, session_id}` | `inputs: {messages: [HumanMessage]}`, `config` | JSON → LangChain 메시지 |
| 2 | `supervisor.ainvoke` | `inputs` | `SupervisorState` | 초기 상태 딕셔너리 생성 |
| 3 | `supervisor_route_node` | `SupervisorState` | `{messages, current_agent, iteration}` | LLM 호출 → 라우팅 파싱 |
| 4 | `route_next` | `SupervisorState` | `"agent"` or `"end"` | 조건부 분기 결정 |
| 5 | `execute_agent_node` | `SupervisorState` | `inputs: {messages: [HumanMessage]}` | HumanMessage만 필터링 |
| 6 | `agent.ainvoke` | `inputs` | `AgentState` | 초기 상태 딕셔너리 생성 |
| 7 | `call_model` | `AgentState` | `{messages, pending_tool_call, should_stop, iteration}` | LLM 호출 → 도구/답변 파싱 |
| 8 | `should_continue` | `AgentState` | `"tools"` or `"end"` | 조건부 분기 결정 |
| 9 | `execute_tool` | `AgentState.pending_tool_call` | `{messages: [HumanMessage(Observation)], pending_tool_call: None}` | 도구 실행 → 결과 포맷팅 |
| 10 | `call_model` (2회) | `AgentState` (Observation 포함) | `{messages: [AIMessage(Final Answer)], should_stop: True}` | LLM 호출 → 최종 답변 추출 |
| 11 | `should_continue` | `should_stop: True` | `"end"` | Agent 종료 결정 |
| 12 | `execute_agent_node` (계속) | Agent 결과 | `{messages, agent_outputs}` | 에이전트 결과 집계 |
| 13 | `supervisor_route_node` (2회) | `SupervisorState` (agent_outputs 포함) | `{messages: [AIMessage], current_agent: "__end__"}` | 최종 응답 생성 |
| 14 | `route_next` | `current_agent: "__end__"` | `"end"` | Supervisor 종료 결정 |
| 15 | Graph 완료 | - | `final_state: SupervisorState` | 최종 상태 반환 |
| 16 | `chat.py` | `final_state["messages"][-1]` | HTTP JSON `{response, tool_calls, metadata}` | LangChain → JSON 변환 |

### 5.2 메시지 누적 과정

LangGraph의 `add_messages` reducer에 의해 메시지가 누적됩니다:

```
초기:
  messages: [HumanMessage("회사 휴가 정책 알려줘")]

Supervisor 라우팅 후:
  messages: [
    HumanMessage("회사 휴가 정책 알려줘"),
    AIMessage("Delegate: rag_agent...")
  ]

Agent call_model 후:
  messages: [
    HumanMessage("회사 휴가 정책 알려줘"),
    AIMessage("Thought: ...\nAction: search_knowledge_base...")
  ]

Agent execute_tool 후:
  messages: [
    HumanMessage("회사 휴가 정책 알려줘"),
    AIMessage("Thought: ...\nAction: search_knowledge_base..."),
    HumanMessage("Observation: [RAG Search Results]...")
  ]

Agent call_model (2회) 후:
  messages: [
    HumanMessage("회사 휴가 정책 알려줘"),
    AIMessage("Thought: ...\nAction: search_knowledge_base..."),
    HumanMessage("Observation: [RAG Search Results]..."),
    AIMessage("회사의 연차휴가 정책은...")  ← Final Answer
  ]
```

### 5.3 상태 업데이트 패턴

노드 함수가 반환하는 딕셔너리는 기존 상태와 **머지**됩니다:

```python
# 노드 함수 반환값
return {
    "messages": [AIMessage(content="...")],  # 기존 리스트에 추가 (add_messages)
    "iteration": 2,                           # 덮어쓰기
    "should_stop": True                       # 덮어쓰기
}

# 머지 결과
state = {
    "messages": [...기존..., AIMessage(content="...")],  # 추가됨
    "iteration": 2,                                       # 업데이트됨
    "max_iterations": 10,                                 # 유지됨 (반환 안함)
    "agent_name": "rag_agent",                           # 유지됨
    "pending_tool_call": None,                           # 유지됨 (반환 안함)
    "should_stop": True                                  # 업데이트됨
}
```

---

## 6. 기존 구조 vs 새 구조 비교

### 6.1 기존 구조 (Native Tool Calling)

```
┌─────────┐     bind_tools()      ┌─────────┐
│   LLM   │◄─────────────────────►│  Tools  │
└─────────┘   (API 레벨 바인딩)    └─────────┘
     │
     │ tool_calls 속성 (JSON 구조)
     │
     ▼
┌─────────────────────────────────────────────────┐
│ langgraph.prebuilt.create_react_agent           │
│                                                 │
│ 요구사항:                                        │
│ - LLM이 tool_calls를 OpenAI 형식 JSON으로 반환    │
│ - vLLM: --enable-auto-tool-choice 필요          │
│                                                 │
│ 문제점:                                         │
│ - Open Source 모델에서 형식 불일치               │
│ - <|python_tag|>{"type": "function"...} 반환    │
│ - BadRequestError 발생                          │
└─────────────────────────────────────────────────┘
```

### 6.2 새 구조 (Prompt-based Tool Calling)

```
┌─────────┐                       ┌─────────┐
│   LLM   │                       │  Tools  │
└─────────┘                       └─────────┘
     │                                 │
     │ 텍스트 응답                       │
     │ (Action: ...\nAction Input: {})  │
     │                                 │
     ▼                                 │
┌─────────────────────────────────────────────────┐
│ src.systems.react.create_custom_react_agent     │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ ToolCallParser.parse(text)                  │ │
│ │                                             │ │
│ │ 정규식 패턴:                                 │ │
│ │ - r'Action:\s*(\w+)\s*\n\s*Action Input:'   │ │
│ │ - r'Final Answer:\s*(.+)'                   │ │
│ │                                             │ │
│ │ JSON 파싱으로 도구 인자 추출                  │ │
│ └─────────────────────────────────────────────┘ │
│                      │                          │
│                      ▼                          │
│            execute_tool(name, args)─────────────┘
│                                                 │
│ 장점:                                           │
│ - 모든 모델에서 안정적 동작                      │
│ - API 형식 의존성 없음                          │
│ - vLLM 특수 설정 불필요                         │
└─────────────────────────────────────────────────┘
```

### 6.3 Import 변경 요약

| 파일 | 기존 Import | 새 Import |
|------|------------|----------|
| `rag_agent.py` | `from langgraph.prebuilt import create_react_agent` | `from src.systems.react import create_custom_react_agent` |
| `external_agent.py` | `from langgraph.prebuilt import create_react_agent` | `from src.systems.react import create_custom_react_agent` |
| `internal_agent.py` | `from langgraph.prebuilt import create_react_agent` | `from src.systems.react import create_custom_react_agent` |
| `build_graph.py` | `from langgraph_supervisor import create_supervisor` | `from src.systems.react import create_custom_supervisor` |

---

## 부록: 핵심 정규식 패턴

### ToolCallParser 패턴

```python
# 도구 호출 패턴
TOOL_CALL_PATTERNS = [
    # Format 1: ReAct 표준 형식
    r'Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\n\s*Action Input:\s*(\{.*?\})',

    # Format 2: XML 태그 형식
    r'<tool_call>\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*</tool_call>\s*<tool_input>\s*(\{.*?\})\s*</tool_input>',

    # Format 3: JSON 코드 블록 형식
    r'```(?:json)?\s*\{[^`]*"action"\s*:\s*"([a-zA-Z_][a-zA-Z0-9_]*)"[^`]*"action_input"\s*:\s*(\{[^`]*?\})[^`]*\}[^`]*```',
]

# 최종 답변 패턴
FINAL_ANSWER_PATTERNS = [
    r'(?:Final Answer|최종 답변|답변|Answer):\s*(.+?)(?:\n\n|\n(?=Thought:)|$)',
    r'(?:결론|결과):\s*(.+?)(?:\n\n|$)',
]
```

### Supervisor 라우팅 패턴

```python
# 에이전트 위임 패턴
delegate_pattern = r'Delegate:\s*(\w+)'

# 최종 답변 패턴
final_pattern = r'Final Answer:\s*(.+)'
```
