# vLLM Tool Calling 설정 가이드 (gpt-oss-120b)

이 문서는 ML35 서버에서 gpt-oss-120b 모델을 vLLM으로 서빙하고, Native Tool Calling을 설정하는 방법을 안내합니다.

---

## 목차

1. [ML35 서버 접속](#1-ml35-서버-접속)
2. [vLLM 환경 설정](#2-vllm-환경-설정)
3. [vLLM 서버 실행](#3-vllm-서버-실행)
4. [Tool Calling 검증](#4-tool-calling-검증)
5. [Backend 서비스 연동](#5-backend-서비스-연동)
6. [트러블슈팅](#6-트러블슈팅)

---

## 1. ML35 서버 접속

### 1.1 SSH 접속

```bash
ssh vrsoft@ML35
# 또는 IP로 직접 접속
ssh vrsoft@<ML35-IP-ADDRESS>
```

### 1.2 작업 디렉토리 이동

```bash
cd /mnt/data1/work/sm-ai-v2/sm-ai-v2-backend
```

### 1.3 환경 확인

```bash
# GPU 상태 확인
nvidia-smi

# vLLM 환경 확인
which python
python --version
pip show vllm
```

---

## 2. vLLM 환경 설정

### 2.1 필수 환경 변수

vLLM 실행 전 아래 환경 변수 설정이 필요할 수 있습니다:

```bash
# CUDA 관련 설정 (필요시)
export CUDA_VISIBLE_DEVICES=0,1

# 토큰화 병렬처리 비활성화 (경고 방지)
export TOKENIZERS_PARALLELISM=false
```

### 2.2 모델 경로 확인

gpt-oss-120b 모델은 다음 경로에 저장되어 있습니다:

```bash
# 모델 경로
/mnt/data1/work/model_vllm/gpt_model

# 구조 확인
ls -la /mnt/data1/work/model_vllm/gpt_model
```

모델 디렉토리에는 다음 파일들이 포함되어야 합니다:
- `config.json`: 모델 설정
- `tokenizer.json`, `tokenizer_config.json`: 토크나이저 설정
- `*.safetensors` 또는 `*.bin`: 모델 가중치 파일

---

## 3. vLLM 서버 실행

### 3.1 기본 실행 명령어

```bash
python -m vllm.entrypoints.openai.api_server \
    --model /mnt/data1/work/model_vllm/gpt_model \
    --tokenizer /mnt/data1/work/model_vllm/gpt_model \
    --served-model-name gpt-oss-120b \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.90 \
    --max-model-len 131072 \
    --max-num-batched-tokens 4096 \
    --port 8000 \
    --host 0.0.0.0 \
    --disable-custom-all-reduce \
    --enable-auto-tool-choice \
    --tool-call-parser openai
```

### 3.2 옵션 상세 설명

| 옵션 | 값 | 설명 |
|------|------|------|
| `--model` | `/mnt/data1/work/model_vllm/gpt_model` | 모델 가중치 경로 |
| `--tokenizer` | `/mnt/data1/work/model_vllm/gpt_model` | 토크나이저 경로 (모델과 동일) |
| `--served-model-name` | `gpt-oss-120b` | API에서 사용할 모델 이름 |
| `--tensor-parallel-size` | `2` | GPU 분산 개수 (ML35: 2개 GPU 사용) |
| `--gpu-memory-utilization` | `0.90` | GPU 메모리 사용률 (90%) |
| `--max-model-len` | `131072` | 최대 컨텍스트 길이 (128K) |
| `--max-num-batched-tokens` | `4096` | 배치당 최대 토큰 수 |
| `--port` | `8000` | API 서버 포트 |
| `--host` | `0.0.0.0` | 모든 인터페이스에서 접속 허용 |
| `--disable-custom-all-reduce` | - | Custom all-reduce 비활성화 (안정성) |
| **`--enable-auto-tool-choice`** | - | **자동 도구 선택 활성화 (필수)** |
| **`--tool-call-parser`** | `openai` | **도구 호출 파서 (필수: openai 형식)** |

### 3.3 백그라운드 실행 (권장)

서버를 백그라운드에서 실행하고 로그를 파일로 저장:

```bash
# 로그 디렉토리 생성
mkdir -p /mnt/data1/work/sm-ai-v2/logs

# 백그라운드 실행 (nohup)
nohup python -m vllm.entrypoints.openai.api_server \
    --model /mnt/data1/work/model_vllm/gpt_model \
    --tokenizer /mnt/data1/work/model_vllm/gpt_model \
    --served-model-name gpt-oss-120b \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.90 \
    --max-model-len 131072 \
    --max-num-batched-tokens 4096 \
    --port 8000 \
    --host 0.0.0.0 \
    --disable-custom-all-reduce \
    --enable-auto-tool-choice \
    --tool-call-parser openai \
    > /mnt/data1/work/sm-ai-v2/logs/vllm.log 2>&1 &

# 프로세스 확인
ps aux | grep vllm

# 로그 모니터링
tail -f /mnt/data1/work/sm-ai-v2/logs/vllm.log
```

### 3.4 tmux/screen 사용 (대안)

```bash
# tmux 세션 시작
tmux new -s vllm

# vLLM 서버 실행 (위 명령어)
python -m vllm.entrypoints.openai.api_server ...

# 세션 분리: Ctrl+B, D
# 세션 재접속: tmux attach -t vllm
```

### 3.5 서버 상태 확인

```bash
# 서버 시작 대기 (약 1-2분 소요)
# 로그에서 "Uvicorn running on http://0.0.0.0:8000" 확인

# Health Check
curl http://localhost:8000/health

# 모델 목록 확인
curl http://localhost:8000/v1/models
```

예상 응답:
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-oss-120b",
      "object": "model",
      "created": 1234567890,
      "owned_by": "vllm"
    }
  ]
}
```

---

## 4. Tool Calling 검증

### 4.1 직접 API 테스트

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss-120b",
    "messages": [
      {"role": "user", "content": "서울의 현재 날씨를 알려줘"}
    ],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "특정 위치의 현재 날씨를 가져옵니다",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "도시 이름 (예: Seoul, Tokyo)"
            }
          },
          "required": ["location"]
        }
      }
    }],
    "tool_choice": "auto"
  }'
```

### 4.2 정상 응답 (Tool Calling 성공)

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-oss-120b",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": null,
      "tool_calls": [{
        "id": "call_xxx",
        "type": "function",
        "function": {
          "name": "get_weather",
          "arguments": "{\"location\": \"Seoul\"}"
        }
      }]
    },
    "finish_reason": "tool_calls"
  }],
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 20,
    "total_tokens": 70
  }
}
```

### 4.3 검증 포인트

| 항목 | 정상 | 비정상 |
|------|------|--------|
| `message.tool_calls` | 배열로 존재 | `null` 또는 없음 |
| `message.content` | `null` | raw string 출력 |
| `finish_reason` | `"tool_calls"` | `"stop"` |
| `function.arguments` | valid JSON | 파싱 불가 |

---

## 5. Backend 서비스 연동

### 5.1 LLM Service 설정

`src/core/llm_service.py`:

```python
from langchain_openai import ChatOpenAI
from src.config.settings import get_settings

