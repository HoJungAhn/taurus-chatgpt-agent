## Why

실제 ChatGPT API가 현재 호출 불가능한 상황에서, EAI 에러 정제 서비스의 전체 흐름을 검증하기 위해
고정 응답을 반환하는 Mock ChatGPT Service가 필요하다. 이를 통해 실제 API 없이 통합 테스트를 진행할 수 있다.

## What Changes

- `POST /service/chatgpt` REST endpoint 신규 추가
- Bearer token (`abcdefghijk`) 기반 인증 처리
- Request: 실제 ChatGPT API 형식과 동일한 스키마
  ```json
  {
    "model": "gpt-4",
    "messages": [
      { "role": "system", "content": "<system_prompt>" },
      { "role": "user",   "content": "<error_stack>" }
    ]
  }
  ```
- Response: 실제 ChatGPT API 형식과 동일한 스키마 (고정된 NullPointerException 분석 결과 반환)
  ```json
  {
    "choices": [
      {
        "message": {
          "role": "assistant",
          "content": "<고정 분석 결과 텍스트>"
        }
      }
    ]
  }
  ```
- 인증 실패 시 `401 Unauthorized` 응답
- `application/json` Content-Type 처리
- 서비스 포트: 환경 변수로 설정 (테스트용이므로 자유롭게 지정)

## Capabilities

### New Capabilities
- `mock-chatgpt-endpoint`: `/service/chatgpt` POST 엔드포인트 - Bearer token 인증 후 error stack 수신, 고정 분석 결과 반환

### Modified Capabilities

## Impact

- `app/services/chatgpt_service.py`: Mock 서비스 구현체 추가 (실제 ChatGPT 클라이언트와 동일 인터페이스)
- `app/api/routes.py`: `/service/chatgpt` 라우트 등록
- `app/models/schemas.py`: ChatGPT request/response Pydantic 모델 추가
- `tests/test_chatgpt_service.py`: Mock 서비스 단위 테스트
- `requirements.txt`: FastAPI, uvicorn, pydantic 의존성 추가
