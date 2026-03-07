## Context

실제 ChatGPT API를 호출할 수 없는 개발/테스트 환경에서 `taurus-chatgpt-agent`의 전체 플로우를 검증하기 위해
고정 응답을 반환하는 Mock 서버가 필요하다. 실제 OpenAI API와 동일한 request/response 스키마를 사용하여
나중에 URL만 교체하면 실제 ChatGPT로 전환 가능하도록 설계한다.

## Goals / Non-Goals

**Goals:**
- 실제 OpenAI Chat Completions API와 동일한 request/response 스키마 구현
- Bearer token 인증 처리 (`abcdefghijk`)
- 고정된 NullPointerException 분석 결과 반환
- `project-bootstrap`에서 생성된 `mock_server/` 구조 위에 구현

**Non-Goals:**
- 실제 AI 추론 기능 구현
- 다양한 응답 시나리오 처리 (단순 고정 응답)
- 데이터 저장 기능

## Decisions

### 결정 1: OpenAI Chat Completions API 스키마 그대로 채택

**Request 스키마** (`POST /service/chatgpt`):
```json
{
  "model": "gpt-4",
  "messages": [
    { "role": "system", "content": "<system_prompt>" },
    { "role": "user",   "content": "<error_stack>" }
  ]
}
```

**Response 스키마**:
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "<분석 결과 텍스트>"
      }
    }
  ]
}
```

- **이유**: 메인 서비스(`taurus-chatgpt-agent`)가 실제 ChatGPT로 전환 시 코드 수정 없이 URL만 교체 가능
- **대안 고려**: 단순화된 커스텀 스키마 → 실제 API 전환 시 메인 서비스 코드 수정 필요, 기각

### 결정 2: Bearer token 인증을 FastAPI Dependency로 구현
```python
# Authorization: Bearer abcdefghijk 검증
# 실패 시 HTTP 401 반환
```
- **이유**: FastAPI `Depends`를 활용하면 라우트 함수와 인증 로직 분리 가능

### 결정 3: 고정 응답을 상수로 관리
- 분석 결과 텍스트를 `mock_server/` 내부 상수로 정의
- **이유**: 응답 내용 변경 시 한 곳만 수정하면 됨

## Risks / Trade-offs

- [Risk] mock 응답이 항상 고정이므로 다양한 입력에 대한 응답 차이를 테스트 불가
  → Mitigation: mock의 목적은 전체 플로우 검증이지 ChatGPT 품질 검증이 아님. 범위 내 허용.
- [Risk] 실제 OpenAI API response에는 `id`, `created`, `usage` 등 추가 필드가 있음
  → Mitigation: 메인 서비스는 `choices[0].message.content`만 사용하므로 추가 필드 생략 가능

## Migration Plan

신규 서비스이므로 마이그레이션 불필요.
실제 ChatGPT 전환 시: `CHATGPT_API_URL`을 OpenAI URL로 변경 → mock 서버 중지 → `mock_server/` 삭제 가능.

## Open Questions

- 없음
