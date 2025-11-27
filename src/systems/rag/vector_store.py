"""Vector Store - ChromaDB 기반 벡터 저장소

EmbeddingService를 사용하여 Local HuggingFace 또는 OpenAI Embeddings를 지원합니다.
"""

import os
from langchain_community.vectorstores import Chroma
from src.config.settings import get_settings
from src.core.embedding_service import EmbeddingService

settings = get_settings()


class VectorStore:
    """벡터 저장소 클래스 (싱글톤)

    ChromaDB를 사용하여 문서를 벡터로 저장하고 검색합니다.
    Embedding provider는 settings.py의 EMBEDDING_PROVIDER 설정을 따릅니다.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """VectorStore 초기화"""
        # Ensure directory exists
        os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)

        # EmbeddingService를 통해 embedding function 획득
        self.embedding_function = EmbeddingService.get_embeddings()

        self.client = Chroma(
            persist_directory=settings.CHROMA_DB_PATH,
            embedding_function=self.embedding_function,
            collection_name="soundmind_knowledge"
        )

    def add_documents(self, documents):
        """문서를 벡터 저장소에 추가합니다."""
        return self.client.add_documents(documents)

    def similarity_search(self, query: str, k: int = 4):
        """유사한 문서를 검색합니다."""
        return self.client.similarity_search(query, k=k)

    def similarity_search_with_score(self, query: str, k: int = 4):
        """유사한 문서를 점수와 함께 검색합니다."""
        return self.client.similarity_search_with_score(query, k=k)

    def as_retriever(self, **kwargs):
        """Retriever로 변환합니다."""
        return self.client.as_retriever(**kwargs)

    def delete(self, ids: list[str] | None = None):
        """문서를 삭제합니다."""
        if ids:
            self.client.delete(ids=ids)

    def get_collection_stats(self) -> dict:
        """컬렉션 통계를 반환합니다."""
        collection = self.client._collection
        return {
            "name": collection.name,
            "count": collection.count(),
            "embedding_provider": EmbeddingService.get_provider(),
            "embedding_model": EmbeddingService.get_model_info()
        }

    @classmethod
    def reset_instance(cls):
        """싱글톤 인스턴스를 리셋합니다. (테스트용)"""
        cls._instance = None
        EmbeddingService.clear_cache()


# Global instance
vector_store = VectorStore()
