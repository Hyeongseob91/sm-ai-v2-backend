"""LLM Service - LLM 인스턴스 관리

Local vLLM과 OpenAI API 두 가지 provider를 지원합니다.
settings.py의 LLM_PROVIDER 설정으로 전환할 수 있습니다.
"""

from langchain_openai import ChatOpenAI
from src.config.settings import get_settings

settings = get_settings()


class LLMService:
    """LLM 서비스 클래스

    Provider 설정에 따라 Local vLLM 또는 OpenAI API를 사용합니다.

    Usage:
        # 기본 설정 사용 (settings.py의 LLM_PROVIDER 따름)
        llm = LLMService.get_llm()

        # 특정 provider 강제 지정
        llm = LLMService.get_llm(provider="openai")
        llm = LLMService.get_llm(provider="local")

        # 파라미터 오버라이드
        llm = LLMService.get_llm(temperature=0.3, model="gpt-4o")
    """

    @staticmethod
    def get_llm(
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        **kwargs
    ) -> ChatOpenAI:
        """LLM 인스턴스를 반환합니다.

        Args:
            provider: "local" (vLLM) 또는 "openai". None이면 settings 사용
            model: 모델명. None이면 provider에 따른 기본값 사용
            temperature: 온도 설정. None이면 settings 사용
            **kwargs: ChatOpenAI에 전달할 추가 파라미터

        Returns:
            ChatOpenAI: LangChain ChatOpenAI 인스턴스

        Raises:
            ValueError: 유효하지 않은 provider인 경우
        """
        # Provider 결정
        selected_provider = provider or settings.LLM_PROVIDER

        # Temperature 결정
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE

        if selected_provider == "local":
            return LLMService._get_local_llm(model, temp, **kwargs)
        elif selected_provider == "openai":
            return LLMService._get_openai_llm(model, temp, **kwargs)
        else:
            raise ValueError(f"Unknown LLM provider: {selected_provider}. Use 'local' or 'openai'")

    @staticmethod
    def _get_local_llm(model: str | None, temperature: float, **kwargs) -> ChatOpenAI:
        """Local vLLM 인스턴스 생성"""
        model_name = model or settings.LOCAL_LLM_MODEL

        # Local vLLM은 API key가 필요 없지만, ChatOpenAI는 필수로 요구함
        api_key = settings.OPENAI_API_KEY or "dummy-key-for-local-vllm"

        return ChatOpenAI(
            base_url=settings.LOCAL_LLM_BASE_URL,
            api_key=api_key,
            model=model_name,
            temperature=temperature,
            **kwargs
        )

    @staticmethod
    def _get_openai_llm(model: str | None, temperature: float, **kwargs) -> ChatOpenAI:
        """OpenAI API 인스턴스 생성"""
        model_name = model or settings.OPENAI_MODEL

        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is required for OpenAI provider. "
                "Set it in .env file or environment variable."
            )

        # base_url이 설정되어 있으면 사용 (OpenAI 호환 API용)
        llm_kwargs = {
            "api_key": settings.OPENAI_API_KEY,
            "model": model_name,
            "temperature": temperature,
            **kwargs
        }

        if settings.OPENAI_BASE_URL:
            llm_kwargs["base_url"] = settings.OPENAI_BASE_URL

        return ChatOpenAI(**llm_kwargs)

    @staticmethod
    def get_provider() -> str:
        """현재 설정된 LLM provider를 반환합니다."""
        return settings.LLM_PROVIDER

    @staticmethod
    def get_model_info() -> dict:
        """현재 LLM 설정 정보를 반환합니다."""
        provider = settings.LLM_PROVIDER

        if provider == "local":
            return {
                "provider": "local",
                "base_url": settings.LOCAL_LLM_BASE_URL,
                "model": settings.LOCAL_LLM_MODEL,
                "temperature": settings.LLM_TEMPERATURE
            }
        else:
            return {
                "provider": "openai",
                "base_url": settings.OPENAI_BASE_URL or "https://api.openai.com/v1",
                "model": settings.OPENAI_MODEL,
                "temperature": settings.LLM_TEMPERATURE,
                "api_key_configured": bool(settings.OPENAI_API_KEY)
            }
