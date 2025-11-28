"""Settings API - API Key Management

.env 파일에서 API Key를 관리합니다.
"""

import re
from fastapi import APIRouter, HTTPException
from pathlib import Path
from pydantic import BaseModel

router = APIRouter()

# 프로젝트 루트의 .env 파일 경로
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class ApiKeyRequest(BaseModel):
    """API Key 저장 요청"""
    api_key: str


class ApiKeyStatusResponse(BaseModel):
    """API Key 상태 응답"""
    exists: bool


class SuccessResponse(BaseModel):
    """성공 응답"""
    success: bool


def read_env_file() -> str:
    """Read .env file content"""
    if ENV_FILE_PATH.exists():
        return ENV_FILE_PATH.read_text(encoding='utf-8')
    return ""


def write_env_file(content: str) -> None:
    """Write content to .env file"""
    ENV_FILE_PATH.write_text(content, encoding='utf-8')


def get_openai_api_key() -> str | None:
    """Get OPENAI_API_KEY from .env file"""
    content = read_env_file()
    match = re.search(r'^OPENAI_API_KEY=(.+)$', content, re.MULTILINE)
    if match:
        value = match.group(1).strip()
        # Remove quotes if present
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        return value if value else None
    return None


def set_openai_api_key(api_key: str) -> None:
    """Set OPENAI_API_KEY in .env file"""
    content = read_env_file()

    # Check if OPENAI_API_KEY already exists
    if re.search(r'^OPENAI_API_KEY=', content, re.MULTILINE):
        # Replace existing value
        content = re.sub(
            r'^OPENAI_API_KEY=.*$',
            f'OPENAI_API_KEY={api_key}',
            content,
            flags=re.MULTILINE
        )
    else:
        # Add new line
        if content and not content.endswith('\n'):
            content += '\n'
        content += f'OPENAI_API_KEY={api_key}\n'

    write_env_file(content)


def delete_openai_api_key() -> None:
    """Delete OPENAI_API_KEY from .env file"""
    content = read_env_file()

    # Remove OPENAI_API_KEY line
    content = re.sub(r'^OPENAI_API_KEY=.*\n?', '', content, flags=re.MULTILINE)

    write_env_file(content)


@router.post("/api-key", response_model=SuccessResponse)
async def save_api_key(request: ApiKeyRequest):
    """API Key 저장"""
    try:
        if not request.api_key or not request.api_key.strip():
            raise HTTPException(status_code=400, detail="API key is required")

        set_openai_api_key(request.api_key.strip())
        return SuccessResponse(success=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api-key/status", response_model=ApiKeyStatusResponse)
async def get_api_key_status():
    """API Key 존재 여부 확인"""
    try:
        api_key = get_openai_api_key()
        return ApiKeyStatusResponse(exists=bool(api_key))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api-key", response_model=SuccessResponse)
async def remove_api_key():
    """API Key 삭제"""
    try:
        delete_openai_api_key()
        return SuccessResponse(success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
