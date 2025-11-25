"""RAG 시스템 커스텀 예외 클래스"""


class RAGException(Exception):
    """RAG 시스템 기본 예외"""
    pass


class UnsupportedFileTypeError(RAGException):
    """지원하지 않는 파일 형식 예외"""

    def __init__(self, extension: str, supported: list[str]):
        self.extension = extension
        self.supported = supported
        message = f"Unsupported file type: {extension}. Supported types: {', '.join(supported)}"
        super().__init__(message)


class FileLoadError(RAGException):
    """파일 로드 실패 예외"""

    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        message = f"Failed to load file '{file_path}': {reason}"
        super().__init__(message)
