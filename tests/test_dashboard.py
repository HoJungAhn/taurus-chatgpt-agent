"""
GET /dashboard 엔드포인트 단위 테스트 모듈.

FastAPI TestClient를 사용하여 실제 서버 없이 HTTP 요청을 시뮬레이션한다.
similarity_service의 get_summary와 get_all_interfaces를 mock으로 대체하여
DB 없이 대시보드 라우트 로직만 독립적으로 검증한다.

테스트 시나리오:
1. 정상 요청 → HTTP 200 + text/html Content-Type
2. 데이터 없는 상태 → "저장된 데이터 없음" 문자열 포함
3. 데이터 있는 상태 → interface_id와 통계 정보 포함
"""

from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app, similarity_service

# TestClient: 실제 서버 없이 FastAPI 앱에 HTTP 요청을 보낼 수 있는 동기 테스트 클라이언트.
# 내부적으로 requests 라이브러리를 사용하여 ASGI 앱을 직접 호출한다.
client = TestClient(app)


def test_dashboard_returns_200_html():
    """
    GET /dashboard 요청 시 HTTP 200과 HTML Content-Type을 반환하는지 검증.

    get_summary와 get_all_interfaces를 mock하여 빈 데이터 상황을 시뮬레이션한다.
    응답 헤더의 content-type이 "text/html"을 포함해야 한다.
    """
    with patch.object(similarity_service, "get_summary", return_value={"total": 0, "unique_interfaces": 0}), \
         patch.object(similarity_service, "get_all_interfaces", return_value=[]):
        response = client.get("/dashboard")
    assert response.status_code == 200
    # FastAPI TemplateResponse는 "text/html; charset=utf-8"을 반환하므로
    # "in" 연산자로 부분 일치 검증
    assert "text/html" in response.headers["content-type"]


def test_dashboard_shows_empty_message():
    """
    DB에 데이터가 없을 때 "저장된 데이터 없음" 메시지가 표시되는지 검증.

    get_all_interfaces가 빈 리스트를 반환하면 Jinja2 템플릿의 {% if %} 분기에서
    "저장된 데이터 없음" 메시지가 렌더링되어야 한다.
    """
    with patch.object(similarity_service, "get_summary", return_value={"total": 0, "unique_interfaces": 0}), \
         patch.object(similarity_service, "get_all_interfaces", return_value=[]):
        response = client.get("/dashboard")
    # HTML 응답 본문에 빈 상태 메시지가 포함되어야 한다
    assert "저장된 데이터 없음" in response.text


def test_dashboard_shows_interface_id():
    """
    데이터가 있을 때 interface_id와 통계 정보가 HTML에 렌더링되는지 검증.

    mock_interfaces: Jinja2 템플릿이 기대하는 데이터 구조.
    - interface_id: 인터페이스 식별자
    - count: 해당 인터페이스의 저장 건수
    - latest: 가장 최근 저장 시각 (ISO 8601 형식)
    - records: 개별 저장 레코드 목록 (error_stack, chatgpt_result, created_at)

    HTML에 "IF-001"과 "전체 저장 건수"가 포함되어야 한다.
    """
    mock_interfaces = [
        {
            "interface_id": "IF-001",
            "count": 2,
            "latest": "2026-03-07T12:00:00+00:00",
            "records": [
                {
                    "error_stack": "java.lang.NullPointerException",
                    "chatgpt_result": "분석 결과",
                    "created_at": "2026-03-07T12:00:00+00:00",
                }
            ],
        }
    ]
    with patch.object(similarity_service, "get_summary", return_value={"total": 2, "unique_interfaces": 1}), \
         patch.object(similarity_service, "get_all_interfaces", return_value=mock_interfaces):
        response = client.get("/dashboard")
    assert response.status_code == 200
    # 인터페이스 ID가 HTML에 렌더링되어야 한다
    assert "IF-001" in response.text
    # 통계 섹션의 레이블이 존재해야 한다
    assert "전체 저장 건수" in response.text
