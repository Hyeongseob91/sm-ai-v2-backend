"""RAG Agent - 내부 문서 검색 전문 에이전트

LangGraph의 prebuilt create_react_agent를 사용합니다.
vLLM의 native tool calling으로 동작합니다.
"""

from langgraph.prebuilt import create_react_agent
from src.core.llm_service import LLMService
from src.systems.calling_tools import get_rag_tools

RAG_AGENT_PROMPT = """당신은 내부 지식 기반 검색 전문가입니다.

## 역할
- 회사 정책, 프로젝트 문서, 내부 데이터에 대한 질문에 답변합니다.
- 업로드된 문서에서 관련 정보를 검색합니다.

## 사용 도구
- search_knowledge_base: 벡터 데이터베이스에서 관련 문서를 검색합니다.

## 도구 사용 기준
- 회사 정책, 프로젝트 문서, 업로드된 자료에 대한 구체적인 질문에만 도구를 사용하세요.
- 단순한 인사나 일반 상식 질문에는 도구를 사용하지 마세요.

## 작업 지침
1. 질문이 내부 문서 검색이 필요한지 판단하세요.
2. 필요한 경우에만 search_knowledge_base 도구를 사용하세요.
3. 검색 결과를 바탕으로 정확한 답변을 제공하세요.
4. 검색 결과가 없으면 솔직하게 "관련 문서를 찾지 못했습니다"라고 답하세요.
"""


async def create_rag_agent():
    """RAG Agent 생성 - 내부 문서 검색 전문

    LangGraph의 prebuilt create_react_agent를 사용하여
    vLLM의 native tool calling으로 동작합니다.
    """
    llm = LLMService.get_llm()
    tools = await get_rag_tools()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        name="rag_agent",
        prompt=RAG_AGENT_PROMPT
    )
    return agent
