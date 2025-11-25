import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from src.config.settings import get_settings
import os

settings = get_settings()

class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Ensure directory exists
        os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
        
        self.embedding_function = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": settings.EMBEDDING_DEVICE},
            encode_kwargs={"normalize_embeddings": True}
        )
        
        self.client = Chroma(
            persist_directory=settings.CHROMA_DB_PATH,
            embedding_function=self.embedding_function,
            collection_name="soundmind_knowledge"
        )

    def add_documents(self, documents):
        return self.client.add_documents(documents)

    def similarity_search(self, query: str, k: int = 4):
        return self.client.similarity_search(query, k=k)

    def as_retriever(self):
        return self.client.as_retriever()

# Global instance
vector_store = VectorStore()
