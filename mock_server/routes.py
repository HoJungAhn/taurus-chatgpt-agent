"""
mock-chatgpt-server 라우트 모듈.

POST /service/chatgpt : Bearer token 인증 후 고정된 ChatGPT 분석 결과를 반환한다.
"""

from fastapi import APIRouter, Depends
from mock_server.schemas import ChatRequest, ChatResponse, ChatChoice, ChatResponseMessage
from mock_server.auth import verify_bearer_token
from mock_server.constants import MOCK_ANALYSIS_RESULT

router = APIRouter()


@router.post("/service/chatgpt", response_model=ChatResponse)
async def mock_chatgpt(request: ChatRequest, _: None = Depends(verify_bearer_token)):
    """
    ChatGPT API를 모사하는 엔드포인트.

    Bearer token 인증(verify_bearer_token Dependency)을 통과한 요청에 대해
    MOCK_ANALYSIS_RESULT 상수를 ChatGPT 응답 형식으로 감싸 반환한다.

    인증 실패 시: HTTP 401 (verify_bearer_token에서 처리)
    필수 필드 누락 시: HTTP 422 (Pydantic 자동 처리)
    정상 요청 시: HTTP 200 + ChatResponse

    Args:
        request: OpenAI Chat Completions API 형식의 요청 (model, messages 필드 필수)
        _: Bearer token 검증 결과 (None이면 인증 성공. 값 사용 불필요하므로 _로 명명)
    """
    # 입력 내용과 무관하게 항상 동일한 고정 응답을 반환한다.
    # 실제 ChatGPT와 동일한 choices[0].message.content 구조로 응답한다.
    return ChatResponse(
        choices=[
            ChatChoice(
                message=ChatResponseMessage(
                    role="assistant",
                    content=MOCK_ANALYSIS_RESULT,
                )
            )
        ]
    )
