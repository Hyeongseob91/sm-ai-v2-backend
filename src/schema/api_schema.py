from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str
    session_id: str
    model_name: str = "gpt-4-turbo-preview"

class ChatResponse(BaseModel):
    response: str
    tool_calls: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