settings = get_settings()

class LLMService:
    @staticmethod
    def get_llm(model_name: str = "gpt-oss-120b", temperature: float = 0.7):
        """vLLM 서버에 연결된 LLM 인스턴스 반환"""
        api_key_value = settings.OPENAI_API_KEY if settings.OPENAI_API_KEY else "dummies"
        return ChatOpenAI(
            base_url="http://localhost:8000/v1",  # vLLM 서버 주소
            api_key=api_key_value,                # 더미 키 (vLLM은 인증 불필요)
            model=model_name,                     # gpt-oss-120b
            temperature=temperature
        )
```

### 5.2 Backend 서비스 실행

```bash
cd /mnt/data1/work/sm-ai-v2/sm-ai-v2-backend

# 가상환경 활성화
source .venv/bin/activate

# uvicorn으로 실행
uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload
```

### 5.3 연동 테스트

```bash
# Chat API 테스트
curl -X POST http://localhost:8080/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "회사 휴가 정책 알려줘",
    "session_id": "test-session-001"
  }'
```

---

## 6. 트러블슈팅

### 6.1 Tool Calling이 동작하지 않는 경우

**증상**: `tool_calls`가 `null`이고 `content`에 raw JSON 문자열 출력

**원인**: `--enable-auto-tool-choice --tool-call-parser openai` 옵션 누락

**해결**:
```bash
# vLLM 서버 재시작 시 옵션 확인
--enable-auto-tool-choice \
--tool-call-parser openai
```

### 6.2 GPU 메모리 부족

**증상**: `CUDA out of memory` 오류

**해결**:
```bash
# 메모리 사용률 낮추기
--gpu-memory-utilization 0.80

# 또는 max-model-len 줄이기
--max-model-len 65536
```

### 6.3 서버 시작 느림

**증상**: 모델 로딩에 5분 이상 소요

**원인**: 120B 모델의 대용량 가중치 로딩

**해결**: 정상 동작이며, `tail -f` 로그로 진행 상황 모니터링

### 6.4 연결 거부 오류

**증상**: `Connection refused` on port 8000

**확인 사항**:
```bash
# 프로세스 실행 확인
ps aux | grep vllm

# 포트 사용 확인
netstat -tlnp | grep 8000

# 방화벽 확인
sudo ufw status
```

### 6.5 vLLM 프로세스 종료

```bash
# PID 확인 후 종료
ps aux | grep vllm
kill <PID>

# 또는 강제 종료
pkill -f "vllm.entrypoints.openai.api_server"
```

---

## 부록: Quick Reference

### 빠른 시작 체크리스트

1. [ ] ML35 서버 SSH 접속
2. [ ] `nvidia-smi`로 GPU 상태 확인
3. [ ] 모델 경로 확인 (`/mnt/data1/work/model_vllm/gpt_model`)
4. [ ] vLLM 서버 실행 (Tool Calling 옵션 포함)
5. [ ] `curl localhost:8000/v1/models`로 서버 상태 확인
6. [ ] Tool Calling 테스트
7. [ ] Backend 서비스 실행 및 연동 확인

### 핵심 포트

| 서비스 | 포트 | 설명 |
|--------|------|------|
| vLLM API Server | 8000 | OpenAI 호환 API |
| Backend API | 8080 | FastAPI 서비스 |

### 핵심 명령어

```bash
# vLLM 서버 상태 확인
curl http://localhost:8000/health

# 모델 목록
curl http://localhost:8000/v1/models

# Chat 테스트 (Tool Calling)
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-oss-120b","messages":[{"role":"user","content":"Hello"}]}'
```
