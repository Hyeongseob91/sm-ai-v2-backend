from typing import Annotated, Sequence, TypedDict, Union
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from src.core.llm_service import LLMService
from src.systems.agent.calling_tools import get_all_tools

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

async def call_model(state: AgentState, config: RunnableConfig):
    messages = state["messages"]
    
    # Get LLM
    llm = LLMService.get_llm()
    
    # Bind Tools
    tools = await get_all_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    # Invoke
    response = await llm_with_tools.ainvoke(messages, config)
    
    return {"messages": [response]}
