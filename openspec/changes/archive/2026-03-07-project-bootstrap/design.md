## Context

두 개의 독립 서비스(`taurus-chatgpt-agent`, `mock-chatgpt-server`)를 구성하는 프로젝트 뼈대가 없는 상태.
이후 모든 change(`mock-chatgpt-service`, `similarity-db`, `restapi-recive-layer`)가 공통으로 참조하는
디렉토리 구조, 환경 변수 설정, 의존성 목록을 먼저 확립한다.

## Goals / Non-Goals

**Goals:**
- 두 서비스의 디렉토리 구조 및 패키지 초기화 (`__init__.py`)
- 환경 변수 기반 설정 파일 (`app/config.py`, `mock_server/config.py`)
- 전체 의존성 파일 (`requirements.txt` × 2)
- `.env.example` 제공으로 개발 환경 설정 가이드
- `.gitignore` 설정
- **mock 서버를 나중에 삭제 가능한 구조로 완전 분리**

**Non-Goals:**
- 실제 API 엔드포인트 구현 (각 change에서 담당)
- DB 스키마 생성 (similarity-db change에서 담당)
- 테스트 코드 작성 (각 change에서 담당)

## Decisions

### 결정 1: mock_server는 코드 레벨 의존성 없이 완전 분리
```
taurus-chatgpt-agent/   ← 메인 서비스 루트
├── app/                ← 메인 서비스 패키지 (mock 코드 import 없음)
│   └── config.py       ← CHATGPT_API_URL 환경 변수로만 mock 참조
└── mock_server/        ← 독립 실행 패키지 (삭제 시 메인 서비스 영향 없음)
    ├── main.py
    ├── config.py
    └── requirements.txt
```
- **이유**: mock 삭제 시 `mock_server/` 디렉토리만 제거하면 됨. 메인 서비스 코드 수정 불필요.
- **실제 ChatGPT 전환 방법**: `.env`의 `CHATGPT_API_URL`을 실제 OpenAI URL로 교체하고 mock 서버 중지.
- **대안 고려**: 메인 앱 안에 mock 로직 포함 → 삭제 시 코드 수정 필요, 기각.

```
[mock 사용 중]                     [실제 ChatGPT 전환]
CHATGPT_API_URL=                   CHATGPT_API_URL=
  http://localhost:8001/            https://api.openai.com/
  service/chatgpt                   v1/chat/completions

mock_server/ 실행 중               mock_server/ 중지 or 삭제
```

### 결정 2: 설정을 pydantic-settings BaseSettings로 관리
```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_port: int = 9000
    chatgpt_api_url: str
    chatgpt_api_key: str
    chatgpt_model: str = "gpt-4"
    chatgpt_timeout: int = 30
    chatgpt_system_prompt: str
    similarity_db_path: str = "similarity.db"
    similarity_threshold: float = 0.8

    class Config:
        env_file = ".env"
```
- **이유**: 타입 검증, `.env` 자동 로딩, 기본값 명시가 한 곳에서 가능
- **대안 고려**: `os.environ.get()` 직접 사용 → 타입 안전성 없음, 기각

### 결정 3: requirements.txt를 서비스별로 분리
- `requirements.txt` (taurus-chatgpt-agent 전용)
- `mock_server/requirements.txt` (mock 서버 전용 — scikit-learn 불필요)
- **이유**: mock 삭제 시 의존성도 함께 제거. 메인 서비스 배포에 mock 의존성 포함 방지.

## Risks / Trade-offs

- [Risk] `.env` 파일 미생성 시 필수 환경 변수 누락으로 앱 시작 실패
  → Mitigation: `.env.example` 제공, `BaseSettings` 미설정 시 명확한 에러 출력
- [Risk] mock_server와 app의 config 구조가 중복됨
  → Mitigation: 두 서비스는 완전 독립 실행 단위이므로 중복 허용. 공유 코드 없음이 목표.

## Migration Plan

신규 프로젝트이므로 마이그레이션 불필요. 구현 후 바로 이후 change 진행.

## Open Questions

- `CHATGPT_SYSTEM_PROMPT` 내용을 구체적으로 무엇으로 정의할지 (restapi-recive-layer change에서 결정)
- mock_server 기본 포트 결정 (구현 시 `.env.example`에 명시)
