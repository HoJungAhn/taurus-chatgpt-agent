## Why

`mock-chatgpt-service`, `similarity-db`, `restapi-recive-layer` 모든 change가 공통으로 참조하는
프로젝트 기반 파일(FastAPI 앱 진입점, 환경 변수 설정, 의존성 목록)이 없으면 각 change 구현 시 충돌과 혼선이 발생한다.
가장 먼저 프로젝트 뼈대를 구성하여 이후 change들이 일관된 기반 위에서 개발될 수 있도록 한다.

## What Changes

### taurus-chatgpt-agent (메인 서비스, 포트 9000)
- `app/__init__.py`: 패키지 초기화
- `app/main.py`: FastAPI 앱 생성 및 라우터 등록, 포트 9000 실행
- `app/config.py`: 전체 환경 변수 통합 관리
  - `APP_PORT` (기본값: 9000)
  - `CHATGPT_API_URL`: ChatGPT(or mock) 서비스 호출 URL
  - `CHATGPT_API_KEY`: Bearer token 값
  - `CHATGPT_MODEL` (기본값: `gpt-4`)
  - `CHATGPT_TIMEOUT` (기본값: 30)
  - `CHATGPT_SYSTEM_PROMPT`: ChatGPT system prompt 문자열
  - `SIMILARITY_DB_PATH` (기본값: `similarity.db`)
  - `SIMILARITY_THRESHOLD` (기본값: 0.8)
- `app/api/__init__.py`
- `app/services/__init__.py`
- `app/models/__init__.py`
- `tests/__init__.py`
- `requirements.txt`: 전체 의존성 (fastapi, uvicorn, httpx, pydantic, scikit-learn)
- `.env.example`: 환경 변수 예시 파일
- `.gitignore`: `.env`, `*.db`, `__pycache__` 등 제외

### mock-chatgpt-server (독립 테스트 서비스)
- `mock_server/__init__.py`
- `mock_server/main.py`: FastAPI 앱 생성, 포트 환경 변수로 설정
- `mock_server/config.py`: `MOCK_PORT`, `MOCK_BEARER_TOKEN` 환경 변수
- `mock_server/requirements.txt`: fastapi, uvicorn, pydantic
- `mock_server/.env.example`

## Capabilities

### New Capabilities
- `project-structure`: 두 서비스의 디렉토리 구조 및 공통 설정 파일 초기화

### Modified Capabilities

## Impact

- 이후 모든 change(`mock-chatgpt-service`, `similarity-db`, `restapi-recive-layer`)가 이 bootstrap 위에서 구현됨
- `app/config.py`는 모든 서비스 모듈이 import하는 단일 설정 소스
- `requirements.txt`는 각 change 구현 시 필요한 라이브러리를 추가하는 기준 파일
