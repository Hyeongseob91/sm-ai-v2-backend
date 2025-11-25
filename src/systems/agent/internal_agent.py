"""Internal Agent - 내부 분석 및 처리 전문 에이전트"""

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

## 작업 지침
1. 사용자의 분석 요청을 정확히 이해하세요.
2. 적절한 분석 방법을 선택하고 실행하세요.
3. 결과를 명확하고 이해하기 쉽게 설명하세요.
4. 필요시 시각화나 요약을 제공하세요.

## 참고
현재 내부 도구가 제한적입니다. 도구 없이도 일반적인 분석과 계산은 수행할 수 있습니다.
"""


async def create_internal_agent():
    """Internal Agent 생성 - 내부 분석 및 처리 전문"""
    llm = LLMService.get_llm()
    tools = await get_internal_tools()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        name="internal_agent",
        prompt=INTERNAL_AGENT_PROMPT
    )
    return agent
