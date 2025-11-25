"""RAG Agent - 내부 문서 검색 전문 에이전트"""

from langgraph.prebuilt import create_react_agent
from src.core.llm_service import LLMService
from src.systems.calling_tools import get_rag_tools

RAG_AGENT_PROMPT = """당신은 내부 지식 기반 검색 전문가입니다.

## 역할
- 회사 정책, 프로젝트 문서, 내부 데이터에 대한 질문에 답변합니다.
- 업로드된 문서에서 관련 정보를 검색합니다.

## 사용 도구
- search_knowledge_base: 벡터 데이터베이스에서 관련 문서를 검색합니다.

## 작업 지침
1. 사용자 질문에서 핵심 키워드를 파악하세요.
2. search_knowledge_base 도구를 사용하여 관련 문서를 검색하세요.
3. 검색 결과를 바탕으로 정확하고 유용한 답변을 제공하세요.
4. 출처가 있다면 함께 언급하세요.
"""


async def create_rag_agent():
    """RAG Agent 생성 - 내부 문서 검색 전문"""
    llm = LLMService.get_llm()
    tools = await get_rag_tools()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        name="rag_agent",
        prompt=RAG_AGENT_PROMPT
    )
    return agent
