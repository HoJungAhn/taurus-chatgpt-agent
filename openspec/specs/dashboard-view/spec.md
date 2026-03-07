## ADDED Requirements

### Requirement: GET /dashboard 페이지 제공
`GET /dashboard`는 similarity DB의 저장 현황을 HTML 페이지로 반환해야 한다.

#### Scenario: 대시보드 페이지 접근
- **WHEN** 브라우저에서 `GET /dashboard`를 요청했을 때
- **THEN** HTTP 200과 함께 HTML 페이지가 반환되어야 한다
- **THEN** `Content-Type: text/html`이어야 한다

#### Scenario: 저장 데이터 없을 때
- **WHEN** similarity DB가 비어 있을 때 `GET /dashboard`를 요청했을 때
- **THEN** "저장된 데이터 없음" 메시지와 함께 페이지가 정상 반환되어야 한다

---

### Requirement: 요약 통계 표시
대시보드 상단에 전체 저장 건수와 고유 interface_id 수를 표시해야 한다.

#### Scenario: 요약 통계 확인
- **WHEN** 12건의 레코드가 3개의 interface_id에 걸쳐 저장되어 있을 때
- **THEN** 페이지에 "전체 저장 건수: 12", "고유 Interface ID: 3" 정보가 표시되어야 한다

---

### Requirement: interface_id별 목록 표시
각 interface_id에 대해 저장 건수와 가장 최근 저장 시각을 목록으로 표시해야 한다.

#### Scenario: interface_id 목록 표시
- **WHEN** IF-001(5건), IF-002(4건), IF-003(3건)이 저장되어 있을 때
- **THEN** 각 interface_id가 저장 건수 및 최근 저장 시각과 함께 목록에 표시되어야 한다

---

### Requirement: interface_id 클릭 시 상세 레코드 펼쳐 보기
interface_id를 클릭하면 해당 interface_id의 레코드 목록이 펼쳐져야 한다.
각 레코드는 error_stack 요약, chatgpt_result 요약, created_at을 표시해야 한다.

#### Scenario: 상세 레코드 펼침
- **WHEN** 사용자가 interface_id 항목을 클릭했을 때
- **THEN** 해당 interface_id의 레코드 목록이 테이블 형태로 펼쳐져야 한다
- **THEN** error_stack과 chatgpt_result는 100자로 잘려서 표시되어야 한다
- **THEN** created_at은 저장된 시각 그대로 표시되어야 한다

#### Scenario: 다시 클릭 시 접힘
- **WHEN** 펼쳐진 interface_id 항목을 다시 클릭했을 때
- **THEN** 레코드 목록이 접혀야 한다
