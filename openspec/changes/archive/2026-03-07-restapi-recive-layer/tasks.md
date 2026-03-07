## 1. Pydantic 모델 정의

- [x] 1.1 `app/models/schemas.py` 생성 — `RefineRequest`, `RefineResponse` Pydantic 모델 정의
  - `RefineRequest`: `interface_id: str`, `error_stack: str`
  - `RefineResponse`: `interface_id: str`, `refine_message: str`, `is_refined: bool`, `status: Literal["success", "cached", "timeout", "chatgpt_error"]`

## 2. ChatGPT 호출 서비스 구현

- [x] 2.1 `app/services/chatgpt_service.py` 생성 — `call_chatgpt(error_stack: str) -> str` 비동기 함수 구현
  - httpx AsyncClient로 `CHATGPT_API_URL`에 POST 요청
  - `Authorization: Bearer {CHATGPT_API_KEY}` 헤더 포함
  - OpenAI 형식 request body 구성 (`model`, `messages` with system/user role)
  - `choices[0].message.content` 추출하여 반환
  - `httpx.TimeoutException` → `TimeoutError` 발생
  - 기타 오류 → `ChatGPTError` 발생

## 3. 엔드포인트 구현

- [x] 3.1 `app/api/routes.py` 생성 — `POST /api/refine` 라우트 구현
  - similarity-db `find_similar` 호출 → 결과 있으면 `status="cached"` 반환
  - ChatGPT 호출 → 성공 시 DB `save` 후 `status="success"` 반환
  - TimeoutError → DB 저장 없이 원본 반환, `status="timeout"`
  - ChatGPTError → DB 저장 없이 원본 반환, `status="chatgpt_error"`
  - similarity-db 오류 → 예외 catch 후 ChatGPT 직접 호출로 fallback
- [x] 3.2 `app/main.py` 업데이트 — `/api/refine` 라우터 등록

## 4. 테스트 코드 작성

- [x] 4.1 `tests/test_api.py` 생성
  - similarity-db 캐시 hit → `status="cached"`, `is_refined=True` 확인
  - ChatGPT 성공 → `status="success"`, `is_refined=True`, DB 저장 확인
  - ChatGPT timeout → `status="timeout"`, `is_refined=False`, DB 미저장 확인
  - ChatGPT 오류 → `status="chatgpt_error"`, `is_refined=False`, DB 미저장 확인
  - 필수 필드 누락 → HTTP 422 확인

## 5. 통합 검증

- [x] 5.1 mock 서버 기동 후 `POST /api/refine` curl 테스트 (전체 플로우 확인)
- [x] 5.2 동일 요청 두 번 전송 → 두 번째는 `status="cached"` 반환 확인
- [x] 5.3 pytest 실행하여 모든 테스트 통과 확인
