## 1. similarity_service 조회 메서드 추가

- [x] 1.1 `BaseSimilarityService`에 `get_summary()`, `get_all_interfaces()` 추상 메서드 추가
- [x] 1.2 `TFIDFSimilarityService`에 `get_summary()` 구현 — 전체 건수, 고유 interface_id 수 반환
- [x] 1.3 `TFIDFSimilarityService`에 `get_all_interfaces()` 구현 — interface_id별 건수, 최근 created_at, 레코드 목록(error_stack, chatgpt_result, created_at) 반환

## 2. Jinja2 템플릿 설정

- [x] 2.1 `requirements.txt`에 `jinja2` 추가
- [x] 2.2 `app/templates/` 디렉토리 생성
- [x] 2.3 `app/main.py`에 `Jinja2Templates` 설정 추가

## 3. HTML 템플릿 작성

- [x] 3.1 `app/templates/dashboard.html` 생성
  - 상단: 제목 "Dashboard", 전체 건수, 고유 interface_id 수 표시
  - interface_id 목록: `<details>`/`<summary>` 태그로 펼침/접기 구현, 최근 시각 `YYYY-MM-DD hh:mm:ss` 포맷 표시
  - 상세 테이블 컬럼: `stacktrace`(100자 truncate) / `refined message`(100자 truncate) / `update`(`YYYY-MM-DD hh:mm:ss` 포맷)
  - 데이터 없을 때 "저장된 데이터 없음" 메시지 표시
  - 기본 CSS 인라인 적용 (외부 파일 없음)

## 4. 대시보드 라우트 추가

- [x] 4.1 `app/api/routes.py`에 `GET /dashboard` 라우트 추가 — `get_all_interfaces()`, `get_summary()` 호출 후 Jinja2 템플릿 렌더링

## 5. 테스트 코드 작성

- [x] 5.1 `tests/test_dashboard.py` 생성
  - `GET /dashboard` → HTTP 200, `text/html` 확인
  - 데이터 있을 때 interface_id 목록 HTML에 포함 확인
  - DB 비어 있을 때 정상 응답 확인

## 6. 동작 검증

- [x] 6.1 서비스 기동 후 브라우저에서 `http://localhost:9000/dashboard` 접속 확인
- [x] 6.2 pytest 실행하여 모든 테스트 통과 확인
