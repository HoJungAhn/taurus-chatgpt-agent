## 1. DB 초기화 구현

- [x] 1.1 `app/services/similarity_service.py` 생성 — `BaseSimilarityService` 추상 인터페이스 정의 (`save`, `find_similar` 메서드)
- [x] 1.2 `TFIDFSimilarityService` 구현 클래스 작성 — SQLite 연결 초기화 및 테이블/인덱스 생성 (`similarity_store` 테이블)
- [x] 1.3 FastAPI lifespan 이벤트에 DB 초기화 연결 (`app/main.py` 업데이트)

## 2. 저장 기능 구현

- [x] 2.1 `save(interface_id, error_stack, chatgpt_result)` 메서드 구현 — `created_at` ISO8601 포함하여 SQLite INSERT

## 3. 유사도 검색 구현

- [x] 3.1 `find_similar(interface_id, error_stack)` 메서드 구현
  - 동일 `interface_id`의 모든 `error_stack` 조회
  - 데이터 없으면 `None` 반환
  - TF-IDF vectorizer로 기존 텍스트들 + 새 텍스트 fit_transform
  - cosine_similarity 계산 → threshold 이상이면 해당 `chatgpt_result` 반환, 미만이면 `None` 반환

## 4. 설정 연동

- [x] 4.1 `SIMILARITY_DB_PATH`, `SIMILARITY_THRESHOLD` 환경 변수를 `app/config.py`에서 읽어 사용 확인

## 5. 테스트 코드 작성

- [x] 5.1 `tests/test_similarity_service.py` 생성
  - 데이터 저장 후 조회 확인
  - 유사도 threshold 이상 → 기존 결과 반환 확인
  - 유사도 threshold 미만 → None 반환 확인
  - 미존재 interface_id → None 반환 확인
  - 타 interface_id 데이터 미참조 확인
  - ChatGPT timeout 시 저장 없음 확인 (save 미호출 시 DB 미변경 검증)

## 6. 동작 검증

- [x] 6.1 pytest 실행하여 모든 테스트 통과 확인
