"""
POST /api/refine 엔드포인트의 Request/Response Pydantic 모델 정의.

Pydantic BaseModel을 사용하여 JSON 직렬화/역직렬화 및 유효성 검증을 자동 처리한다.
필수 필드가 누락된 요청은 FastAPI가 자동으로 HTTP 422를 반환한다.
"""

from pydantic import BaseModel
from typing import Literal, Optional


class RefineRequest(BaseModel):
    """POST /api/refine 요청 스키마."""

    interface_id: str   # EAI 인터페이스 식별자 (similarity 검색 범위를 구분하는 키)
    error_stack: str    # Java error stacktrace 원문


class RefineResponse(BaseModel):
    """POST /api/refine 응답 스키마.

    status 필드로 처리 경로를 구분하며, 모든 케이스에서 HTTP 200을 반환한다.
    EAI 서비스는 status 값으로 성공/실패/캐시 여부를 판단한다.
    """

    interface_id: str    # 요청의 interface_id를 그대로 반환 (응답 추적용)
    refine_message: str  # 정제된 분석 결과 또는 원본 error_stack (오류 시)
    is_refined: bool     # ChatGPT 정제 성공 여부 (cached 포함 시 True)

    # 처리 경로를 나타내는 status:
    # - "success"      : ChatGPT 정제 성공, DB에 저장 완료
    # - "cached"       : similarity DB에서 캐시 히트, ChatGPT 호출 생략
    # - "timeout"      : ChatGPT API timeout 초과, 원본 error_stack 반환
    # - "chatgpt_error": ChatGPT API 오류 발생, 원본 error_stack 반환
    status: Literal["success", "cached", "timeout", "chatgpt_error"]
    ratio: Optional[float] = None  # find_similar() 계산된 max_similarity (stored=0이면 null)
