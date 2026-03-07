## Why

동일하거나 유사한 Java error stacktrace가 반복 수신될 때 ChatGPT API를 매번 호출하는 것은 비효율적이다.
interface_id 기준으로 error stacktrace와 ChatGPT 결과를 디스크에 저장하고, 새 오류 수신 시 TF-IDF + Cosine Similarity로 유사도를 비교하여 기존 결과를 재사용하는 Similarity DB가 필요하다.

## What Changes

- `app/services/similarity_service.py` 신규 구현
  - interface_id 기준으로 error_stack + chatgpt_result 저장 (SQLite, 디스크 영속)
  - 새 error_stack 수신 시 **동일 interface_id 내 데이터만** TF-IDF + Cosine Similarity 비교 (타 interface_id 미참조)
  - 유사도 threshold 이상인 경우 기존 chatgpt_result 반환
  - ChatGPT timeout/오류 발생 시 DB 저장 없음 (정제 실패 데이터는 저장하지 않음)
- SQLite DB 파일 (`similarity.db`) 디스크 저장
- 유사도 threshold 및 DB 파일 경로 환경 변수로 관리
- 유사도 알고리즘 인터페이스 기반 설계 (교체 가능 구조)

## Capabilities

### New Capabilities
- `similarity-store`: interface_id를 key로 error_stack + chatgpt_result를 SQLite에 저장/조회하는 기능
- `similarity-search`: 새 error_stack과 저장된 텍스트를 TF-IDF + Cosine Similarity로 비교하여 유사 결과 반환

### Modified Capabilities

## Impact

- `app/services/similarity_service.py`: 신규 생성 — 저장, 조회, 유사도 비교 로직
- `app/config.py`: `SIMILARITY_DB_PATH`, `SIMILARITY_THRESHOLD` 환경 변수 추가
- `tests/test_similarity_service.py`: 저장/조회/유사도 비교 단위 테스트
- `requirements.txt`: `scikit-learn` 추가

### SQLite 테이블 구조
```sql
CREATE TABLE similarity_store (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    interface_id  TEXT NOT NULL,
    error_stack   TEXT NOT NULL,
    chatgpt_result TEXT NOT NULL,
    created_at    TEXT NOT NULL
);
CREATE INDEX idx_interface_id ON similarity_store(interface_id);
```
