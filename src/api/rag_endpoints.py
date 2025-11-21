from fastapi import APIRouter, UploadFile, File, HTTPException
from src.models.api_schema import BaseResponse
from src.systems.rag.ingestion import IngestionService

router = APIRouter()
ingestion_service = IngestionService()

@router.post("/ingest", response_model=BaseResponse)
async def ingest_document(file: UploadFile = File(...)):
    try:
        num_chunks = await ingestion_service.process_file(file)
        return BaseResponse(
            success=True,
            message=f"Successfully ingested {file.filename}",
            data={"chunks_created": num_chunks}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
