"""Chat 도메인 API 엔드포인트

Multi-Agent 대화 시스템과의 상호작용을 담당합니다.
"""

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage

from src.schema.api_schema import ChatRequest, ChatResponse
from src.api.dependencies import get_graph

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def send_message(request: ChatRequest, graph=Depends(get_graph)):
    """Multi-Agent 시스템에 메시지를 전송하고 응답을 받습니다.

    Args:
        request: 채팅 요청 (message, session_id)
        graph: Multi-Agent 그래프 인스턴스 (의존성 주입)

    Returns:
        ChatResponse: AI 응답 및 메타데이터
    """
    try:
        # 세션 설정
        config = {"configurable": {"thread_id": request.session_id}}

        # 입력 메시지 구성
        inputs = {"messages": [HumanMessage(content=request.message)]}

        # 그래프 실행
        final_state = await graph.ainvoke(inputs, config)

        # 응답 추출
        messages = final_state["messages"]
        last_message = messages[-1]

        return ChatResponse(
            response=last_message.content,
            tool_calls=[],
            metadata={"thread_id": request.session_id}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
