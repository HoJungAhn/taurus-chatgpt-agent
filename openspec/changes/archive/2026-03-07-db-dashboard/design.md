## Context

similarity DB에 쌓인 데이터를 운영 중 브라우저로 바로 확인할 수 있는 대시보드 페이지가 필요하다.
별도 프론트엔드 앱 없이 FastAPI + Jinja2로 서버사이드 렌더링하여 단순하게 구현한다.

## Goals / Non-Goals

**Goals:**
- `GET /dashboard` — interface_id별 저장 현황 HTML 페이지 제공
- 요약 통계 + interface_id 목록 테이블 + 클릭 시 상세 레코드 펼침
- 외부 JS 프레임워크 없이 순수 HTML/CSS + `<details>` 태그로 인터랙션 처리
- `similarity_service`에 대시보드용 조회 메서드 추가

**Non-Goals:**
- 실시간 자동 갱신 (수동 새로고침으로 충분)
- 삭제/수정 기능
- 인증/권한 처리

## Decisions

### 결정 1: Jinja2 서버사이드 렌더링 채택

```
GET /dashboard
    │
    ▼
similarity_service.get_summary()        → 전체 건수, interface_id 수
similarity_service.get_all_interfaces() → interface_id별 건수 + 최근 시각
    │
    ▼
Jinja2 템플릿 렌더링 → HTML 반환
```

- **이유**: 별도 API 없이 한 번의 요청으로 페이지 완성. 외부 의존성 최소.
- **대안 고려**: Vue/React SPA → 과도한 복잡성, 기각 / 별도 JSON API → 이 용도에 불필요, 기각

### 결정 2: `<details>` + `<summary>` 태그로 상세 펼침 구현

```html
<details>
  <summary>IF-001 (3건 | 최근: 2026-03-07 12:00)</summary>
  <table>
    <tr><td>error_stack 요약</td><td>chatgpt_result 요약</td><td>created_at</td></tr>
    ...
  </table>
</details>
```

- **이유**: JavaScript 없이 브라우저 네이티브 기능으로 펼침/접기 구현 가능

### 결정 3: 페이지 레이아웃

```
┌─────────────────────────────────────────────┐
│  Similarity DB Dashboard                    │
│  전체 저장 건수: 12   고유 Interface ID: 3   │
├─────────────────────────────────────────────┤
│  ▶ IF-001  (5건 | 최근: 2026-03-07 14:22)   │
│  ▼ IF-002  (4건 | 최근: 2026-03-07 13:10)   │
│    ┌──────────────┬──────────────┬─────────┐ │
│    │ Error 요약   │ 정제 결과 요약│ 저장 시각│ │
│    ├──────────────┼──────────────┼─────────┤ │
│    │ NullPoint... │ 603라인에서..│ 13:10   │ │
│    └──────────────┴──────────────┴─────────┘ │
│  ▶ IF-003  (3건 | 최근: 2026-03-07 11:05)   │
└─────────────────────────────────────────────┘
```

### 결정 4: similarity_service에 조회 메서드 2개 추가

```python
def get_summary(self) -> dict:
    # 전체 건수, 고유 interface_id 수 반환

def get_all_interfaces(self) -> list[dict]:
    # interface_id별 건수, 최근 created_at, 레코드 목록 반환
```

- `BaseSimilarityService`에 추상 메서드로 추가 → `TFIDFSimilarityService`에서 구현

## Risks / Trade-offs

- [Risk] DB 데이터가 많을 경우 전체 조회 시 느릴 수 있음
  → Mitigation: EAI 오류 건수 규모는 제한적. 문제 시 페이지네이션 추가 가능.
- [Risk] error_stack, chatgpt_result가 길어 화면이 복잡해질 수 있음
  → Mitigation: 각 필드를 100자로 truncate하여 표시, 전체 내용은 hover 또는 별도 영역으로 확인

## Migration Plan

기존 similarity_service에 조회 메서드만 추가. 기존 기능 영향 없음.

## Open Questions

- 없음
