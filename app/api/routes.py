"""
taurus-chatgpt-agent API 라우트 모듈.

POST /api/refine : EAI 서비스에서 수신한 error_stack을 정제하여 반환한다.
GET  /dashboard  : similarity DB 저장 현황을 HTML 페이지로 제공한다.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.models.schemas import RefineRequest, RefineResponse
from app.services.chatgpt_service import call_chatgpt, TimeoutError, ChatGPTError

router = APIRouter()


@router.post("/api/refine", response_model=RefineResponse)
async def refine(request: RefineRequest):
    """
    Java error stacktrace를 수신하여 ChatGPT로 정제한 결과를 반환한다.

    처리 순서:
    1. similarity DB에서 동일 interface_id 내 유사한 error_stack 검색
       → 캐시 히트 시: status="cached", is_refined=True, DB 저장 없이 즉시 반환
       → similarity DB 자체 오류 시: 예외를 무시하고 ChatGPT 직접 호출로 fallback
    2. ChatGPT API 호출
       → 성공: DB에 저장 후 status="success", is_refined=True 반환
       → timeout: DB 저장 없이 원본 error_stack 반환, status="timeout", is_refined=False
       → 오류: DB 저장 없이 원본 error_stack 반환, status="chatgpt_error", is_refined=False

    모든 케이스에서 HTTP 200을 반환하며, EAI 서비스는 status 필드로 결과를 판단한다.
    """
    # similarity_service를 지연 임포트(lazy import)하여 순환 참조를 방지한다.
    # app.main이 routes를 임포트하고, routes도 app.main을 참조하는 구조이므로
    # 함수 내부에서 임포트하여 모듈 로드 시점의 순환 참조 문제를 회피한다.
    from app.main import similarity_service

    # Step 1: similarity DB 캐시 조회
    ratio = None
    try:
        cached, ratio = similarity_service.find_similar(request.interface_id, request.error_stack)
        if cached is not None:
            # 유사도 threshold 이상의 기존 결과 발견 → ChatGPT 호출 없이 즉시 반환
            return RefineResponse(
                interface_id=request.interface_id,
                refine_message=cached,
                is_refined=True,
                status="cached",
                ratio=ratio,
            )
    except Exception:
        # similarity DB 오류는 전체 서비스 장애로 이어지지 않도록 무시하고
        # ChatGPT 직접 호출로 fallback 처리한다.
        pass

    # Step 2: ChatGPT API 호출
    try:
        result = await call_chatgpt(request.error_stack)
        # 정제 성공 시에만 DB에 저장한다 (timeout/오류 시에는 저장하지 않음)
        similarity_service.save(request.interface_id, request.error_stack, result)
        return RefineResponse(
            interface_id=request.interface_id,
            refine_message=result,
            is_refined=True,
            status="success",
            ratio=ratio,
        )
    except TimeoutError:
        # ChatGPT 응답 시간 초과: 원본 error_stack을 refine_message로 반환
        return RefineResponse(
            interface_id=request.interface_id,
            refine_message=request.error_stack,
            is_refined=False,
            status="timeout",
            ratio=ratio,
        )
    except ChatGPTError:
        # ChatGPT API 오류: 원본 error_stack을 refine_message로 반환
        return RefineResponse(
            interface_id=request.interface_id,
            refine_message=request.error_stack,
            is_refined=False,
            status="chatgpt_error",
            ratio=ratio,
        )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    similarity DB 저장 현황을 Jinja2 템플릿으로 렌더링하여 HTML 페이지를 반환한다.

    - get_summary(): 전체 건수, 고유 interface_id 수 (상단 통계)
    - get_all_interfaces(): interface_id별 레코드 목록 (펼침/접기 테이블)

    브라우저에서 http://localhost:9000/dashboard 로 접근하면 확인할 수 있다.
    """
    # templates도 지연 임포트로 순환 참조를 방지한다.
    from app.main import similarity_service, templates

    summary = similarity_service.get_summary()
    interfaces = similarity_service.get_all_interfaces()

    # Jinja2 템플릿(dashboard.html)에 데이터를 전달하여 HTML을 생성한다.
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"summary": summary, "interfaces": interfaces},
    )
