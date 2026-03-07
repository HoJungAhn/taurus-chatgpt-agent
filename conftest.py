"""
pytest 전역 설정 모듈 (conftest.py).

pytest가 테스트 모듈을 import하기 전에 이 파일이 먼저 실행된다.
app.config.Settings는 모듈 로드 시점에 환경 변수를 검증하므로,
테스트 환경에서 필수 환경 변수가 없으면 ValidationError가 발생한다.

os.environ.setdefault를 사용하여 실제 .env 파일이 없어도
테스트가 정상적으로 실행될 수 있도록 최소한의 환경 변수를 설정한다.
setdefault는 해당 키가 이미 존재하면 덮어쓰지 않으므로, 실제 환경 변수가
설정된 경우에는 그 값이 우선 사용된다.
"""

import os

# 테스트 환경에서 app.config.Settings 초기화에 필요한 필수 환경 변수 설정.
# 실제 HTTP 호출이 발생하지 않도록 테스트에서는 mock으로 대체하므로
# 값이 유효한 URL일 필요는 없다.
os.environ.setdefault("CHATGPT_API_URL", "http://localhost:8001/service/chatgpt")
os.environ.setdefault("CHATGPT_API_KEY", "test-key")
os.environ.setdefault("CHATGPT_SYSTEM_PROMPT", "Test system prompt")
