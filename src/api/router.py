from fastapi import APIRouter
from src.api.agent_endpoints import router as chat_router
from src.api.rag_endpoints import router as rag_router

api_router = APIRouter()

api_router.include_router(chat_router, prefix="/v1", tags=["chat"])
api_router.include_router(rag_router, prefix="/v1/rag", tags=["rag"])
