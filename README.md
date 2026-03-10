# taurus-chatgpt-agent

EAI 서비스에서 발생한 Java error stacktrace를 ChatGPT API로 정제하여 반환하는 중간 처리 서비스.

## 아키텍처

```
EAI 서비스
    │
    │ POST /api/refine
    ▼
taurus-chatgpt-agent (port 9000)
    │
    ├── similarity-db 조회 (SQLite + TF-IDF)
    │       └── 유사 결과 있음 → status="cached" 즉시 반환
    │
    └── ChatGPT API 호출 (httpx async)
            ├── 성공    → DB 저장 → status="success"
            ├── timeout → DB 저장 없음 → status="timeout"
            └── 오류    → DB 저장 없음 → status="chatgpt_error"
```

로컬 테스트 시 실제 ChatGPT 대신 **mock-chatgpt-server**를 사용할 수 있습니다.

```
taurus-chatgpt-agent (port 9000)
    └── mock-chatgpt-server (port 8001)
```

---

## 사전 준비

- Python 3.9 이상

---

## 설치

**1. 가상 환경 생성 및 활성화**

```bash
python3 -m venv agent
source agent/bin/activate        # macOS / Linux
# agent\Scripts\activate         # Windows
```

**2. 의존성 설치**

```bash
pip install -r requirements.txt
```

---

## 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다.

### Mock 서버 연동 (로컬 테스트용)

```dotenv
# taurus-chatgpt-agent
APP_PORT=9000
CHATGPT_API_URL=http://localhost:8001/service/chatgpt
CHATGPT_API_KEY=abcdefghijk
CHATGPT_MODEL=gpt-4
CHATGPT_TIMEOUT=30
CHATGPT_SYSTEM_PROMPT=당신은 Java 오류 분석 전문가입니다. 입력된 error stacktrace를 분석하여 원인과 해결 방법을 한글로 설명해주세요.
SIMILARITY_DB_PATH=similarity.db
SIMILARITY_THRESHOLD=0.8
SIMILARITY_MAX_RECORDS=5

# mock-chatgpt-server
MOCK_PORT=8001
MOCK_BEARER_TOKEN=abcdefghijk
```

### 실제 ChatGPT 연동

```dotenv
CHATGPT_API_URL=https://api.openai.com/v1/chat/completions
CHATGPT_API_KEY=sk-...
```

---

## 실행 방법

> 실행 전 **프로젝트 루트**에서 가상 환경을 활성화합니다: `source agent/bin/activate`

| 대상 | 명령 | 포트 |
|------|------|------|
| **mock_server** | `python -m mock_server.main` | 8001 |
| **app** | `python -m app.main` | 9000 |

### 1단계: Mock ChatGPT 서버 시작 (터미널 1)

```bash
python -m mock_server.main
```

```
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### 2단계: 메인 서비스 시작 (터미널 2)

```bash
python -m app.main
```

```
INFO:     Uvicorn running on http://0.0.0.0:9000
```

### 서비스 종료

```bash
kill $(lsof -ti:8001) $(lsof -ti:9000)
```

---

## 테스트 방법

### curl로 API 호출

**기본 요청:**

```bash
curl -X POST http://localhost:9000/api/refine \
  -H "Content-Type: application/json" \
  -d '{
    "interface_id": "IF-001",
    "error_stack": "java.lang.NullPointerException\n\tat com.example.Service.process(Service.java:42)\n\tat com.example.Main.main(Main.java:10)"
  }'
```

**예상 응답 (최초 호출 — ChatGPT 정제 성공):**

```json
{
  "interface_id": "IF-001",
  "refine_message": "오류 분석: NullPointerException이 Service.java 42번 라인에서 발생했습니다...",
  "is_refined": true,
  "status": "success"
}
```

**예상 응답 (동일/유사 요청 재호출 — 캐시 히트):**

```json
{
  "interface_id": "IF-001",
  "refine_message": "오류 분석: NullPointerException이 Service.java 42번 라인에서 발생했습니다...",
  "is_refined": true,
  "status": "cached"
}
```

---

### status별 시나리오 테스트

| 시나리오 | status | is_refined | 방법 |
|---|---|---|---|
| 최초 요청, ChatGPT 성공 | `success` | `true` | 기본 요청 |
| 동일/유사 요청 재전송 | `cached` | `true` | 동일 요청 두 번 전송 |
| ChatGPT 응답 지연 | `timeout` | `false` | `CHATGPT_TIMEOUT=1` 설정 후 실제 API 호출 |
| ChatGPT URL 오류 | `chatgpt_error` | `false` | `CHATGPT_API_URL`을 잘못된 주소로 설정 |

**캐시 동작 확인 (2회 연속 전송):**

```bash
# 1회: status="success"
curl -X POST http://localhost:9000/api/refine \
  -H "Content-Type: application/json" \
  -d '{"interface_id": "IF-001", "error_stack": "java.lang.NullPointerException at com.example.Service.process(Service.java:42)"}'

