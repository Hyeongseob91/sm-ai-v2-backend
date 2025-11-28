from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional, Literal

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Supervisor-based Multi-Agent System"
    DEBUG: bool = True

    # ==========================================================
    # LLM Configuration
    # ==========================================================
    # Provider: "local" (vLLM) or "openai" (OpenAI API)
    LLM_PROVIDER: Literal["local", "openai"] = "local"

    # Local vLLM Settings
    LOCAL_LLM_BASE_URL: str = "http://localhost:8000/v1"
    LOCAL_LLM_MODEL: str = "gpt-oss-120b"

    # OpenAI API Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Optional[str] = None  # None이면 기본 OpenAI API 사용

    # Common LLM Settings
    LLM_TEMPERATURE: float = 0.7

    # Anthropic (향후 확장용)
    ANTHROPIC_API_KEY: Optional[str] = None

    # ==========================================================
    # Web Search Configuration
    # ==========================================================
    # Tavily API (optional - enhanced web search)
    TAVILY_API_KEY: Optional[str] = None

    # ==========================================================
    # Embedding Configuration
    # ==========================================================
    # Provider: "local" (HuggingFace) or "openai" (OpenAI API)
    EMBEDDING_PROVIDER: Literal["local", "openai"] = "local"

    # Local Embedding Settings (HuggingFace)
    LOCAL_EMBEDDING_MODEL: str = "BAAI/bge-m3"
    LOCAL_EMBEDDING_DEVICE: str = "cpu"  # GPU는 vLLM이 사용 중

    # OpenAI Embedding Settings
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # ==========================================================
    # Vector DB
    # ==========================================================
    CHROMA_DB_PATH: str = "./chroma_db"
    
    # MCP Servers
    # - @antv/mcp-server-chart: 차트/다이어그램 생성 (25+ 종류)
    # - mcp-echarts: Apache ECharts 기반 전문 차트
    MCP_SERVER_URLS: list[str] = [
        "http://localhost:1122/sse",  # @antv/mcp-server-chart
        "http://localhost:3033/sse",  # mcp-echarts
    ]

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # Ignore extra fields
    )

@lru_cache
def get_settings():
    return Settings()
