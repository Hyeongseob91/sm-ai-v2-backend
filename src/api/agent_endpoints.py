from fastapi import APIRouter, HTTPException
from src.models.api_schema import ChatRequest, ChatResponse
from src.systems.agent.build_graph import build_graph
from langchain_core.messages import HumanMessage

router = APIRouter()

# Cache the graph to avoid rebuilding on every request
_graph_app = None

async def get_graph():
    global _graph_app
    if _graph_app is None:
        _graph_app = await build_graph()
    return _graph_app

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        app = await get_graph()
        
        # Config for the session
        config = {"configurable": {"thread_id": request.session_id}}
        
        # Input message
        inputs = {"messages": [HumanMessage(content=request.message)]}
        
        # Invoke the graph
        # For streaming, we would use astream_events
        final_state = await app.ainvoke(inputs, config)
        
        # Extract response
        messages = final_state["messages"]
        last_message = messages[-1]
        
        return ChatResponse(
            response=last_message.content,
            tool_calls=[], # We could extract tool calls from history if needed
            metadata={"thread_id": request.session_id}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
