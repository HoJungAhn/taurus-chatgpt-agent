## ADDED Requirements

### Requirement: 메인 서비스 디렉토리 구조 초기화
taurus-chatgpt-agent 메인 서비스는 아래 구조로 초기화되어야 한다.
`mock_server/`는 코드 레벨 import 없이 완전 독립 구조여야 하며, 삭제 시 메인 서비스에 영향이 없어야 한다.

```
taurus-chatgpt-agent/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   └── models/
│       └── __init__.py
├── mock_server/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   └── requirements.txt
├── tests/
│   └── __init__.py
├── requirements.txt
├── .env.example
└── .gitignore
```

#### Scenario: 메인 서비스 패키지 구조 확인
- **WHEN** 프로젝트 bootstrap 완료 후
- **THEN** `app/`, `app/api/`, `app/services/`, `app/models/` 디렉토리가 존재해야 한다
- **THEN** 각 디렉토리에 `__init__.py`가 존재해야 한다

#### Scenario: mock_server 독립성 확인
- **WHEN** `mock_server/` 디렉토리를 삭제했을 때
- **THEN** `app/` 패키지 import 및 실행에 오류가 없어야 한다

---

### Requirement: 환경 변수 설정 관리
메인 서비스는 pydantic-settings `BaseSettings`를 통해 환경 변수를 관리해야 한다.
`.env` 파일 또는 OS 환경 변수에서 자동으로 로딩되어야 한다.

필수 환경 변수:
- `CHATGPT_API_URL`: ChatGPT(or mock) 호출 URL
- `CHATGPT_API_KEY`: Bearer token 인증 키
- `CHATGPT_SYSTEM_PROMPT`: ChatGPT system prompt 문자열

기본값 환경 변수:
- `APP_PORT=9000`
- `CHATGPT_MODEL=gpt-4`
- `CHATGPT_TIMEOUT=30`
- `SIMILARITY_DB_PATH=similarity.db`
- `SIMILARITY_THRESHOLD=0.8`

#### Scenario: 필수 환경 변수 미설정 시 오류 발생
- **WHEN** `CHATGPT_API_URL`, `CHATGPT_API_KEY`, `CHATGPT_SYSTEM_PROMPT` 중 하나라도 `.env`에 없을 때
- **THEN** 앱 시작 시 `ValidationError`가 발생하고 누락된 변수명이 출력되어야 한다

#### Scenario: 기본값 환경 변수 미설정 시 기본값 적용
- **WHEN** `APP_PORT`를 별도로 설정하지 않았을 때
- **THEN** 서비스는 포트 `9000`으로 실행되어야 한다

#### Scenario: .env 파일 자동 로딩
- **WHEN** 프로젝트 루트에 `.env` 파일이 존재할 때
- **THEN** 별도 코드 없이 환경 변수가 자동으로 로딩되어야 한다

---

### Requirement: ChatGPT URL 교체만으로 mock/실제 API 전환
메인 서비스는 `CHATGPT_API_URL` 환경 변수 값만 변경하여 mock 서버와 실제 ChatGPT API를 전환할 수 있어야 한다.
메인 서비스 코드 수정이 필요하지 않아야 한다.

#### Scenario: mock 서버로 요청 전송
- **WHEN** `CHATGPT_API_URL=http://localhost:8001/service/chatgpt` 으로 설정되고 mock 서버가 실행 중일 때
- **THEN** 메인 서비스가 해당 URL로 요청을 전송해야 한다

#### Scenario: 실제 ChatGPT API로 전환
- **WHEN** `CHATGPT_API_URL=https://api.openai.com/v1/chat/completions` 으로 변경하고 mock 서버를 중지했을 때
- **THEN** 메인 서비스 코드 수정 없이 실제 ChatGPT API로 요청이 전송되어야 한다

---

### Requirement: .env.example 및 .gitignore 제공
`.env.example`에 모든 환경 변수와 예시 값이 포함되어야 한다.
`.gitignore`에 `.env`, `*.db`, `__pycache__`가 포함되어야 한다.

#### Scenario: .env.example 내용 확인
- **WHEN** 개발자가 프로젝트를 처음 클론했을 때
- **THEN** `.env.example`을 복사하여 `.env`를 생성하면 로컬 실행이 가능해야 한다

#### Scenario: .env가 git에 커밋되지 않음
- **WHEN** `git status`를 실행했을 때
- **THEN** `.env` 파일이 untracked 또는 ignored 상태여야 한다
