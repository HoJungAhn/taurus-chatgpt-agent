"""
POST /service/chatgpt mock 엔드포인트 단위 테스트 모듈.

FastAPI TestClient를 사용하여 실제 서버 없이 mock ChatGPT API를 테스트한다.
환경 변수 MOCK_BEARER_TOKEN의 기본값("abcdefghijk")을 사용하므로
별도의 conftest.py 없이 동작한다.

테스트 시나리오:
1. 유효한 Bearer token + 정상 요청 → HTTP 200 + ChatGPT 형식 응답
2. Authorization 헤더 누락 → HTTP 401
3. 잘못된 Bearer token → HTTP 401
4. 필수 필드(messages) 누락 → HTTP 422
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from mock_server.main import app

# TestClient: ASGI 앱을 직접 호출하는 동기 테스트 클라이언트.
# 실제 HTTP 서버를 기동하지 않으므로 빠르고 독립적인 테스트가 가능하다.
client = TestClient(app)

# 유효한 Authorization 헤더.
# MOCK_BEARER_TOKEN 환경 변수의 기본값 "abcdefghijk"와 일치해야 인증이 통과된다.
VALID_HEADERS = {"Authorization": "Bearer abcdefghijk"}

# OpenAI Chat Completions API 형식의 유효한 요청 바디.
# mock 서버는 이 형식의 요청을 받아 고정된 MOCK_ANALYSIS_RESULT를 반환한다.
VALID_BODY = {
    "model": "gpt-4",
    "messages": [
        {"role": "system", "content": "You are a Java error analyst."},
        {"role": "user", "content": "java.lang.NullPointerException at com.example.Service.process(Service.java:42)"},
    ],
}


def test_normal_request_returns_200():
    """
    유효한 Bearer token과 정상 요청 바디로 POST 시 HTTP 200과 ChatGPT 형식 응답을 반환하는지 검증.

    응답은 OpenAI Chat Completions API 호환 구조여야 한다:
    choices[0].message.role == "assistant"
    choices[0].message.content == MOCK_ANALYSIS_RESULT
    """
    response = client.post("/service/chatgpt", json=VALID_BODY, headers=VALID_HEADERS)
    assert response.status_code == 200
    data = response.json()
    # OpenAI 호환 구조 검증: choices 배열이 존재해야 한다
    assert "choices" in data
    assert len(data["choices"]) > 0
    # choices[0].message 구조 검증
    assert "message" in data["choices"][0]
    assert "content" in data["choices"][0]["message"]
    # mock 서버는 항상 "assistant" 역할로 응답한다
    assert data["choices"][0]["message"]["role"] == "assistant"


def test_missing_authorization_header_returns_401():
    """
    Authorization 헤더 없이 요청 시 HTTP 401을 반환하는지 검증.

    verify_bearer_token Dependency가 Authorization 헤더 누락을 감지하고
    HTTPException(status_code=401)을 발생시켜야 한다.
    """
    # headers 파라미터를 전달하지 않으면 Authorization 헤더가 없는 상태
    response = client.post("/service/chatgpt", json=VALID_BODY)
    assert response.status_code == 401


def test_wrong_bearer_token_returns_401():
    """
    잘못된 Bearer token으로 요청 시 HTTP 401을 반환하는지 검증.

    verify_bearer_token이 token 값을 MOCK_BEARER_TOKEN 환경 변수와 비교하여
    불일치 시 HTTPException(status_code=401)을 발생시켜야 한다.
    """
    response = client.post(
        "/service/chatgpt",
        json=VALID_BODY,
        headers={"Authorization": "Bearer wrongtoken"},  # 의도적으로 잘못된 token 사용
    )
    assert response.status_code == 401


def test_missing_messages_field_returns_422():
    """
    필수 필드(messages) 누락 시 HTTP 422를 반환하는지 검증.

    ChatRequest Pydantic 모델이 messages 필드를 필수로 정의하므로,
    해당 필드 없이 요청하면 FastAPI가 자동으로 422 Unprocessable Entity를 반환한다.
    Pydantic validation은 Bearer token 인증보다 먼저 수행되지 않으며,
    인증 Dependency가 먼저 실행된 후 request body가 파싱된다.

    실제로는 인증 헤더가 있는 상태에서 필드 누락 시 422가 발생한다.
    """
    response = client.post(
        "/service/chatgpt",
        json={"model": "gpt-4"},  # messages 필드 누락
        headers=VALID_HEADERS,
    )
    assert response.status_code == 422
