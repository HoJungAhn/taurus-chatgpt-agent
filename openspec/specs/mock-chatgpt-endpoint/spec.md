## ADDED Requirements

### Requirement: POST /service/chatgpt 엔드포인트
mock 서버는 `POST /service/chatgpt` 엔드포인트를 제공해야 한다.
요청은 OpenAI Chat Completions API와 동일한 스키마를 사용해야 한다.
Bearer token 인증을 통과한 경우에만 고정된 분석 결과를 반환해야 한다.

#### Scenario: 정상 요청 처리
- **WHEN** `Authorization: Bearer abcdefghijk` 헤더와 올바른 request body로 POST 요청 시
- **THEN** HTTP 200과 함께 `choices[0].message.content`에 고정된 NullPointerException 분석 결과를 반환해야 한다

#### Scenario: Bearer token 누락 시 인증 실패
- **WHEN** `Authorization` 헤더 없이 POST 요청 시
- **THEN** HTTP 401 Unauthorized를 반환해야 한다

#### Scenario: Bearer token 값 불일치 시 인증 실패
- **WHEN** `Authorization: Bearer wrongtoken` 으로 POST 요청 시
- **THEN** HTTP 401 Unauthorized를 반환해야 한다

---

### Requirement: OpenAI API 호환 Request 스키마
request body는 OpenAI Chat Completions API 형식을 따라야 한다.

```json
{
  "model": "gpt-4",
  "messages": [
    { "role": "system", "content": "<system_prompt>" },
    { "role": "user",   "content": "<error_stack>" }
  ]
}
```

#### Scenario: 올바른 request body 수신
- **WHEN** `model`과 `messages` 필드가 포함된 JSON body로 요청 시
- **THEN** 정상적으로 처리되어 HTTP 200을 반환해야 한다

#### Scenario: 필수 필드 누락 시 오류
- **WHEN** `messages` 필드 없이 요청 시
- **THEN** HTTP 422 Unprocessable Entity를 반환해야 한다

---

### Requirement: OpenAI API 호환 Response 스키마
response body는 OpenAI Chat Completions API 형식을 따라야 한다.

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

#### Scenario: response 구조 확인
- **WHEN** 인증된 정상 요청을 수신했을 때
- **THEN** response에 `choices` 배열이 있어야 하고 `choices[0].message.content`에 분석 텍스트가 있어야 한다
