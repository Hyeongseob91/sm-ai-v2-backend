# API 명세서

sm-ai-v2-backend Multi-Agent 시스템의 REST API 명세서입니다.

---

## 목차

1. [개요](#1-개요)
2. [기본 정보](#2-기본-정보)
3. [API 엔드포인트](#3-api-엔드포인트)
4. [데이터 스키마](#4-데이터-스키마)
5. [에러 처리](#5-에러-처리)
6. [사용 예시](#6-사용-예시)

---

## 1. 개요

### 1.1 시스템 설명

sm-ai-v2-backend는 Multi-Agent 기반의 대화형 AI 시스템입니다. Supervisor 패턴을 사용하여 RAG, 외부 시스템 연동, 내부 분석 등 전문 에이전트를 조율합니다.

### 1.2 주요 기능

- **Chat API**: Multi-Agent 시스템과의 대화
- **Documents API**: RAG를 위한 문서 업로드 및 인덱싱

---

## 2. 기본 정보

### 2.1 Base URL

```
http://localhost:8080
```

### 2.2 Content-Type

모든 요청과 응답은 `application/json` 형식을 사용합니다.

```
Content-Type: application/json
```

### 2.3 인증

현재 버전에서는 인증이 필요하지 않습니다.

---

## 3. API 엔드포인트

### 3.1 Health Check

서버 상태를 확인합니다.

#### Request

```http
GET /health
```

#### Response

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | 서버 정상 동작 |

---

### 3.2 Chat API

Multi-Agent 시스템에 메시지를 전송하고 응답을 받습니다.

#### Request

```http
POST /v1/chat
Content-Type: application/json
```

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | 사용자 메시지 |
| `session_id` | string | Yes | 세션 식별자 (대화 히스토리 관리용) |

```json
{
  "message": "회사 휴가 정책 알려줘",
  "session_id": "user-session-123"
}
```

#### Response

```json
{
  "response": "회사의 연차휴가 정책은 다음과 같습니다:\n\n- 1년 미만 근속: 월 1일\n- 1년 이상 근속: 연 15일\n- 3년 이상 근속: 연 20일\n\n단, 출근율 80% 이상 시 전액 부여됩니다.",
  "tool_calls": [],
  "metadata": {
    "thread_id": "user-session-123"
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | AI 응답 메시지 |
| `tool_calls` | array | 사용된 도구 호출 정보 (현재 빈 배열) |
| `metadata` | object | 메타데이터 |
| `metadata.thread_id` | string | 세션 ID |

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | 성공 |
| 500 | 서버 내부 오류 |

#### Error Response

```json
{
  "detail": "Error message description"
}
```

---

### 3.3 Documents Upload API

RAG 검색을 위한 문서를 업로드합니다. 문서는 자동으로 청크로 분할되어 벡터 데이터베이스에 저장됩니다.

#### Request

```http
POST /v1/documents/upload
Content-Type: multipart/form-data
```

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | 업로드할 문서 파일 |

#### Supported File Types

| Extension | MIME Type | Description |
|-----------|-----------|-------------|
| `.pdf` | application/pdf | PDF 문서 |
| `.txt` | text/plain | 텍스트 파일 |
| `.docx` | application/vnd.openxmlformats-officedocument.wordprocessingml.document | Word 문서 |
| `.xlsx` | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | Excel 스프레드시트 |
| `.pptx` | application/vnd.openxmlformats-officedocument.presentationml.presentation | PowerPoint 프레젠테이션 |

#### Response (Success)

```json
{
  "success": true,
  "message": "Successfully uploaded document.pdf",
  "data": {
    "chunks_created": 15
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | 성공 여부 |
| `message` | string | 결과 메시지 |
| `data` | object | 추가 데이터 |
| `data.chunks_created` | integer | 생성된 청크 수 |

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | 성공 |
| 400 | 지원하지 않는 파일 형식 |
| 422 | 파일 로드 실패 |
| 500 | 서버 내부 오류 |

#### Error Responses

**지원하지 않는 파일 형식 (400)**
```json
{
  "detail": {
    "error": "unsupported_file_type",
    "message": "Unsupported file type: .mp4",
    "supported_types": [".pdf", ".txt", ".docx", ".xlsx", ".pptx"]
  }
}
```

**파일 로드 실패 (422)**
```json
{
  "detail": {
    "error": "file_load_error",
    "message": "Failed to load file: corrupted PDF"
  }
}
```

---

## 4. 데이터 스키마

### 4.1 ChatRequest

```python
class ChatRequest(BaseModel):
    message: str          # 사용자 메시지 (필수)
    session_id: str       # 세션 ID (필수)
```

### 4.2 ChatResponse

```python
class ChatResponse(BaseModel):
    response: str                          # AI 응답 메시지
    tool_calls: List[Dict[str, Any]] = []  # 도구 호출 정보
    metadata: Dict[str, Any] = {}          # 메타데이터
```

### 4.3 BaseResponse

```python
class BaseResponse(BaseModel):
    success: bool = True                   # 성공 여부
    message: Optional[str] = None          # 결과 메시지
    data: Optional[Dict[str, Any]] = None  # 추가 데이터
```

---

## 5. 에러 처리

### 5.1 공통 에러 응답 형식

```json
{
  "detail": "에러 메시지 또는 에러 객체"
}
```

### 5.2 HTTP 상태 코드

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | 요청 성공 |
| 400 | Bad Request | 잘못된 요청 (파일 형식 오류 등) |
| 422 | Unprocessable Entity | 처리 불가 (파일 로드 실패 등) |
| 500 | Internal Server Error | 서버 내부 오류 |

### 5.3 에러 타입

| Error Type | HTTP Code | Description |
|------------|-----------|-------------|
| `unsupported_file_type` | 400 | 지원하지 않는 파일 형식 |
| `file_load_error` | 422 | 파일 로드/파싱 실패 |

---

## 6. 사용 예시

### 6.1 Chat API - curl

```bash
# 기본 대화
curl -X POST http://localhost:8080/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "회사 휴가 정책 알려줘",
    "session_id": "user-001"
  }'

# 연속 대화 (같은 session_id 사용)
curl -X POST http://localhost:8080/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "특별휴가는 어떻게 되나요?",
    "session_id": "user-001"
  }'
```

### 6.2 Chat API - Python

```python
import requests

# API 엔드포인트
url = "http://localhost:8080/v1/chat"

# 요청 데이터
payload = {
    "message": "프로젝트 문서에서 보안 관련 정책을 찾아줘",
    "session_id": "python-session-001"
}

# API 호출
response = requests.post(url, json=payload)
result = response.json()

print(result["response"])
```

### 6.3 Documents Upload - curl

```bash
# PDF 문서 업로드
curl -X POST http://localhost:8080/v1/documents/upload \
  -F "file=@/path/to/document.pdf"

# Word 문서 업로드
curl -X POST http://localhost:8080/v1/documents/upload \
  -F "file=@/path/to/report.docx"
```

### 6.4 Documents Upload - Python

```python
import requests

url = "http://localhost:8080/v1/documents/upload"

# 파일 업로드
with open("인사규정.pdf", "rb") as f:
    files = {"file": ("인사규정.pdf", f, "application/pdf")}
    response = requests.post(url, files=files)

result = response.json()
print(f"Success: {result['success']}")
print(f"Chunks created: {result['data']['chunks_created']}")
```

### 6.5 Health Check - curl

```bash
curl http://localhost:8080/health
```

---

## 부록: API 라우팅 구조

```
/
├── /health                    GET   - Health Check
└── /v1
    ├── /chat                  POST  - Chat API
    └── /documents
        └── /upload            POST  - Document Upload
```

### FastAPI 자동 문서

서버 실행 시 자동 생성되는 API 문서:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json
