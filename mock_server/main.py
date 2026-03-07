"""
mock-chatgpt-server 메인 애플리케이션 모듈.

실제 ChatGPT API를 사용할 수 없는 개발/테스트 환경에서
OpenAI Chat Completions API와 동일한 스키마로 고정 응답을 반환하는 독립 서버다.

CHATGPT_API_URL 환경 변수를 이 서버의 URL로 지정하면
taurus-chatgpt-agent가 이 서버를 실제 ChatGPT처럼 사용한다.
실제 ChatGPT로 전환 시에는 URL만 변경하면 된다.
"""

import uvicorn
from fastapi import FastAPI
from mock_server.routes import router

app = FastAPI(title="mock-chatgpt-server")

# POST /service/chatgpt 엔드포인트를 앱에 등록한다.
app.include_router(router)


if __name__ == "__main__":
    # python -m mock_server.main 으로 직접 실행할 때의 진입점.
    # 포트는 MOCK_PORT 환경 변수로 설정 (기본값 8001).
    from mock_server.config import mock_settings
    uvicorn.run("mock_server.main:app", host="0.0.0.0", port=mock_settings.mock_port, reload=False)
