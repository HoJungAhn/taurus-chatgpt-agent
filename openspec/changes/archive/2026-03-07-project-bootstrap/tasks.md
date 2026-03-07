## 1. 메인 서비스 디렉토리 구조 생성

- [x] 1.1 `app/`, `app/api/`, `app/services/`, `app/models/` 디렉토리 생성 및 각 `__init__.py` 추가
- [x] 1.2 `tests/` 디렉토리 생성 및 `__init__.py` 추가
- [x] 1.3 `app/main.py` 생성 — FastAPI 앱 초기화 및 포트 9000 실행 설정 (라우터 등록은 빈 상태)

## 2. 메인 서비스 설정 파일 생성

- [x] 2.1 `app/config.py` 생성 — pydantic-settings `BaseSettings` 기반 환경 변수 관리
  - 필수: `CHATGPT_API_URL`, `CHATGPT_API_KEY`, `CHATGPT_SYSTEM_PROMPT`
  - 기본값: `APP_PORT=9000`, `CHATGPT_MODEL=gpt-4`, `CHATGPT_TIMEOUT=30`, `SIMILARITY_DB_PATH=similarity.db`, `SIMILARITY_THRESHOLD=0.8`
- [x] 2.2 `.env.example` 생성 — 모든 환경 변수 예시값 포함
- [x] 2.3 `.gitignore` 생성 — `.env`, `*.db`, `__pycache__/`, `*.pyc`, `.pytest_cache/` 포함

## 3. 메인 서비스 의존성 파일 생성

- [x] 3.1 `requirements.txt` 생성 — fastapi, uvicorn, httpx, pydantic, pydantic-settings, scikit-learn, pytest, pytest-asyncio 포함

## 4. mock_server 디렉토리 구조 생성

- [x] 4.1 `mock_server/` 디렉토리 생성 및 `__init__.py` 추가
- [x] 4.2 `mock_server/main.py` 생성 — FastAPI 앱 초기화 (엔드포인트는 빈 상태)
- [x] 4.3 `mock_server/config.py` 생성 — `MOCK_PORT`, `MOCK_BEARER_TOKEN` 환경 변수 관리
- [x] 4.4 `mock_server/requirements.txt` 생성 — fastapi, uvicorn, pydantic, pydantic-settings 포함
- [x] 4.5 `mock_server/.env.example` 생성 — `MOCK_PORT`, `MOCK_BEARER_TOKEN=abcdefghijk` 예시 포함

## 5. 구조 검증

- [x] 5.1 `app/` 패키지 import 확인 — `mock_server/` 없이도 `from app.config import settings` 정상 동작 확인
- [x] 5.2 필수 환경 변수 누락 시 `ValidationError` 발생 확인
- [x] 5.3 `uvicorn app.main:app --port 9000` 으로 메인 서비스 기동 확인 (빈 앱)
- [x] 5.4 `uvicorn mock_server.main:app` 으로 mock 서버 기동 확인 (빈 앱)
