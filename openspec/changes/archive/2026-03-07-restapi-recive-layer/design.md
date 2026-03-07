## Context

EAI 서비스로부터 Java error stacktrace를 수신하여 ChatGPT로 정제하는 메인 엔드포인트를 구현한다.
similarity-db와 mock-chatgpt-service(또는 실제 ChatGPT)를 조합하여 서비스 플로우를 완성한다.

## Goals / Non-Goals

**Goals:**
- `POST /api/refine` 엔드포인트 구현
- similarity-db 우선 조회 → 없으면 ChatGPT 호출 → 저장 후 반환 플로우
- ChatGPT timeout(30초)/오류 시 원본 error_stack 반환 (DB 저장 없음)
- 모든 케이스 HTTP 200 응답, status 필드로 처리 경로 구분
- httpx AsyncClient로 비동기 ChatGPT 호출

**Non-Goals:**
- 인증/인가 처리 (EAI 내부 서비스 간 호출)
- 요청 rate limiting
- 로그 저장소 구현

## Decisions

### 결정 1: Request / Response Pydantic 모델

```python
# Request
class RefineRequest(BaseModel):
    interface_id: str
    error_stack: str

# Response
class RefineResponse(BaseModel):
    interface_id: str
    refine_message: str
    is_refined: bool
    status: Literal["success", "cached", "timeout", "chatgpt_error"]
```

- 필드 누락 시 FastAPI가 자동으로 HTTP 422 반환

### 결정 2: 처리 순서 및 status 매핑

```
수신 (interface_id, error_stack)
    │
    ▼
similarity-db 조회 (interface_id 내)
    ├── 유사 결과 있음 → status="cached",   is_refined=True  → 200 반환
    └── 없음
         │
         ▼
    ChatGPT API 호출 (httpx, timeout=30s)
         ├── 성공 → DB 저장 → status="success",       is_refined=True  → 200 반환
         ├── timeout → DB 저장 없음 → status="timeout",     is_refined=False → 200 반환
         └── 오류  → DB 저장 없음 → status="chatgpt_error", is_refined=False → 200 반환

※ timeout/오류 시 refine_message = 원본 error_stack
```

### 결정 3: ChatGPT 호출은 httpx AsyncClient 사용

```python
async with httpx.AsyncClient(timeout=settings.chatgpt_timeout) as client:
    response = await client.post(
        settings.chatgpt_api_url,
        headers={"Authorization": f"Bearer {settings.chatgpt_api_key}"},
        json={
            "model": settings.chatgpt_model,
            "messages": [
                {"role": "system", "content": settings.chatgpt_system_prompt},
                {"role": "user",   "content": error_stack}
            ]
        }
    )
```

- **이유**: FastAPI 비동기 환경에서 requests(동기) 사용 시 이벤트 루프 블로킹 발생
- **대안 고려**: requests + run_in_executor → 복잡성 증가, 기각

### 결정 4: ChatGPT 응답에서 content 추출

```python
result = response.json()["choices"][0]["message"]["content"]
```

- OpenAI API 및 mock 서비스 모두 동일 경로 사용

## Risks / Trade-offs

- [Risk] ChatGPT API URL이 잘못 설정되면 모든 요청이 timeout으로 처리됨
  → Mitigation: 앱 시작 시 `CHATGPT_API_URL` 설정 존재 여부 검증
- [Risk] similarity-db 조회 실패 시 전체 요청 실패 가능
  → Mitigation: similarity-db 조회 오류는 catch하여 ChatGPT 직접 호출로 fallback

## Migration Plan

신규 구현이므로 마이그레이션 불필요.

## Open Questions

- `CHATGPT_SYSTEM_PROMPT` 내용 확정 필요 (운영팀과 협의)
