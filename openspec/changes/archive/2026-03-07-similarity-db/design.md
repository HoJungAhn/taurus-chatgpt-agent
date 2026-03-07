## Context

동일하거나 유사한 Java error stacktrace가 반복 수신될 때 ChatGPT API를 매번 호출하지 않도록
SQLite 기반 유사도 저장소를 구현한다. interface_id를 기준으로 데이터를 관리하며,
TF-IDF + Cosine Similarity로 텍스트 유사도를 계산한다.

## Goals / Non-Goals

**Goals:**
- interface_id 기준 error_stack + chatgpt_result SQLite 저장/조회
- 동일 interface_id 내 TF-IDF + Cosine Similarity 유사도 비교
- 유사도 threshold 이상 시 기존 결과 반환 (ChatGPT 호출 생략)
- ChatGPT 성공 응답 시에만 DB 저장 (timeout/오류 시 저장 없음)
- 교체 가능한 인터페이스 기반 설계

**Non-Goals:**
- interface_id 간 교차 유사도 비교
- 벡터 영속화 (조회 시마다 즉석 계산)
- 실시간 대용량 처리 최적화

## Decisions

### 결정 1: SQLite (stdlib sqlite3) 단독 사용

```sql
CREATE TABLE similarity_store (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    interface_id   TEXT    NOT NULL,
    error_stack    TEXT    NOT NULL,
    chatgpt_result TEXT    NOT NULL,
    created_at     TEXT    NOT NULL
);
CREATE INDEX idx_interface_id ON similarity_store(interface_id);
```

- **이유**: 추가 의존성 없음, 단일 `.db` 파일, interface_id 인덱스로 빠른 조회
- **대안 고려**: TinyDB(JSON) → 쿼리 유연성 부족, 기각 / Redis → 별도 서버 필요, 오버스펙, 기각

### 결정 2: TF-IDF 벡터는 DB에 저장하지 않고 조회 시 즉석 계산

```
조회 흐름:
1. interface_id로 DB에서 모든 error_stack 텍스트 가져오기
2. 가져온 텍스트들 + 새 error_stack으로 TfidfVectorizer fit_transform
3. 새 error_stack 벡터와 기존 벡터들 간 cosine_similarity 계산
4. 최대 유사도 값이 threshold 이상이면 해당 chatgpt_result 반환
```

- **이유**: 벡터 직렬화/역직렬화 복잡성 제거. EAI 오류 건수 규모에서 성능 충분.
- **대안 고려**: 벡터 BLOB 저장 → 복잡성 증가, 건수 많아질 때 최적화 옵션으로 유보

### 결정 3: SimilarityService를 추상 인터페이스로 설계

```python
class BaseSimilarityService(ABC):
    def save(self, interface_id: str, error_stack: str, chatgpt_result: str) -> None: ...
    def find_similar(self, interface_id: str, error_stack: str) -> Optional[str]: ...
```

- **이유**: 향후 알고리즘 교체(BM25, sentence-transformers 등) 시 구현체만 교체 가능
- `TFIDFSimilarityService`가 기본 구현체

### 결정 4: DB 연결을 앱 시작 시 초기화, 종료 시 해제

FastAPI lifespan 이벤트를 사용하여 DB 연결 및 테이블 생성 처리.

## Risks / Trade-offs

- [Risk] 같은 interface_id에 데이터가 누적될수록 TF-IDF 계산 비용 증가
  → Mitigation: EAI 운영 환경의 오류 건수는 제한적. 문제 발생 시 벡터 캐싱으로 최적화 가능.
- [Risk] TF-IDF는 Java 클래스명/메서드명 토큰화에 의존 → 동일 로직의 다른 클래스명 오류를 다르게 판단할 수 있음
  → Mitigation: threshold 조정으로 보완. interface_id 내 비교이므로 실제 오탐 위험 낮음.

## Migration Plan

신규 구현이므로 마이그레이션 불필요.
`SIMILARITY_DB_PATH` 환경 변수로 DB 파일 위치 지정 가능.

## Open Questions

- threshold 기본값 0.8이 실제 운영 데이터에서 적절한지는 운영 후 튜닝 필요
