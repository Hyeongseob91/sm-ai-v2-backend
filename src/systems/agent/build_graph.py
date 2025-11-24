from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from src.systems.agent.build_agent import AgentState, call_model
from src.systems.agent.calling_tools import get_all_tools
from src.core.session_manager import SessionManager

async def build_graph():
    # 1. Define Tools
    tools = await get_all_tools()
    tool_node = ToolNode(tools)

    # 2. Define Graph
    workflow = StateGraph(AgentState)

    # 3. Add Nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    # 4. Define Edges
    workflow.set_entry_point("agent")

    def should_continue(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )

    workflow.add_edge("tools", "agent")

    # 5. Compile with Checkpointer
    # Note: In a real request, we might get the checkpointer based on session_id dynamically,
    # but compile() happens once. 
    # Usually, we compile the graph once and pass the checkpointer config at runtime (invoke/stream).
    # However, to use a checkpointer, we need to pass it to compile().
    checkpointer = SessionManager.get_checkpointer("global")
    
    app = workflow.compile(checkpointer=checkpointer)
    return app
