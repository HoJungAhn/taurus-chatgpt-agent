## ADDED Requirements

### Requirement: POST /api/refine 엔드포인트
`POST /api/refine`은 EAI 서비스로부터 `interface_id`와 `error_stack`을 수신하여 정제된 메시지를 반환해야 한다.
모든 처리 결과는 HTTP 200으로 응답하고, `status` 필드로 처리 경로를 구분해야 한다.

#### Scenario: similarity-db 캐시 hit 시 반환
- **WHEN** 동일 `interface_id` 내 유사한 `error_stack`이 DB에 존재할 때
- **THEN** HTTP 200과 함께 `status="cached"`, `is_refined=true`, 기존 `chatgpt_result`를 `refine_message`로 반환해야 한다

#### Scenario: ChatGPT 정제 성공 시 반환
- **WHEN** similarity-db에 유사 결과 없어 ChatGPT를 호출하고 성공 응답을 받았을 때
- **THEN** HTTP 200과 함께 `status="success"`, `is_refined=true`, 정제된 메시지를 `refine_message`로 반환하고 DB에 저장해야 한다

#### Scenario: ChatGPT timeout 시 원본 반환
- **WHEN** ChatGPT API 호출이 30초 내에 응답하지 않을 때
- **THEN** HTTP 200과 함께 `status="timeout"`, `is_refined=false`, 원본 `error_stack`을 `refine_message`로 반환해야 한다
- **THEN** DB에 저장하지 않아야 한다

#### Scenario: ChatGPT 오류 시 원본 반환
- **WHEN** ChatGPT API 호출 중 네트워크 오류 또는 비정상 응답이 발생했을 때
- **THEN** HTTP 200과 함께 `status="chatgpt_error"`, `is_refined=false`, 원본 `error_stack`을 `refine_message`로 반환해야 한다
- **THEN** DB에 저장하지 않아야 한다

#### Scenario: 필수 필드 누락 시 422 반환
- **WHEN** `interface_id` 또는 `error_stack` 필드 없이 요청 시
- **THEN** HTTP 422 Unprocessable Entity를 반환해야 한다

---

### Requirement: Request / Response JSON 스키마

**Request**:
```json
{
  "interface_id": "IF-001",
  "error_stack": "java.lang.NullPointerException\n\tat com.example..."
}
```

**Response**:
```json
{
  "interface_id": "IF-001",
  "refine_message": "...",
  "is_refined": true,
  "status": "success"
}
```

#### Scenario: response 구조 확인
- **WHEN** 정상적인 요청을 처리했을 때
- **THEN** response에 `interface_id`, `refine_message`, `is_refined`, `status` 필드가 모두 포함되어야 한다

---

### Requirement: 서비스 포트 9000 실행
메인 서비스는 기본 포트 9000에서 실행되어야 한다.

#### Scenario: 기본 포트로 실행
- **WHEN** `APP_PORT` 환경 변수 미설정 시
- **THEN** 서비스가 포트 9000으로 기동되어야 한다
