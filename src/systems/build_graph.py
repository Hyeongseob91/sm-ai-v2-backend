"""Multi-Agent Supervisor 그래프 빌더

Supervisor 패턴을 사용하여 3개의 전문 에이전트를 조율합니다:
- RAG Agent: 내부 문서 검색
- External Agent: 외부 시스템 연동 (MCP)
- Internal Agent: 내부 분석 및 처리
"""

from langgraph_supervisor import create_supervisor
from src.systems.agent.rag_agent import create_rag_agent
from src.systems.agent.external_agent import create_external_agent
from src.systems.agent.internal_agent import create_internal_agent
from src.systems.agent.supervisor import SUPERVISOR_PROMPT
from src.core.llm_service import LLMService
from src.core.session_manager import SessionManager


async def build_graph():
    """Multi-Agent Supervisor 그래프 생성"""
    # 1. Supervisor용 LLM 준비
    llm = LLMService.get_llm()

    # 2. Sub-Agents 생성
    rag_agent = await create_rag_agent()
    external_agent = await create_external_agent()
    internal_agent = await create_internal_agent()

    # 3. Supervisor 워크플로우 생성
    workflow = create_supervisor(
        agents=[rag_agent, external_agent, internal_agent],
        model=llm,
        prompt=SUPERVISOR_PROMPT,
        output_mode="full_history"  # 전체 대화 히스토리 유지
    )

    # 4. 체크포인터로 컴파일
    checkpointer = SessionManager.get_checkpointer("global")
    app = workflow.compile(checkpointer=checkpointer)

    return app
