## Why

similarity DB에 어떤 interface_id 기준으로 얼마나 많은 오류가 저장되어 있는지 운영 중 확인할 방법이 없다.
`GET /dashboard` 웹 페이지를 통해 저장 현황을 브라우저에서 바로 확인할 수 있는 관리 대시보드가 필요하다.

## What Changes

- `GET /dashboard` HTML 페이지 엔드포인트 추가
- 대시보드 표시 내용:
  - **요약 통계**: 전체 저장 건수, 고유 interface_id 수
  - **interface_id별 목록 테이블**: interface_id / 저장 건수 / 최근 저장 시각
  - **상세 보기**: interface_id 클릭 시 해당 오류 목록 펼쳐 보기 (error_stack 요약 + chatgpt_result 요약 + created_at)
- Jinja2 템플릿 기반 서버사이드 렌더링 (외부 JS 프레임워크 없음)
- `app/templates/dashboard.html` 템플릿 파일 추가
- `requirements.txt`에 `jinja2` 추가

## Capabilities

### New Capabilities
- `dashboard-view`: `GET /dashboard` — similarity DB의 interface_id별 저장 현황을 HTML 페이지로 표시

### Modified Capabilities

## Impact

- `app/api/routes.py`: `GET /dashboard` 라우트 추가
- `app/templates/dashboard.html`: HTML 템플릿 신규 생성
- `app/services/similarity_service.py`: 대시보드용 통계 조회 메서드 추가 (`get_summary`, `get_records_by_interface`)
- `app/main.py`: Jinja2 `StaticFiles` / `Jinja2Templates` 설정 추가
- `requirements.txt`: `jinja2` 추가
