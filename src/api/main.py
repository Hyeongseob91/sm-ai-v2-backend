from fastapi import FastAPI
from src.api.router import api_router
from src.config.settings import get_settings
from src.core.mcp_manager import mcp_manager
from contextlib import asynccontextmanager

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print(f"Starting {settings.APP_NAME}...")
    await mcp_manager.initialize()
    yield
    # Shutdown logic
    print("Shutting down...")
    await mcp_manager.cleanup()

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
