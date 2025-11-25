"""Documents 도메인 API 엔드포인트

문서 업로드, 관리, 검색 기능을 담당합니다.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException

from src.schema.api_schema import BaseResponse
from src.systems.rag.ingestion import IngestionService
from src.systems.rag.exceptions import UnsupportedFileTypeError, FileLoadError

router = APIRouter()

# 문서 수집 서비스 인스턴스
_ingestion_service = IngestionService()


@router.post("/upload", response_model=BaseResponse)
async def upload_document(file: UploadFile = File(...)):
    """문서를 업로드하고 벡터 데이터베이스에 저장합니다.

    지원 파일 형식: .pdf, .txt, .docx, .xlsx, .pptx

    Args:
        file: 업로드할 문서 파일

    Returns:
        BaseResponse: 업로드 결과 및 생성된 청크 수
    """
    try:
        num_chunks = await _ingestion_service.process_file(file)
        return BaseResponse(
            success=True,
            message=f"Successfully uploaded {file.filename}",
            data={"chunks_created": num_chunks}
        )
    except UnsupportedFileTypeError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsupported_file_type",
                "message": str(e),
                "supported_types": list(IngestionService.SUPPORTED_EXTENSIONS)
            }
        )
    except FileLoadError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "file_load_error",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
