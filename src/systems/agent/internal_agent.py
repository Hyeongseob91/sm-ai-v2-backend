"""Internal Agent - 내부 분석 및 처리 전문 에이전트

LangGraph의 prebuilt create_react_agent를 사용합니다.
vLLM의 native tool calling으로 동작합니다.
"""

from langgraph.prebuilt import create_react_agent
from src.core.llm_service import LLMService
from src.systems.calling_tools import get_internal_tools

INTERNAL_AGENT_PROMPT = """당신은 내부 분석 및 처리 전문가입니다.

## 역할
- 데이터 분석 및 처리 작업을 수행합니다.
- 내부 비즈니스 로직을 실행합니다.
- 계산, 변환, 집계 등의 작업을 담당합니다.

## 사용 도구
- 내부 분석 도구들 (향후 추가 예정)

## 도구 사용 기준
- 도구가 필요한 복잡한 작업에만 도구를 사용하세요.
- 간단한 계산이나 분석은 직접 수행할 수 있습니다.
- 단순한 인사나 일반적인 대화에는 도구를 사용하지 마세요.

## 작업 지침
1. 요청이 도구 사용이 필요한지 판단하세요.
2. 도구 없이 처리 가능한 경우 직접 분석/계산하세요.
3. 도구가 필요한 경우에만 적절한 도구를 선택하세요.
4. 결과를 명확하고 이해하기 쉽게 설명하세요.

## 참고
현재 내부 도구가 제한적입니다. 도구 없이도 일반적인 분석과 계산은 수행할 수 있습니다.
"""


async def create_internal_agent():
    """Internal Agent 생성 - 내부 분석 및 처리 전문

    LangGraph의 prebuilt create_react_agent를 사용하여
    vLLM의 native tool calling으로 동작합니다.
    """
    llm = LLMService.get_llm()
    tools = await get_internal_tools()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        name="internal_agent",
        prompt=INTERNAL_AGENT_PROMPT
    )
    return agent
