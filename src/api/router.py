"""API Gateway - 메인 라우터

모든 도메인별 라우터를 등록하고 관리합니다.
향후 분산 배포 시 이 파일에서 내부 호출을 외부 서비스 호출로 전환할 수 있습니다.
"""

from fastapi import APIRouter

from src.api.v1 import chat, documents, docs, settings

api_router = APIRouter()

# ============================================================
# API Gateway - 도메인별 라우터 등록
# ============================================================

# Chat 도메인: Multi-Agent 대화 시스템
api_router.include_router(
    chat.router,
    prefix="/v1/chat",
    tags=["Chat"]
)

# Documents 도메인: 문서 업로드 및 관리
api_router.include_router(
    documents.router,
    prefix="/v1/documents",
    tags=["Documents"]
)

# Docs 도메인: 기술 문서 조회
api_router.include_router(
    docs.router,
    prefix="/v1/docs",
    tags=["Docs"]
)

# Settings 도메인: API Key 등 설정 관리
api_router.include_router(
    settings.router,
    prefix="/v1/settings",
    tags=["Settings"]
)

# ============================================================
# 향후 확장 예시
# ============================================================
# from src.api.v1 import analytics
# api_router.include_router(
#     analytics.router,
#     prefix="/v1/analytics",
#     tags=["Analytics"]
# )
