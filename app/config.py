"""
애플리케이션 환경 변수 설정 모듈.

pydantic-settings의 BaseSettings를 사용하여 .env 파일 또는 OS 환경 변수에서
자동으로 값을 읽어온다. 필수 필드가 누락된 경우 앱 시작 시 ValidationError가 발생한다.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 환경 변수 설정 클래스"""

    # 서비스 포트. 기본값 9000.
    app_port: int = 9000

    # ChatGPT API 접속 정보 (필수 환경 변수).
    # mock 서버 사용 시: CHATGPT_API_URL=http://localhost:8001/service/chatgpt
    # 실제 OpenAI 사용 시: CHATGPT_API_URL=https://api.openai.com/v1/chat/completions
    chatgpt_api_url: str
    chatgpt_api_key: str         # Bearer token 인증 키
    chatgpt_system_prompt: str   # ChatGPT system role에 전달할 프롬프트

    # ChatGPT API 선택적 설정 (기본값 제공).
    chatgpt_model: str = "gpt-4"  # 사용할 ChatGPT 모델명
    chatgpt_timeout: int = 30     # API 응답 대기 timeout (초)

    # Similarity DB 설정.
    similarity_db_path: str = "similarity.db"  # SQLite DB 파일 경로
    similarity_threshold: float = 0.8          # 캐시 히트 판단 유사도 임계값 (0~1)

    class Config:
        env_file = ".env"          # 프로젝트 루트의 .env 파일에서 자동 로딩
        env_file_encoding = "utf-8"
        extra = "ignore"           # .env에 정의되지 않은 필드는 무시 (mock_server 변수 등)


# 모듈 로드 시 한 번만 생성하는 싱글톤 설정 인스턴스.
# 다른 모듈에서 `from app.config import settings`로 임포트하여 사용한다.
settings = Settings()
