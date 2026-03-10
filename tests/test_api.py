"""
POST /api/refine 엔드포인트 단위 테스트.

FastAPI TestClient를 사용하여 실제 서버 없이 HTTP 요청을 시뮬레이션한다.
similarity_service와 call_chatgpt를 mock으로 대체하여 라우트 로직만 독립적으로 검증한다.

테스트 시나리오:
1. similarity DB 캐시 히트 → status="cached"
2. ChatGPT 호출 성공 → status="success", DB 저장 호출 확인
3. ChatGPT timeout → status="timeout", DB 저장 미호출 확인
4. ChatGPT 오류 → status="chatgpt_error", DB 저장 미호출 확인
5. 필수 필드 누락 → HTTP 422
6. response에 ratio 필드 포함 검증
7. stored=0 케이스에서 ratio가 null임을 검증
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app, similarity_service

# TestClient: 실제 서버 없이 FastAPI 앱에 HTTP 요청을 보낼 수 있는 동기 테스트 클라이언트
client = TestClient(app)

# 테스트 전반에서 공통으로 사용하는 유효한 요청 바디
VALID_BODY = {
    "interface_id": "IF-001",
    "error_stack": "java.lang.NullPointerException at com.example.Service.process(Service.java:42)",
}


def test_cached_response():
    """
    similarity DB에 유사한 결과가 있을 때 캐시 응답을 반환하는지 검증.

    find_similar를 mock하여 캐시 히트 상황을 시뮬레이션한다.
    ChatGPT 호출 없이 즉시 status="cached"로 응답해야 한다.
    """
    with patch.object(similarity_service, "find_similar", return_value=("캐시된 결과", 0.95)):
        response = client.post("/api/refine", json=VALID_BODY)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cached"
    assert data["is_refined"] is True
    assert data["refine_message"] == "캐시된 결과"
    assert data["interface_id"] == "IF-001"


def test_chatgpt_success():
    """
    ChatGPT 호출 성공 시 결과를 반환하고 DB에 저장하는지 검증.

    find_similar가 (None, 0.5)를 반환(캐시 미스)하고,
    call_chatgpt가 성공적으로 결과를 반환하는 상황을 시뮬레이션한다.
    save()가 정확히 한 번 호출되어야 한다.
    """
    with patch.object(similarity_service, "find_similar", return_value=(None, 0.5)), \
         patch.object(similarity_service, "save") as mock_save, \
         patch("app.api.routes.call_chatgpt", return_value="ChatGPT 분석 결과"):
        response = client.post("/api/refine", json=VALID_BODY)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["is_refined"] is True
    assert data["refine_message"] == "ChatGPT 분석 결과"
    # 성공 시에만 DB 저장이 호출되어야 한다
    mock_save.assert_called_once()


def test_chatgpt_timeout():
    """
    ChatGPT API가 timeout 될 때 원본 error_stack을 반환하고 DB에 저장하지 않는지 검증.

    call_chatgpt가 TimeoutError를 발생시키는 상황을 시뮬레이션한다.
    refine_message는 원본 error_stack이어야 하며, save()는 호출되어선 안 된다.
    """
    from app.services.chatgpt_service import TimeoutError as ChatGPTTimeoutError
    with patch.object(similarity_service, "find_similar", return_value=(None, 0.3)), \
         patch("app.api.routes.call_chatgpt", side_effect=ChatGPTTimeoutError()), \
         patch.object(similarity_service, "save") as mock_save:
        response = client.post("/api/refine", json=VALID_BODY)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "timeout"
    assert data["is_refined"] is False
    # timeout 시 원본 error_stack을 그대로 반환해야 한다
    assert data["refine_message"] == VALID_BODY["error_stack"]
    # timeout 시에는 DB에 저장하면 안 된다
    mock_save.assert_not_called()


def test_chatgpt_error():
    """
    ChatGPT API 오류 발생 시 원본 error_stack을 반환하고 DB에 저장하지 않는지 검증.

    call_chatgpt가 ChatGPTError를 발생시키는 상황을 시뮬레이션한다.
    """
    from app.services.chatgpt_service import ChatGPTError
    with patch.object(similarity_service, "find_similar", return_value=(None, 0.2)), \
         patch("app.api.routes.call_chatgpt", side_effect=ChatGPTError()), \
         patch.object(similarity_service, "save") as mock_save:
        response = client.post("/api/refine", json=VALID_BODY)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "chatgpt_error"
    assert data["is_refined"] is False
    # 오류 시 원본 error_stack을 그대로 반환해야 한다
    assert data["refine_message"] == VALID_BODY["error_stack"]
    # 오류 시에는 DB에 저장하면 안 된다
    mock_save.assert_not_called()


def test_missing_fields_returns_422():
    """
    필수 필드(error_stack) 누락 시 HTTP 422를 반환하는지 검증.

    Pydantic이 자동으로 유효성 검증을 수행하여 FastAPI가 422를 반환한다.
    """
    response = client.post("/api/refine", json={"interface_id": "IF-001"})
    assert response.status_code == 422


def test_response_contains_ratio_on_hit():
    """
    similarity HIT 시 response에 ratio 필드가 포함됨을 검증.

    find_similar가 (result, 0.95) tuple을 반환하면
    response의 ratio 필드에 0.95가 포함되어야 한다.
    """
    with patch.object(similarity_service, "find_similar", return_value=("캐시된 결과", 0.95)):
        response = client.post("/api/refine", json=VALID_BODY)
    assert response.status_code == 200
    data = response.json()
    assert "ratio" in data
    assert data["ratio"] == pytest.approx(0.95)


def test_response_ratio_is_null_when_no_stored_data():
    """
    stored=0 케이스(stored 데이터 없음)에서 response의 ratio가 null임을 검증.

    find_similar가 (None, None) tuple을 반환하면(SKIP 케이스)
    response의 ratio 필드는 null이어야 한다.
    """
    with patch.object(similarity_service, "find_similar", return_value=(None, None)), \
         patch.object(similarity_service, "save"), \
         patch("app.api.routes.call_chatgpt", return_value="ChatGPT 분석 결과"):
        response = client.post("/api/refine", json=VALID_BODY)
    assert response.status_code == 200
    data = response.json()
    assert data["ratio"] is None
