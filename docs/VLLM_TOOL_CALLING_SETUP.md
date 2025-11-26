# LLM Tool Calling 설정 가이드

이 문서는 다양한 LLM 모델을 사용할 때 Tool Calling 설정 방법을 안내합니다.

---

## 1. OpenAI GPT 계열 모델 사용

OpenAI의 GPT 모델을 사용하는 경우, native tool calling이 완벽하게 지원됩니다.

### 1.1 설정 방법

`src/core/llm_service.py`를 수정하여 OpenAI API를 직접 사용합니다:

```python
from langchain_openai import ChatOpenAI

class LLMService:
    @staticmethod
    def get_llm(model_name: str = "gpt-4", temperature: float = 0.7):
        return ChatOpenAI(
            api_key="your-openai-api-key",  # 또는 OPENAI_API_KEY 환경변수
            model=model_name,
            temperature=temperature
        )
```

### 1.2 지원되는 모델

| 모델 | Tool Calling 지원 | 권장 용도 |
|------|------------------|----------|
| `gpt-4o` | 완벽 지원 | 복잡한 멀티 에이전트 작업 |
| `gpt-4o-mini` | 완벽 지원 | 비용 효율적인 일반 작업 |
| `gpt-4-turbo` | 완벽 지원 | 대규모 컨텍스트 필요시 |
| `gpt-3.5-turbo` | 지원 | 간단한 작업, 빠른 응답 |

### 1.3 환경 변수 설정

```bash
# .env 파일
OPENAI_API_KEY=sk-your-api-key-here
```

### 1.4 OpenAI 모델 사용 시 장점

- Native tool calling 완벽 지원
- `langgraph.prebuilt.create_react_agent` 직접 사용 가능
- Custom StateGraph 구현 불필요
- 병렬 도구 호출 지원

### 1.5 비용 고려사항

| 모델 | 입력 (1M tokens) | 출력 (1M tokens) |
|------|-----------------|-----------------|
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| gpt-3.5-turbo | $0.50 | $1.50 |

---

## 2. vLLM으로 Open Source 모델 서빙

### 2.1 문제 배경

`gpt-oss-120b` 모델과 LangGraph의 `create_react_agent`를 사용할 때, 기본 vLLM 설정으로는 Tool Calling이 정상 동작하지 않을 수 있습니다.

### 증상
- 도구 호출 시 `BadRequestError` 발생
- 응답이 `<|python_tag|>{"type": "function"...}` 형태의 raw string으로 반환
- 단순한 메시지에도 도구를 호출하려는 현상

### 2.2 해결 방법

#### vLLM 서버 실행 옵션 변경

모델의 base architecture에 따라 적절한 옵션을 선택하세요.

#### Llama 계열 모델 (Llama 3.1, 3.2 등)
```bash
vllm serve gpt-oss-120b \
  --host 0.0.0.0 \
  --port 8000 \
  --enable-auto-tool-choice \
  --tool-call-parser llama3_json \
  --chat-template /path/to/tool_chat_template_llama3.1_json.jinja
```

#### Hermes/Qwen 계열 모델
```bash
vllm serve gpt-oss-120b \
  --host 0.0.0.0 \
  --port 8000 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

#### Mistral 계열 모델
```bash
vllm serve gpt-oss-120b \
  --host 0.0.0.0 \
  --port 8000 \
  --enable-auto-tool-choice \
  --tool-call-parser mistral \
  --chat-template examples/tool_chat_template_mistral.jinja
```

### 2.3 주요 옵션 설명

| 옵션 | 설명 |
|------|------|
| `--enable-auto-tool-choice` | 모델이 자동으로 도구 호출 여부를 결정하도록 함 |
| `--tool-call-parser <parser>` | 도구 호출 응답을 파싱하는 방법 지정 |
| `--chat-template <path>` | 도구 호출을 지원하는 chat template 지정 |

### 2.4 지원되는 Tool Call Parser

| Parser | 호환 모델 |
|--------|----------|
| `llama3_json` | Llama 3.1, 3.2 |
| `hermes` | Hermes, Qwen 2.5 |
| `mistral` | Mistral 7B v0.3+ |
| `deepseek_v3` | DeepSeek V3 |
| `internlm` | InternLM |
| `jamba` | Jamba |

### 2.5 Chat Template 파일

vLLM 저장소에서 제공하는 template 파일들:
- `tool_chat_template_llama3.1_json.jinja`
- `tool_chat_template_llama3.2_json.jinja`
- `tool_chat_template_mistral.jinja`
- `tool_chat_template_hermes.jinja`

GitHub: https://github.com/vllm-project/vllm/tree/main/examples

## 3. 검증 방법

### 3.1 직접 API 테스트
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss-120b",
    "messages": [{"role": "user", "content": "What is the weather?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {
          "type": "object",
          "properties": {"location": {"type": "string"}},
          "required": ["location"]
        }
      }
    }]
  }'
```

### 3.2 응답 확인
정상적인 경우:
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "tool_calls": [{
        "id": "call_xxx",
        "type": "function",
        "function": {
          "name": "get_weather",
          "arguments": "{\"location\": \"Seoul\"}"
        }
      }]
    }
  }]
}
```

비정상적인 경우 (raw string 반환):
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "<|python_tag|>{\"type\": \"function\", ...}"
    }
  }]
}
```

## 4. 문제 해결

### 4.1 vLLM 설정으로 해결되지 않는 경우

모델이 native tool calling을 제대로 지원하지 않으면, **Phase 2: Custom StateGraph** 구현이 필요합니다.

이 방식은:
1. Prompt 기반 도구 호출 (API 레벨 바인딩 대신)
2. 모델 응답에서 JSON 파싱으로 도구 호출 추출
3. 모든 모델에서 안정적으로 동작

자세한 내용은 `src/systems/react/` 디렉토리의 구현을 참조하세요.

### 4.2 모델별 권장 설정

| 모델 유형 | 권장 접근법 | 비고 |
|----------|------------|------|
| OpenAI GPT-4/3.5 | Native tool calling | 가장 안정적 |
| Claude 3 | Native tool calling | Anthropic API 사용 |
| Llama 3.1 70B+ | vLLM + llama3_json parser | 대형 모델 권장 |
| Llama 3.2 8B | Custom StateGraph | 소형 모델은 prompt-based 권장 |
| Qwen 2.5 | vLLM + hermes parser | 또는 Custom StateGraph |
| gpt-oss-120b | Custom StateGraph | prompt-based 안정적 |

---

## 5. 참고 자료

- [vLLM Tool Calling Documentation](https://docs.vllm.ai/en/stable/features/tool_calling/)
- [vLLM GitHub - Tool Call Examples](https://github.com/vllm-project/vllm/tree/main/examples)
- [LangGraph ReAct Agent from Scratch](https://langchain-ai.github.io/langgraph/how-tos/react-agent-from-scratch/)
