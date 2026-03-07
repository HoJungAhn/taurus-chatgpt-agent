"""
Bearer token 인증 FastAPI Dependency 모듈.

Authorization 헤더에서 Bearer token을 추출하여 환경 변수(MOCK_BEARER_TOKEN)와 비교한다.
FastAPI의 Depends 시스템을 통해 라우트에 주입되므로, 인증 로직과 비즈니스 로직을 분리할 수 있다.
"""

from fastapi import Header, HTTPException
from mock_server.config import mock_settings


async def verify_bearer_token(authorization: str = Header(default=None)):
    """
    Authorization 헤더의 Bearer token을 검증하는 FastAPI Dependency 함수.

    검증 실패 조건:
    - Authorization 헤더가 없는 경우
    - "Bearer " 접두사로 시작하지 않는 경우
    - token 값이 MOCK_BEARER_TOKEN과 일치하지 않는 경우

    실패 시 HTTP 401 Unauthorized를 반환한다.
    성공 시 None을 반환하며, 라우트 함수는 _: None = Depends(verify_bearer_token)으로 사용한다.

    Args:
        authorization: HTTP Authorization 헤더 값. FastAPI가 자동으로 주입한다.
    """
    # Authorization 헤더 누락 또는 형식 불일치 확인
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # "Bearer " 접두사를 제거하여 실제 token 값만 추출
    token = authorization.removeprefix("Bearer ")

    # 환경 변수로 설정된 허용 token과 비교
    if token != mock_settings.mock_bearer_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
