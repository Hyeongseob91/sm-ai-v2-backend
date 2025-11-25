"""External Agent - 외부 시스템 연동 전문 에이전트"""

from langgraph.prebuilt import create_react_agent
from src.core.llm_service import LLMService
from src.systems.calling_tools import get_external_tools

EXTERNAL_AGENT_PROMPT = """당신은 외부 시스템 연동 전문가입니다.

## 역할
- MCP(Model Context Protocol) 도구를 사용하여 외부 시스템과 상호작용합니다.
- 파일 시스템 작업, 외부 API 호출 등을 수행합니다.

## 사용 도구
- MCP 서버에서 제공하는 다양한 외부 도구들
- 파일 목록 조회, 디렉토리 탐색 등

## 작업 지침
1. 사용자 요청에 맞는 적절한 외부 도구를 선택하세요.
2. 도구를 실행하고 결과를 확인하세요.
3. 결과를 사용자가 이해하기 쉽게 정리하여 전달하세요.
4. 오류 발생 시 원인을 설명하고 대안을 제시하세요.
"""


async def create_external_agent():
    """External Agent 생성 - 외부 시스템 연동 전문"""
    llm = LLMService.get_llm()
    tools = await get_external_tools()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        name="external_agent",
        prompt=EXTERNAL_AGENT_PROMPT
    )
    return agent
