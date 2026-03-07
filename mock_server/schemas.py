"""
OpenAI Chat Completions API 호환 Pydantic 스키마 정의.

실제 OpenAI API와 동일한 request/response 구조를 사용하여
taurus-chatgpt-agent가 URL만 교체하면 실제 ChatGPT로 전환 가능하도록 설계한다.

OpenAI API Reference:
  POST https://api.openai.com/v1/chat/completions
"""

from pydantic import BaseModel
from typing import List


class ChatMessage(BaseModel):
    """단일 대화 메시지. role은 "system", "user", "assistant" 중 하나."""

    role: str     # 메시지 발신자 역할 (system / user / assistant)
    content: str  # 메시지 내용


class ChatRequest(BaseModel):
    """POST /service/chatgpt 요청 스키마 (OpenAI Chat Completions API 형식)."""

    model: str                  # 사용할 모델명 (예: "gpt-4")
    messages: List[ChatMessage] # 대화 히스토리. system + user 메시지 포함


class ChatResponseMessage(BaseModel):
    """응답 메시지 내용. assistant가 생성한 텍스트를 담는다."""

    role: str     # 항상 "assistant"
    content: str  # ChatGPT(또는 mock)가 생성한 응답 텍스트


class ChatChoice(BaseModel):
    """응답 후보 항목. OpenAI API는 n 파라미터로 여러 후보를 생성할 수 있으나, mock은 1개만 반환."""

    message: ChatResponseMessage


class ChatResponse(BaseModel):
    """POST /service/chatgpt 응답 스키마 (OpenAI Chat Completions API 형식).

    taurus-chatgpt-agent는 choices[0].message.content 만을 사용한다.
    실제 OpenAI API의 id, created, usage 등 추가 필드는 mock에서 생략한다.
    """

    choices: List[ChatChoice]