# 2회: status="cached" (유사도 0.8 이상이면 DB에서 반환)
curl -X POST http://localhost:9000/api/refine \
  -H "Content-Type: application/json" \
  -d '{"interface_id": "IF-001", "error_stack": "java.lang.NullPointerException at com.example.Service.process(Service.java:42)"}'
```

**필수 필드 누락 (422 확인):**

```bash
curl -X POST http://localhost:9000/api/refine \
  -H "Content-Type: application/json" \
  -d '{"interface_id": "IF-001"}'
```

---

### Mock 서버 단독 테스트

```bash
curl -X POST http://localhost:8001/service/chatgpt \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer abcdefghijk" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "system", "content": "You are a Java error analyst."},
      {"role": "user", "content": "java.lang.NullPointerException at com.example.Service.process(Service.java:42)"}
    ]
  }'
```

**Bearer token 누락 시 (401 확인):**

```bash
curl -X POST http://localhost:8001/service/chatgpt \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "messages": []}'
```

---

### 대시보드 확인

서비스 기동 후 브라우저에서 접속합니다.

```
http://localhost:9000/dashboard
```

similarity DB에 저장된 데이터를 interface_id별로 조회할 수 있습니다. 항목 클릭 시 상세 레코드가 펼쳐집니다.

---

### pytest 실행

> **프로젝트 루트**에서 가상 환경 활성화 후 실행: `source agent/bin/activate`

| 대상 | 명령 |
|------|------|
| **app** 테스트만 | `python -m pytest tests/ -v` |
| **mock_server** 테스트만 | `python -m pytest mock_server/tests/ -v` |
| **전체** (app + mock_server) | `python -m pytest tests/ mock_server/tests/ -v` |

---

## Response 스키마

### POST /api/refine

**Request:**

```json
{
  "interface_id": "IF-001",
  "error_stack": "java.lang.NullPointerException..."
}
```

**Response:**

```json
{
  "interface_id": "IF-001",
  "refine_message": "정제된 오류 분석 내용 또는 원본 error_stack",
  "is_refined": true,
  "status": "success"
}
```

| status | 설명 | is_refined |
|---|---|---|
| `success` | ChatGPT 정제 성공, DB 저장 완료 | `true` |
| `cached` | similarity-db 캐시 히트 | `true` |
| `timeout` | ChatGPT 응답 시간 초과 | `false` |
| `chatgpt_error` | ChatGPT API 오류 | `false` |

> `timeout` / `chatgpt_error` 시 `refine_message`에는 원본 `error_stack`이 그대로 반환됩니다.

---

## 환경 변수 목록

### taurus-chatgpt-agent

| 변수명 | 필수 | 기본값 | 설명 |
|---|---|---|---|
| `APP_PORT` | | `9000` | 서비스 포트 |
| `CHATGPT_API_URL` | 필수 | — | ChatGPT API endpoint |
| `CHATGPT_API_KEY` | 필수 | — | Bearer 인증 키 |
| `CHATGPT_SYSTEM_PROMPT` | 필수 | — | ChatGPT system 프롬프트 |
| `CHATGPT_MODEL` | | `gpt-4` | 사용할 모델명 |
| `CHATGPT_TIMEOUT` | | `30` | API 호출 timeout (초) |
| `SIMILARITY_DB_PATH` | | `similarity.db` | SQLite DB 파일 경로 |
| `SIMILARITY_THRESHOLD` | | `0.8` | 유사도 판단 임계값 (0~1) |
| `SIMILARITY_MAX_RECORDS` | | `5` | interface_id당 최대 저장 건수 (LRU) |

### mock-chatgpt-server

| 변수명 | 기본값 | 설명 |
|---|---|---|
| `MOCK_PORT` | `8001` | Mock 서버 포트 |
| `MOCK_BEARER_TOKEN` | `abcdefghijk` | 허용할 Bearer 토큰 |
