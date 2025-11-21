from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from src.config.settings import get_settings

settings = get_settings()

class LLMService:
    @staticmethod
    def get_llm(model_name: str = "gpt-4-turbo-preview", temperature: float = 0.7):
        if "gpt" in model_name:
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=settings.OPENAI_API_KEY
            )
        elif "claude" in model_name:
            return ChatAnthropic(
                model=model_name,
                temperature=temperature,
                api_key=settings.ANTHROPIC_API_KEY
            )
        else:
            # Fallback or support for local models via Ollama
            return ChatOpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama",
                model=model_name,
                temperature=temperature
            )
