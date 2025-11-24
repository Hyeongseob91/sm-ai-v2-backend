from langchain_openai import ChatOpenAI
from src.config.settings import get_settings

settings = get_settings()

class LLMService:
    @staticmethod
    def get_llm(model_name: str, temperature: float = 0.7):
        """
        Get LLM instance
        """
        api_key_value = settings.OPENAI_API_KEY if settings.OPENAI_API_KEY else "dummies"
        return ChatOpenAI(
            base_url="http://localhost:8000/v1",
            api_key=api_key_value,
            model=model_name,
            temperature=temperature
        )