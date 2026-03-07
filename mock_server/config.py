from pydantic_settings import BaseSettings


class MockSettings(BaseSettings):
    """Mock 서버 환경 변수 설정 클래스"""

    # Server settings
    mock_port: int = 8001

    # Bearer token for authentication
    mock_bearer_token: str = "abcdefghijk"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# 싱글톤 설정 인스턴스
mock_settings = MockSettings()
