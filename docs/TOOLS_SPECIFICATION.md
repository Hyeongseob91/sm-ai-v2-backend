# Tools 명세서

sm-ai-v2-backend Multi-Agent 시스템에서 사용하는 도구(Tools)에 대한 명세서입니다.

---

## 목차

1. [도구 분류 체계](#1-도구-분류-체계)
2. [내부 도구 (사내 시스템)](#2-내부-도구-사내-시스템)
3. [외부 도구 (MCP 서버)](#3-외부-도구-mcp-서버)
4. [MCP 도구 선정 이유](#4-mcp-도구-선정-이유)
5. [도구 설치 및 실행](#5-도구-설치-및-실행)

---

## 1. 도구 분류 체계

### 1.1 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Multi-Agent System                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         SUPERVISOR                                   │   │
│  └────────────────────────────┬────────────────────────────────────────┘   │
│                               │                                             │
│         ┌─────────────────────┼─────────────────────┐                      │
│         ▼                     ▼                     ▼                      │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                │
│  │  RAG Agent  │      │  External   │      │  Internal   │                │
│  │             │      │   Agent     │      │   Agent     │                │
│  └──────┬──────┘      └──────┬──────┘      └──────┬──────┘                │
│         │                    │                    │                        │
│         ▼                    ▼                    ▼                        │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                │
│  │ 사내 RAG    │      │ MCP Tools   │      │ Internal    │                │
│  │ (ChromaDB)  │      │ (외부 서버) │      │ Tools       │                │
│  │             │      │             │      │             │                │
│  │ ★ 우선 적용 │      │ - 차트 생성 │      │ - 분석 도구 │                │
│  │             │      │ - 시각화    │      │ (향후 확장) │                │
│  └─────────────┘      └─────────────┘      └─────────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 도구 분류

| 분류 | 담당 에이전트 | 도구 유형 | 우선순위 |
|------|--------------|----------|---------|
| **내부 도구** | RAG Agent | 사내 RAG 시스템 | **최우선** |
| **외부 도구** | External Agent | MCP 서버 도구 | 보조 |
| **분석 도구** | Internal Agent | 데이터 처리 | 보조 |

---

## 2. 내부 도구 (사내 시스템)

### 2.1 RAG Tool (사내 문서 검색)

**★ 사내 RAG 시스템은 외부 MCP보다 우선 적용됩니다.**

#### 우선 적용 이유

| 항목 | 사내 RAG | 외부 MCP |
|------|----------|----------|
| **데이터 보안** | ✅ 로컬 처리, 외부 유출 없음 | △ 외부 서버 의존 가능성 |
| **커스터마이징** | ✅ 사내 요구사항에 최적화 | △ 범용적 설계 |
| **성능** | ✅ 로컬 ChromaDB로 빠른 응답 | △ 네트워크 지연 |
| **관리 용이성** | ✅ 직접 제어 가능 | △ 외부 의존성 |
| **비용** | ✅ 무료 (로컬) | △ 외부 서비스 비용 가능성 |

#### 도구 정보

```python
# 파일: src/systems/rag/rag_tool.py

class RAGTool(BaseTool):
    name = "search_knowledge_base"
    description = "Use this tool to search for internal documents and knowledge..."

    def _run(self, query: str) -> str:
        docs = vector_store.similarity_search(query)
        return formatted_results
```

#### 사용 대상

- 회사 정책 문서
- 프로젝트 문서
- 업로드된 내부 자료
- 기술 문서 및 매뉴얼

#### 지원 파일 형식

| 형식 | 확장자 | 설명 |
|------|--------|------|
| PDF | `.pdf` | 문서, 보고서 |
| 텍스트 | `.txt` | 일반 텍스트 |
| Word | `.docx` | Microsoft Word |
| Excel | `.xlsx` | 스프레드시트 |
| PowerPoint | `.pptx` | 프레젠테이션 |

---

## 3. 외부 도구 (MCP 서버)

### 3.1 @antv/mcp-server-chart

**GitHub**: https://github.com/antvis/mcp-server-chart

#### 개요

AntV 기반의 차트 및 다이어그램 생성 도구입니다. 25종 이상의 시각화를 지원합니다.

#### 지원 차트 (25+)

| 카테고리 | 차트 종류 |
|----------|----------|
| **기본** | 영역(Area), 막대(Bar), 열(Column), 선(Line), 산점도(Scatter), 파이(Pie) |
| **통계** | 박스플롯(Boxplot), 바이올린(Violin), 히스토그램(Histogram) |
| **비율** | 워드클라우드(WordCloud), 액체(Liquid) |
| **흐름/구조** | 샹키(Sankey), 깔때기(Funnel), 트리맵(Treemap), 네트워크(Network) |
| **다차원** | 레이더(Radar), 듀얼 축(Dual Axis) |
| **비즈니스 다이어그램** | 생선뼈(Fishbone/Ishikawa), 플로우차트(Flowchart), 마인드맵(Mindmap), 조직도(Organization), 벤 다이어그램(Venn) |

#### 연결 정보

| 항목 | 값 |
|------|-----|
| 포트 | 1122 |
| URL | `http://localhost:1122/sse` |
| 프로토콜 | SSE (Server-Sent Events) |

---

### 3.2 mcp-echarts

**GitHub**: https://github.com/hustcc/mcp-echarts

#### 개요

Apache ECharts 기반의 전문 데이터 차트 생성 도구입니다.

#### 주요 기능

| 기능 | 설명 |
|------|------|
| ECharts 완전 지원 | 데이터, 스타일, 테마 등 모든 기능 |
| 출력 형식 | PNG, SVG, Option JSON |
| MinIO 통합 | URL 기반 이미지 반환 (Base64 대신) |
| 로컬 실행 | 외부 서비스 의존 없음, 보안성 높음 |

#### 연결 정보

| 항목 | 값 |
|------|-----|
| 포트 | 3033 |
| URL | `http://localhost:3033/sse` |
| 프로토콜 | SSE |

---

## 4. MCP 도구 선정 이유

### 4.1 도구별 선정 근거

#### @antv/mcp-server-chart 선정 이유

| 선정 기준 | 평가 | 설명 |
|----------|------|------|
| **차트 다양성** | ★★★★★ | 25+ 종류로 조사한 도구 중 가장 많음 |
| **비즈니스 특화** | ★★★★★ | 마인드맵, 조직도, 플로우차트, 생선뼈 다이어그램 지원 |
| **사업계획 적합성** | ★★★★★ | 창의적 방향성, 전략 시각화에 최적 |
| **프로토콜 호환성** | ★★★★☆ | SSE/Streamable 지원으로 기존 MCP 클라이언트 호환 |
| **라이선스** | ★★★★★ | MIT (상업적 사용 가능) |

**대안 대비 우위점**:
- BI-Chart-MCP-Server: 차트 종류 제한적, 문서화 부족
- Quickchart-MCP-Server: 10종류만 지원, QuickChart.io 외부 의존

---

#### mcp-echarts 선정 이유

| 선정 기준 | 평가 | 설명 |
|----------|------|------|
| **차트 품질** | ★★★★★ | Apache ECharts 기반 전문 품질 |
| **출력 형식** | ★★★★★ | PNG/SVG/JSON 다양한 형식 |
| **보안성** | ★★★★★ | 로컬 실행, 외부 의존 없음 |
| **경량화** | ★★★★☆ | 의존성 최소화 |
| **MinIO 통합** | ★★★★☆ | URL 기반 이미지 제공 |

**@antv와의 역할 분담**:
- @antv: 비즈니스 다이어그램, 구조 시각화
- mcp-echarts: 데이터 분석 결과, 정교한 차트

---

### 4.2 도구 조합 시너지

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          작업 흐름 예시                                     │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  사용자: "신규 사업 기획안을 분석하고 시각화해줘"                            │
│                                                                            │
│  1. RAG Agent (사내 시스템 우선)                                            │
│     └─ search_knowledge_base: 관련 내부 문서 검색                          │
│                                                                            │
│  2. External Agent (MCP 도구)                                              │
│     ├─ @antv: 사업 전략 마인드맵 생성                                       │
│     ├─ @antv: 프로세스 플로우차트 생성                                      │
│     └─ mcp-echarts: 시장 분석 데이터 차트 생성                              │
│                                                                            │
│  3. 결과 종합                                                               │
│     └─ 문서 분석 결과 + 시각화 자료 통합 제공                               │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

### 4.3 제외된 도구 및 이유

| 도구 | 제외 이유 |
|------|----------|
| **BI-Chart-MCP-Server** | 차트 종류 제한적, 문서화 부족, Vega-Lite 의존 |
| **Quickchart-MCP-Server** | 10종류만 지원, QuickChart.io 외부 서비스 의존 |
| **Markdownify MCP** | 시각화 기능 없음, 파일 변환만 지원 |
| **MCP Docs Service** | 문서 관리에 특화, 분석/시각화 미지원 |
| **Ultimate MCP Server** | Python 3.13+ 요구, Pydantic v2 호환성 문제로 설치 불안정 |

---

## 5. 도구 설치 및 실행

### 5.1 사전 요구사항

```bash
# Node.js 18+ 확인
node --version

# npm 확인
npm --version
```

### 5.2 MCP 도구 설치

```bash
# mcp-echarts 전역 설치
npm install -g mcp-echarts

# @antv/mcp-server-chart는 npx로 실행 가능 (설치 불필요)
```

### 5.3 MCP 서버 실행

```bash
# 프로젝트 루트에서 실행
cd /mnt/data1/work/sm-ai-v2/sm-ai-v2-backend

# 모든 MCP 서버 시작
./scripts/start_mcp_servers.sh

# 개별 서버 시작
./scripts/start_mcp_servers.sh chart    # @antv/mcp-server-chart만
./scripts/start_mcp_servers.sh echarts  # mcp-echarts만

# 상태 확인
./scripts/start_mcp_servers.sh status

# 모든 서버 중지
./scripts/start_mcp_servers.sh stop
```

### 5.4 연결 확인

```bash
# @antv/mcp-server-chart 확인
curl http://localhost:1122/sse

# mcp-echarts 확인
curl http://localhost:3033/sse
```

---

## 부록: 설정 파일 참조

### settings.py MCP 설정

```python
# src/config/settings.py

# MCP Servers
MCP_SERVER_URLS: list[str] = [
    "http://localhost:1122/sse",  # @antv/mcp-server-chart
    "http://localhost:3033/sse",  # mcp-echarts
]
```

### 포트 요약

| 서비스 | 포트 | 설명 |
|--------|------|------|
| vLLM API Server | 8000 | LLM 서빙 |
| Backend API | 8080 | FastAPI 서비스 |
| @antv/mcp-server-chart | 1122 | 차트/다이어그램 |
| mcp-echarts | 3033 | ECharts 차트 |
