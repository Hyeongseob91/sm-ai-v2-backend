from langgraph.checkpoint.memory import MemorySaver
from typing import Dict

class SessionManager:
    _checkpointers: Dict[str, MemorySaver] = {}

    @classmethod
    def get_checkpointer(cls, session_id: str) -> MemorySaver:
        # In a real app, this might connect to Postgres or Redis.
        # For now, we use in-memory persistence per session logic if needed,
        # but LangGraph usually takes a checkpointer instance passed to the graph.
        # Here we can return a singleton or specific instance.
        
        # Actually, MemorySaver is usually shared or instantiated once per app if it's in-memory.
        # If we want persistence across restarts, we need SqliteSaver or PostgresSaver.
        # For this MVP, we'll return a new MemorySaver if not exists, but note that 
        # MemorySaver in LangGraph is designed to store state for multiple thread_ids.
        
        if "global" not in cls._checkpointers:
            cls._checkpointers["global"] = MemorySaver()
        return cls._checkpointers["global"]
