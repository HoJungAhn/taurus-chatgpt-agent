"""
taurus-chatgpt-agent 메인 애플리케이션 모듈.

FastAPI 앱을 초기화하고, similarity DB 연결 생명주기(lifespan)를 관리하며,
라우터와 Jinja2 템플릿을 등록한다.
"""

import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.services.similarity_service import TFIDFSimilarityService

# dashboard HTML 렌더링에 사용할 Jinja2 템플릿 디렉토리 설정.
# __file__ 기준 상대 경로로 지정하여 실행 위치에 무관하게 동작한다.
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# 앱 전역에서 공유하는 similarity service 인스턴스 (싱글톤).
# DB 경로와 유사도 threshold 값을 환경 변수에서 읽어 초기화한다.
similarity_service = TFIDFSimilarityService(
    db_path=settings.similarity_db_path,
    threshold=settings.similarity_threshold,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan 이벤트 핸들러.

    앱 시작 시 SQLite DB를 초기화(테이블/인덱스 생성)하고,
    앱 종료 시 DB 연결을 안전하게 닫는다.
    yield 전후로 startup/shutdown 로직을 분리하는 FastAPI 권장 패턴.
    """
    similarity_service.init_db()
    yield
    similarity_service.close_db()


# FastAPI 앱 인스턴스 생성. lifespan으로 DB 연결 생명주기를 관리한다.
app = FastAPI(title="taurus-chatgpt-agent", lifespan=lifespan)

# 순환 참조 방지를 위해 라우터를 앱 생성 이후에 import하여 등록한다.
# (routes.py 내부에서 app.main의 similarity_service를 참조하기 때문)
from app.api.routes import router
app.include_router(router)


if __name__ == "__main__":
    # python -m app.main 으로 직접 실행할 때의 진입점.
    # reload=False: 운영 환경에서는 자동 reload를 비활성화한다.
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.app_port, reload=False)
