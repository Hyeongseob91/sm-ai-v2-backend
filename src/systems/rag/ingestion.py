import os
import shutil
from typing import List
from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from src.systems.rag.vector_store import vector_store
from src.systems.rag.loaders import ExcelLoader, PowerPointLoader
from src.systems.rag.exceptions import UnsupportedFileTypeError, FileLoadError

class IngestionService:
    # 지원하는 파일 확장자 목록
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".xlsx", ".pptx"}

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len,
        )
        self.upload_dir = "./user_uploads"
        os.makedirs(self.upload_dir, exist_ok=True)

    async def process_file(self, file: UploadFile) -> int:
        # 1. 파일 확장자 검증
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                extension=file_ext,
                supported=list(self.SUPPORTED_EXTENSIONS)
            )

        # 2. Save file temporarily
        file_path = os.path.join(self.upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            # 3. Load Documents
            documents = self._load_file(file_path)

            # 4. Split Documents
            chunks = self.text_splitter.split_documents(documents)

            # 5. Index to Vector Store
            if chunks:
                vector_store.add_documents(chunks)

            return len(chunks)
        finally:
            # 6. Cleanup
            if os.path.exists(file_path):
                os.remove(file_path)

    def _load_file(self, file_path: str) -> List[Document]:
        """파일 확장자에 따라 적절한 로더를 선택하여 문서를 로드합니다."""
        file_ext = os.path.splitext(file_path)[1].lower()

        loader_map = {
            ".pdf": lambda: PyPDFLoader(file_path),
            ".txt": lambda: TextLoader(file_path, encoding="utf-8"),
            ".docx": lambda: Docx2txtLoader(file_path),
            ".xlsx": lambda: ExcelLoader(file_path),
            ".pptx": lambda: PowerPointLoader(file_path),
        }

        loader_factory = loader_map.get(file_ext)
        if loader_factory is None:
            raise UnsupportedFileTypeError(
                extension=file_ext,
                supported=list(loader_map.keys())
            )

        try:
            loader = loader_factory()
            documents = loader.load()

            if not documents:
                raise FileLoadError(file_path, "No content extracted from file")
            return documents

        except (UnsupportedFileTypeError, FileLoadError):
            raise
        except Exception as e:
            raise FileLoadError(file_path, str(e))
