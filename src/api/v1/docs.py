"""Documentation API - Markdown 문서 제공

docs 폴더와 README.md 파일의 내용을 API로 제공합니다.
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
from pydantic import BaseModel

router = APIRouter()

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
README_PATH = PROJECT_ROOT / "README.md"


class DocInfo(BaseModel):
    """문서 정보"""
    id: str
    title: str
    filename: str


class DocContent(BaseModel):
    """문서 내용"""
    id: str
    title: str
    filename: str
    content: str


class DocsListResponse(BaseModel):
    """문서 목록 응답"""
    readme: DocInfo
    docs: list[DocInfo]


def extract_title_from_md(content: str, filename: str) -> str:
    """마크다운 파일에서 제목 추출"""
    lines = content.strip().split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
    # 제목이 없으면 파일명에서 생성
    return filename.replace('_', ' ').replace('.md', '').title()


@router.get("", response_model=DocsListResponse)
async def get_docs_list():
    """문서 목록 조회"""
    docs_list = []

    # README 정보
    readme_info = DocInfo(
        id="readme",
        title="Tech Stack Overview",
        filename="README.md"
    )

    # docs 폴더의 md 파일 목록
    if DOCS_DIR.exists():
        for md_file in sorted(DOCS_DIR.glob("*.md")):
            try:
                content = md_file.read_text(encoding='utf-8')
                title = extract_title_from_md(content, md_file.name)
                doc_id = md_file.stem.lower()

                docs_list.append(DocInfo(
                    id=doc_id,
                    title=title,
                    filename=md_file.name
                ))
            except Exception:
                continue

    return DocsListResponse(
        readme=readme_info,
        docs=docs_list
    )


@router.get("/readme", response_model=DocContent)
async def get_readme():
    """README.md 내용 조회"""
    if not README_PATH.exists():
        raise HTTPException(status_code=404, detail="README.md not found")

    try:
        content = README_PATH.read_text(encoding='utf-8')
        title = extract_title_from_md(content, "README.md")

        return DocContent(
            id="readme",
            title=title,
            filename="README.md",
            content=content
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}", response_model=DocContent)
async def get_doc_content(doc_id: str):
    """특정 문서 내용 조회"""
    if doc_id == "readme":
        return await get_readme()

    # docs 폴더에서 파일 찾기
    if DOCS_DIR.exists():
        for md_file in DOCS_DIR.glob("*.md"):
            if md_file.stem.lower() == doc_id:
                try:
                    content = md_file.read_text(encoding='utf-8')
                    title = extract_title_from_md(content, md_file.name)

                    return DocContent(
                        id=doc_id,
                        title=title,
                        filename=md_file.name,
                        content=content
                    )
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")
