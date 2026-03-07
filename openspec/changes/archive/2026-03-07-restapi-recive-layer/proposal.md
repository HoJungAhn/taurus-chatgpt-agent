## Why

EAI 서비스에서 발생한 Java error stacktrace를 ChatGPT로 정제하기 위한 진입점이 필요하다.
`POST /api/refine` 엔드포인트를 통해 EAI로부터 오류 정보를 수신하고, 정제된 메시지를 반환하는 수신 레이어를 구축한다.

## What Changes

- `POST /api/refine` REST endpoint 신규 추가
- Request: `interface_id` + `error_stack` (Java stacktrace) JSON 수신
- Response: `refine_message` (정제 or 원본) + `is_refined` + `status` + `interface_id` JSON 반환
- 모든 처리 결과는 HTTP 200으로 응답 (ChatGPT 연동 실패 시에도 원본 반환)
- status 필드로 처리 경로 구분: `success` / `cached` / `timeout` / `chatgpt_error`
- Request 필드 누락 시 HTTP 422 반환 (FastAPI 기본 validation)
- `taurus-chatgpt-agent`는 독립 서비스로 구성 (mock-chatgpt-server와 분리)
- **처리 순서**: similarity-db 조회 → 유사 결과 없을 때만 ChatGPT 호출 → DB 저장 후 response
- **timeout/오류 시**: DB 저장 없이 원본 `error_stack`을 `refine_message`로 response
- **similarity 검색 범위**: 동일 `interface_id` 내 데이터만 비교 (타 인터페이스 데이터 미참조)

## Capabilities

### New Capabilities
- `error-refine-endpoint`: `POST /api/refine` — interface_id와 error_stack을 수신하여 ChatGPT 정제 결과 또는 원본을 반환하는 메인 엔드포인트

### Modified Capabilities

## Impact

- `app/main.py`: FastAPI 앱 진입점 생성
- `app/api/routes.py`: `/api/refine` 라우트 등록
- `app/models/schemas.py`: `RefineRequest`, `RefineResponse` Pydantic 모델 추가
- `app/services/chatgpt_service.py`: ChatGPT 호출 인터페이스 (Mock URL 설정으로 mock-chatgpt-server 연동)
- `app/config.py`: 아래 환경 변수로 관리
  - `CHATGPT_API_URL`: ChatGPT(or mock) 서비스 URL
  - `CHATGPT_API_KEY`: Bearer token 값
  - `CHATGPT_MODEL`: 사용 모델명 (기본값: `gpt-4`)
  - `CHATGPT_TIMEOUT`: 응답 timeout (기본값: 30초)
  - `CHATGPT_SYSTEM_PROMPT`: ChatGPT에 전달할 system prompt 문자열
- 서비스 포트: `9000` (환경 변수 `APP_PORT`로 관리)
- `tests/test_api.py`: `/api/refine` 엔드포인트 단위 테스트
- `requirements.txt`: fastapi, uvicorn, httpx, pydantic 추가
