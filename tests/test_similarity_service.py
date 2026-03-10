"""
TFIDFSimilarityService 단위 테스트 모듈.

실제 디스크 파일 대신 pytest의 tmp_path fixture를 사용하여
테스트 전용 임시 SQLite DB를 생성한다.
각 테스트는 완전히 독립된 DB 인스턴스를 사용하므로 테스트 간 간섭이 없다.

테스트 시나리오:
1. 저장 후 동일한 error_stack 조회 → 일치 결과 반환
2. 임계값 이상 유사도 → 기존 결과 반환
3. 임계값 미만 유사도 → None 반환
4. 데이터 없는 상태 조회 → None 반환
5. 다른 interface_id 데이터는 조회되지 않음 (격리 보장)
6. save 호출 없이 조회 → None 반환 (timeout 시나리오 재현)
7. max_records 미만 저장 시 축출 없음
8. max_records+1번째 저장 시 가장 오래된 row 삭제
9. NULL last_accessed_at을 가진 row가 가장 먼저 축출됨
10. find_similar() HIT 시 last_accessed_at 갱신
11. find_similar() MISS 시 last_accessed_at 변경 없음
12. max_records_per_interface=3으로 초기화하여 3건 제한 동작 검증
"""

import pytest
from app.services.similarity_service import TFIDFSimilarityService

# 테스트 전반에서 공통으로 사용하는 similarity threshold 값.
# 0.8 = 80% 이상 유사해야 캐시 히트로 판정한다.
THRESHOLD = 0.8


@pytest.fixture
def service(tmp_path):
    """
    테스트용 TFIDFSimilarityService fixture.

    tmp_path: pytest built-in fixture로, 테스트마다 고유한 임시 디렉터리를 제공한다.
    테스트 종료 시 pytest가 임시 디렉터리를 자동으로 정리한다.

    yield 패턴: yield 전이 setup(DB 초기화), yield 후가 teardown(DB 연결 해제).
    이를 통해 하나의 함수로 setup/teardown을 표현할 수 있다.

    Yields:
        TFIDFSimilarityService: 초기화된 테스트용 서비스 인스턴스
    """
    # 임시 경로에 테스트 전용 SQLite DB 파일 생성
    svc = TFIDFSimilarityService(db_path=str(tmp_path / "test.db"), threshold=THRESHOLD)
    svc.init_db()  # similarity_records 테이블 생성
    yield svc      # 테스트 함수에 서비스 인스턴스 전달
    svc.close_db() # 테스트 종료 후 DB 연결 해제


def test_save_and_find_identical(service):
    """
    저장한 error_stack과 동일한 문자열 조회 시 결과를 반환하는지 검증.

    완전히 동일한 문자열은 cosine similarity = 1.0 이므로
    threshold(0.8)를 초과하여 반드시 캐시 히트가 발생해야 한다.
    """
    service.save(
        "IF-001",
        "java.lang.NullPointerException at com.example.Service.process",
        "분석 결과",
    )
    result, ratio = service.find_similar(
        "IF-001",
        "java.lang.NullPointerException at com.example.Service.process",
    )
    assert result == "분석 결과"


def test_find_similar_above_threshold(service):
    """
    임계값(0.8) 이상의 유사한 error_stack 조회 시 기존 결과를 반환하는지 검증.

    동일한 문자열은 cosine similarity = 1.0으로 threshold를 초과한다.
    실제 유사도가 정확히 threshold를 넘는 경계값 케이스를 검증한다.
    """
    service.save(
        "IF-001",
        "java.lang.NullPointerException at com.example.Service.process(Service.java:42)",
        "기존 결과",
    )
    result, ratio = service.find_similar(
        "IF-001",
        "java.lang.NullPointerException at com.example.Service.process(Service.java:42)",
    )
    assert result == "기존 결과"


def test_find_similar_below_threshold(service):
    """
    임계값(0.8) 미만의 유사도를 가진 error_stack 조회 시 None을 반환하는지 검증.

    NullPointerException과 IOException은 오류 유형 자체가 다르므로
    TF-IDF cosine similarity가 0.8 미만으로 계산되어 캐시 미스가 발생해야 한다.
    """
    service.save(
        "IF-001",
        "java.lang.NullPointerException at com.example.Foo.bar",
        "분석 결과",
    )
    # 완전히 다른 유형의 오류 → 낮은 cosine similarity → 캐시 미스
    result, ratio = service.find_similar(
        "IF-001",
        "java.io.IOException at com.example.Network.connect(Network.java:99)",
    )
    assert result is None


def test_find_similar_no_data(service):
    """
    DB에 데이터가 없을 때 조회 시 None을 반환하는지 검증.

    corpus가 비어 있으면 TF-IDF 벡터를 생성할 수 없으므로
    find_similar는 조기에 None을 반환해야 한다.
    """
    # 아무것도 저장하지 않은 상태에서 조회
    result, ratio = service.find_similar("IF-999", "java.lang.NullPointerException")
    assert result is None


