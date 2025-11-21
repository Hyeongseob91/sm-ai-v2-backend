import os
import shutil
from typing import List
from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.systems.rag.vector_store import vector_store

class IngestionService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.upload_dir = "./uploads"
        os.makedirs(self.upload_dir, exist_ok=True)

    async def process_file(self, file: UploadFile) -> int:
        # 1. Save file temporarily
        file_path = os.path.join(self.upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            # 2. Load Documents
            documents = self._load_file(file_path)
            
            # 3. Split Documents
            chunks = self.text_splitter.split_documents(documents)
            
            # 4. Index to Vector Store
            if chunks:
                vector_store.add_documents(chunks)
            
            return len(chunks)
        finally:
            # 5. Cleanup
            if os.path.exists(file_path):
                os.remove(file_path)

    def _load_file(self, file_path: str) -> List[Document]:
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding="utf-8")
        return loader.load()
