"""Embedding Service - 임베딩 모델 관리

Local HuggingFace와 OpenAI Embeddings 두 가지 provider를 지원합니다.
settings.py의 EMBEDDING_PROVIDER 설정으로 전환할 수 있습니다.
"""

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from src.config.settings import get_settings

settings = get_settings()


class EmbeddingService:
    """Embedding 서비스 클래스

    Provider 설정에 따라 Local HuggingFace 또는 OpenAI Embeddings를 사용합니다.

    Usage:
        # 기본 설정 사용 (settings.py의 EMBEDDING_PROVIDER 따름)
        embeddings = EmbeddingService.get_embeddings()

        # 특정 provider 강제 지정
        embeddings = EmbeddingService.get_embeddings(provider="openai")
        embeddings = EmbeddingService.get_embeddings(provider="local")

        # 파라미터 오버라이드
        embeddings = EmbeddingService.get_embeddings(model="text-embedding-3-large")
    """

    _local_instance: HuggingFaceEmbeddings | None = None
    _openai_instance: OpenAIEmbeddings | None = None

    @classmethod
    def get_embeddings(
        cls,
        provider: str | None = None,
        model: str | None = None,
        **kwargs
    ) -> Embeddings:
        """Embedding 인스턴스를 반환합니다.

        Args:
            provider: "local" (HuggingFace) 또는 "openai". None이면 settings 사용
            model: 모델명. None이면 provider에 따른 기본값 사용
            **kwargs: Embeddings 클래스에 전달할 추가 파라미터

        Returns:
            Embeddings: LangChain Embeddings 인스턴스

        Raises:
            ValueError: 유효하지 않은 provider인 경우
        """
        selected_provider = provider or settings.EMBEDDING_PROVIDER

        if selected_provider == "local":
            return cls._get_local_embeddings(model, **kwargs)
        elif selected_provider == "openai":
            return cls._get_openai_embeddings(model, **kwargs)
        else:
            raise ValueError(
                f"Unknown embedding provider: {selected_provider}. Use 'local' or 'openai'"
            )

    @classmethod
    def _get_local_embeddings(
        cls,
        model: str | None = None,
        **kwargs
    ) -> HuggingFaceEmbeddings:
        """Local HuggingFace Embeddings 인스턴스 생성

        싱글톤 패턴으로 동일한 모델은 재사용합니다.
        """
        model_name = model or settings.LOCAL_EMBEDDING_MODEL

        # 기본 모델이고 캐시된 인스턴스가 있으면 재사용
        if model_name == settings.LOCAL_EMBEDDING_MODEL and cls._local_instance is not None:
            return cls._local_instance

        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": settings.LOCAL_EMBEDDING_DEVICE},
            encode_kwargs={"normalize_embeddings": True},
            **kwargs
        )

        # 기본 모델이면 캐시
        if model_name == settings.LOCAL_EMBEDDING_MODEL:
            cls._local_instance = embeddings

        return embeddings

    @classmethod
    def _get_openai_embeddings(
        cls,
        model: str | None = None,
        **kwargs
    ) -> OpenAIEmbeddings:
        """OpenAI Embeddings 인스턴스 생성"""
        model_name = model or settings.OPENAI_EMBEDDING_MODEL

        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is required for OpenAI embeddings. "
                "Set it in .env file or environment variable."
            )

        # 기본 모델이고 캐시된 인스턴스가 있으면 재사용
        if model_name == settings.OPENAI_EMBEDDING_MODEL and cls._openai_instance is not None:
            return cls._openai_instance

        embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            model=model_name,
            **kwargs
        )

        # 기본 모델이면 캐시
        if model_name == settings.OPENAI_EMBEDDING_MODEL:
            cls._openai_instance = embeddings

        return embeddings

    @staticmethod
    def get_provider() -> str:
        """현재 설정된 Embedding provider를 반환합니다."""
        return settings.EMBEDDING_PROVIDER

    @staticmethod
    def get_model_info() -> dict:
        """현재 Embedding 설정 정보를 반환합니다."""
        provider = settings.EMBEDDING_PROVIDER

        if provider == "local":
            return {
                "provider": "local",
                "model": settings.LOCAL_EMBEDDING_MODEL,
                "device": settings.LOCAL_EMBEDDING_DEVICE
            }
        else:
            return {
                "provider": "openai",
                "model": settings.OPENAI_EMBEDDING_MODEL,
                "api_key_configured": bool(settings.OPENAI_API_KEY)
            }

    @classmethod
    def clear_cache(cls) -> None:
        """캐시된 인스턴스를 초기화합니다."""
        cls._local_instance = None
        cls._openai_instance = None