def test_different_interface_id_not_referenced(service):
    """
    다른 interface_id로 저장된 데이터는 조회되지 않음을 검증.

    유사도 검색은 동일한 interface_id 내에서만 수행되어야 한다.
    IF-001로 저장된 결과가 IF-002 조회에서 반환되어서는 안 된다.

    이는 인터페이스 간 데이터 격리(isolation)를 보장하는 핵심 테스트다.
    """
    # IF-001에 데이터 저장
    service.save(
        "IF-001",
        "java.lang.NullPointerException at com.example.Service.process(Service.java:42)",
        "IF-001 결과",
    )
    # 동일한 error_stack이지만 IF-002로 조회 → 격리되어야 함
    result, ratio = service.find_similar(
        "IF-002",
        "java.lang.NullPointerException at com.example.Service.process(Service.java:42)",
    )
    assert result is None


def test_no_save_on_timeout(service):
    """
    save를 호출하지 않은 경우 조회 시 None을 반환하는지 검증.

    ChatGPT timeout/오류 시 save를 호출하지 않는 것이 설계 요구사항이다.
    이 테스트는 그 상황(저장 없이 조회)을 재현하여
    미저장 상태에서 정상적으로 None이 반환되는지 확인한다.
    """
    # save를 호출하지 않음 → DB에 데이터 없음
    result, ratio = service.find_similar("IF-001", "java.lang.NullPointerException")
    assert result is None


# ─── LRU 축출 테스트 ────────────────────────────────────────────────────────


@pytest.fixture
def lru_service(tmp_path):
    """
    LRU 테스트용 fixture. max_records_per_interface=3으로 제한하여
    소수의 저장으로 LRU 동작을 빠르게 검증한다.

    Yields:
        TFIDFSimilarityService: max_records=3으로 초기화된 서비스 인스턴스
    """
    svc = TFIDFSimilarityService(
        db_path=str(tmp_path / "lru_test.db"),
        threshold=THRESHOLD,
        max_records_per_interface=3,
    )
    svc.init_db()
    yield svc
    svc.close_db()


def _count_records(service, interface_id: str) -> int:
    """테스트 헬퍼: 특정 interface_id의 DB 저장 건수를 반환한다."""
    return service._conn.execute(
        "SELECT COUNT(*) FROM similarity_store WHERE interface_id = ?",
        (interface_id,),
    ).fetchone()[0]


def _get_last_accessed_at(service, record_id: int):
    """테스트 헬퍼: 특정 id row의 last_accessed_at 값을 반환한다."""
    return service._conn.execute(
        "SELECT last_accessed_at FROM similarity_store WHERE id = ?",
        (record_id,),
    ).fetchone()[0]


def _get_all_ids(service, interface_id: str):
    """테스트 헬퍼: 특정 interface_id의 모든 row id를 삽입 순서로 반환한다."""
    return [
        row[0]
        for row in service._conn.execute(
            "SELECT id FROM similarity_store WHERE interface_id = ? ORDER BY id ASC",
            (interface_id,),
        ).fetchall()
    ]


def test_lru_no_eviction_below_max(lru_service):
    """
    max_records 미만 저장 시 축출이 발생하지 않음을 검증.

    max_records=3인 상태에서 2건 저장 후 건수가 2건으로 유지되어야 한다.
    """
    lru_service.save("IF-001", "java.lang.NullPointerException at Foo.bar", "결과1")
    lru_service.save("IF-001", "java.io.IOException at Network.connect", "결과2")
    assert _count_records(lru_service, "IF-001") == 2


def test_lru_eviction_on_exceed(lru_service):
    """
    max_records+1번째 저장 시 가장 오래된 row가 삭제되어 건수가 max_records를 유지함을 검증.

    max_records=3으로 3건 저장 후 4번째 저장 시 건수는 3건이어야 한다.
    """
    lru_service.save("IF-001", "java.lang.NullPointerException at Foo.bar", "결과1")
    lru_service.save("IF-001", "java.io.IOException at Network.connect", "결과2")
    lru_service.save("IF-001", "java.lang.OutOfMemoryError at Heap.alloc", "결과3")
    assert _count_records(lru_service, "IF-001") == 3

    lru_service.save("IF-001", "java.lang.ClassCastException at Parser.parse", "결과4")
    assert _count_records(lru_service, "IF-001") == 3


def test_lru_evicts_null_last_accessed_first(lru_service):
    """
    NULL last_accessed_at을 가진 row가 가장 먼저 축출됨을 검증.

    3건 저장(모두 NULL last_accessed_at) 후 4번째 저장 시
    가장 먼저 삽입된 row(id가 가장 작은 row)가 삭제되어야 한다.
    """
    lru_service.save("IF-001", "java.lang.NullPointerException at Foo.bar", "결과1")
    lru_service.save("IF-001", "java.io.IOException at Network.connect", "결과2")
    lru_service.save("IF-001", "java.lang.OutOfMemoryError at Heap.alloc", "결과3")

    ids_before = _get_all_ids(lru_service, "IF-001")
    first_id = ids_before[0]

    lru_service.save("IF-001", "java.lang.ClassCastException at Parser.parse", "결과4")

    ids_after = _get_all_ids(lru_service, "IF-001")
    # 첫 번째 row가 삭제되어야 함
    assert first_id not in ids_after
    assert _count_records(lru_service, "IF-001") == 3


