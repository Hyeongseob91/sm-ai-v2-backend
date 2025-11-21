from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "SoundMind AI V2"
    DEBUG: bool = True
    
    # LLM
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Vector DB
    CHROMA_DB_PATH: str = "./chroma_db"
    
    # MCP
    MCP_SERVER_URLS: list[str] = []  # List of external MCP server URLs

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # Ignore extra fields
    )

@lru_cache
def get_settings():
    return Settings()
