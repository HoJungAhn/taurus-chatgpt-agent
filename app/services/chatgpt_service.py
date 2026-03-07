"""
ChatGPT API 호출 서비스 모듈.

httpx.AsyncClient를 사용하여 비동기로 ChatGPT API에 요청을 보내고 결과를 반환한다.
동기 requests 라이브러리 대신 httpx를 사용하는 이유:
FastAPI의 async 이벤트 루프를 블로킹하지 않기 위해 비동기 HTTP 클라이언트가 필요하다.

오류를 두 가지 예외로 분류하여 라우트에서 status 필드를 정확히 구분할 수 있도록 한다:
- TimeoutError  : ChatGPT API가 설정된 timeout 내에 응답하지 않은 경우
- ChatGPTError  : 그 외 네트워크 오류, 비정상 HTTP 응답 등
"""

import httpx
from app.config import settings


class TimeoutError(Exception):
    """ChatGPT API 응답이 timeout (CHATGPT_TIMEOUT 초) 내에 오지 않은 경우."""
    pass


class ChatGPTError(Exception):
    """ChatGPT API 호출 중 timeout 외의 오류가 발생한 경우 (네트워크 오류, 4xx/5xx 등)."""
    pass


async def call_chatgpt(error_stack: str) -> str:
    """
    ChatGPT API에 error_stack을 전송하고 정제된 분석 결과를 반환한다.

    OpenAI Chat Completions API 형식을 사용하므로, mock 서버와 실제 ChatGPT 모두
    동일한 코드로 호출할 수 있다. CHATGPT_API_URL 환경 변수만 변경하면 전환된다.

    Request 구조:
        {
            "model": "<CHATGPT_MODEL>",
            "messages": [
                {"role": "system", "content": "<CHATGPT_SYSTEM_PROMPT>"},
                {"role": "user",   "content": "<error_stack>"}
            ]
        }

    Response에서 choices[0].message.content 필드를 추출하여 반환한다.

    Args:
        error_stack: ChatGPT에게 분석을 요청할 Java error stacktrace 문자열

    Returns:
        ChatGPT가 생성한 오류 분석 결과 문자열

    Raises:
        TimeoutError: httpx.TimeoutException 발생 시
        ChatGPTError: 그 외 모든 예외 발생 시
    """
    try:
        # AsyncClient는 with 블록 종료 시 자동으로 연결을 닫는다.
        # timeout은 연결부터 응답 완료까지의 전체 시간에 적용된다.
        async with httpx.AsyncClient(timeout=settings.chatgpt_timeout) as client:
            response = await client.post(
                settings.chatgpt_api_url,
                headers={"Authorization": f"Bearer {settings.chatgpt_api_key}"},
                json={
                    "model": settings.chatgpt_model,
                    "messages": [
                        {"role": "system", "content": settings.chatgpt_system_prompt},
                        {"role": "user", "content": error_stack},
                    ],
                },
            )
            # 4xx/5xx 응답 시 httpx.HTTPStatusError를 발생시킨다.
            response.raise_for_status()
            # OpenAI API 및 mock 서버 모두 동일한 경로에 결과를 반환한다.
            return response.json()["choices"][0]["message"]["content"]

    except httpx.TimeoutException:
        # API 응답 지연 → status="timeout", DB 저장 없이 원본 반환
        raise TimeoutError()
    except Exception:
        # 그 외 모든 오류 → status="chatgpt_error", DB 저장 없이 원본 반환
        raise ChatGPTError()