def test_lru_hit_updates_last_accessed_at(lru_service):
    """
    find_similar() HIT 시 해당 row의 last_accessed_at이 갱신됨을 검증.

    저장 직후 last_accessed_at은 NULL이어야 하고,
    cache HIT 후에는 UTC 시각으로 갱신되어야 한다.
    """
    lru_service.save("IF-001", "java.lang.NullPointerException at Foo.bar", "결과1")
    row_id = _get_all_ids(lru_service, "IF-001")[0]

    # 저장 직후 last_accessed_at은 NULL
    assert _get_last_accessed_at(lru_service, row_id) is None

    # 동일 문자열로 조회 → HIT
    result, ratio = lru_service.find_similar("IF-001", "java.lang.NullPointerException at Foo.bar")
    assert result == "결과1"

    # HIT 후 last_accessed_at이 갱신되어야 함
    assert _get_last_accessed_at(lru_service, row_id) is not None


def test_lru_miss_does_not_update_last_accessed_at(lru_service):
    """
    find_similar() MISS 시 어떤 row의 last_accessed_at도 변경되지 않음을 검증.
    """
    lru_service.save("IF-001", "java.lang.NullPointerException at Foo.bar", "결과1")
    row_id = _get_all_ids(lru_service, "IF-001")[0]

    # MISS 쿼리 (다른 오류 유형)
    result, ratio = lru_service.find_similar(
        "IF-001",
        "java.io.IOException at completely.different.Package.method",
    )
    assert result is None
    # MISS 후 last_accessed_at은 여전히 NULL
    assert _get_last_accessed_at(lru_service, row_id) is None


def test_lru_hit_survives_eviction(lru_service):
    """
    cache HIT된 row는 last_accessed_at이 갱신되어 축출 대상에서 제외됨을 검증.

    A, B, C 저장 후 A를 HIT시키면 last_accessed_at이 갱신된다.
    D를 저장(4번째)하면 B(가장 오래된 NULL)가 삭제되고 A는 유지되어야 한다.
    """
    lru_service.save("IF-001", "java.lang.NullPointerException at Foo.bar", "결과A")
    lru_service.save("IF-001", "java.io.IOException at Network.connect", "결과B")
    lru_service.save("IF-001", "java.lang.OutOfMemoryError at Heap.alloc", "결과C")

    ids = _get_all_ids(lru_service, "IF-001")
    id_a, id_b = ids[0], ids[1]

    # A를 HIT시켜 last_accessed_at 갱신
    lru_service.find_similar("IF-001", "java.lang.NullPointerException at Foo.bar")

    # D 저장 → B(NULL이므로 가장 오래됨)가 삭제되어야 함
    lru_service.save("IF-001", "java.lang.ClassCastException at Parser.parse", "결과D")

    ids_after = _get_all_ids(lru_service, "IF-001")
    assert id_a in ids_after    # A는 HIT되었으므로 유지
    assert id_b not in ids_after  # B는 NULL이므로 먼저 축출


# ─── 로깅 테스트 ─────────────────────────────────────────────────────────────


def test_logging_skip_when_no_data(service, caplog):
    """
    stored=0 시 SKIP 로그가 출력되고 (None, None)을 반환하는지 검증.
    """
    import logging
    with caplog.at_level(logging.INFO, logger="app.services.similarity_service"):
        result, ratio = service.find_similar("IF-999", "java.lang.NullPointerException")

    assert result is None
    assert ratio is None
    assert "result=SKIP" in caplog.text
    assert "IF-999" in caplog.text


def test_logging_hit(service, caplog):
    """
    HIT 시 result=HIT 로그가 출력되고 (chatgpt_result, float)를 반환하는지 검증.
    """
    import logging
    service.save("IF-001", "java.lang.NullPointerException at Foo.bar", "분석 결과")

    with caplog.at_level(logging.INFO, logger="app.services.similarity_service"):
        result, ratio = service.find_similar("IF-001", "java.lang.NullPointerException at Foo.bar")

    assert result == "분석 결과"
    assert isinstance(ratio, float)
    assert "result=HIT" in caplog.text
    assert "IF-001" in caplog.text


def test_logging_miss(service, caplog):
    """
    MISS 시 result=MISS 로그가 출력되고 (None, float)를 반환하는지 검증.
    """
    import logging
    service.save("IF-001", "java.lang.NullPointerException at Foo.bar", "분석 결과")

    with caplog.at_level(logging.INFO, logger="app.services.similarity_service"):
        result, ratio = service.find_similar(
            "IF-001",
            "java.io.IOException at completely.different.Package.method",
        )

    assert result is None
    assert isinstance(ratio, float)
    assert "result=MISS" in caplog.text
    assert "IF-001" in caplog.text
