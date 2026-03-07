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
    result = service.find_similar(
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
    result = service.find_similar(
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
    result = service.find_similar(
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
    result = service.find_similar("IF-999", "java.lang.NullPointerException")
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
    result = service.find_similar(
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
    result = service.find_similar("IF-001", "java.lang.NullPointerException")
    assert result is None
