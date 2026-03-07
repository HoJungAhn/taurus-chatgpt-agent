## 1. Pydantic 모델 정의

- [x] 1.1 `mock_server/schemas.py` 생성 — OpenAI API 호환 `ChatMessage`, `ChatRequest`, `ChatResponseMessage`, `ChatChoice`, `ChatResponse` Pydantic 모델 정의

## 2. Bearer token 인증 구현

- [x] 2.1 `mock_server/auth.py` 생성 — `Authorization: Bearer <token>` 헤더 검증 FastAPI Dependency 구현
- [x] 2.2 인증 실패 시 HTTP 401 반환 처리

## 3. 고정 응답 데이터 정의

- [x] 3.1 `mock_server/constants.py` 생성 — NullPointerException 분석 고정 응답 텍스트 상수 정의
  (오류 분석 내용 / 오류 원인 / 해결 방법 포함)

## 4. 엔드포인트 구현

- [x] 4.1 `mock_server/routes.py` 생성 — `POST /service/chatgpt` 라우트 구현 (Bearer 인증 적용, 고정 응답 반환)
- [x] 4.2 `mock_server/main.py` 업데이트 — 라우터 등록

## 5. 테스트 코드 작성

- [x] 5.1 `mock_server/tests/test_mock_endpoint.py` 생성
  - 정상 요청 → HTTP 200 및 response 구조 확인
  - Bearer token 누락 → HTTP 401 확인
  - Bearer token 불일치 → HTTP 401 확인
  - 필수 필드 누락 → HTTP 422 확인

## 6. 동작 검증

- [x] 6.1 mock 서버 기동 후 `POST /service/chatgpt` curl 테스트 (Bearer token 포함)
- [x] 6.2 pytest 실행하여 모든 테스트 통과 확인
