## ADDED Requirements

### Requirement: interface_id 기준 데이터 저장
ChatGPT 성공 응답 시 `interface_id`, `error_stack`, `chatgpt_result`를 SQLite DB에 저장해야 한다.
ChatGPT timeout 또는 오류 시에는 저장하지 않아야 한다.

#### Scenario: ChatGPT 성공 시 데이터 저장
- **WHEN** ChatGPT API 호출이 성공하여 결과를 받았을 때
- **THEN** `interface_id`, `error_stack`, `chatgpt_result`, `created_at`이 DB에 저장되어야 한다

#### Scenario: ChatGPT timeout 시 저장 없음
- **WHEN** ChatGPT API 호출이 timeout으로 실패했을 때
- **THEN** DB에 아무 데이터도 저장되지 않아야 한다

#### Scenario: ChatGPT 오류 시 저장 없음
- **WHEN** ChatGPT API 호출이 오류로 실패했을 때
- **THEN** DB에 아무 데이터도 저장되지 않아야 한다

---

### Requirement: interface_id 기준 데이터 조회
주어진 `interface_id`에 해당하는 모든 `error_stack` 데이터를 조회할 수 있어야 한다.

#### Scenario: 저장된 데이터 조회
- **WHEN** 이미 저장된 `interface_id`로 조회 시
- **THEN** 해당 `interface_id`의 모든 `error_stack`과 `chatgpt_result` 목록을 반환해야 한다

#### Scenario: 미존재 interface_id 조회
- **WHEN** 저장된 데이터가 없는 `interface_id`로 조회 시
- **THEN** 빈 목록을 반환해야 한다
