"""
FastAPI 메인 진입점 (로컬 테스트 버전)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from config.settings import get_settings
from utils.logger import setup_logging, get_logger

# 로깅 초기화
setup_logging()
logger = get_logger(__name__)

# FastAPI 애플리케이션 생성
settings = get_settings()
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI 주식/금융 비서 - 카카오톡 챗봇 백엔드",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
from routers.kakao import router as kakao_router
from routers.telegram import router as telegram_router

app.include_router(kakao_router)
app.include_router(telegram_router)


# ========================================
# 기본 엔드포인트
# ========================================

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": f"🤖 {settings.APP_NAME} 백엔드 서버 실행 중",
        "api_version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {
        "status": "alive",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


# ========================================
# 테스트 엔드포인트
# ========================================

@app.get("/api/test")
async def test_api():
    """테스트 엔드포인트"""
    return {
        "message": "✅ FastAPI 서버가 정상 작동합니다!",
        "environment": {
            "debug": settings.DEBUG,
            "app_name": settings.APP_NAME,
            "gemini_key_set": bool(settings.GOOGLE_API_KEY),
            "kakao_app_id_set": bool(settings.KAKAO_APP_ID),
        }
    }


# ========================================
# 금융 데이터 테스트 엔드포인트
# ========================================

@app.get("/api/indices")
async def get_indices():
    """지수/환율 조회 테스트"""
    try:
        from services.finance import get_all_indices
        data = await get_all_indices()
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        logger.error(f"Error in /api/indices: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/api/news")
async def get_news():
    """뉴스 조회 테스트"""
    try:
        from utils.scraper import fetch_naver_news
        news = await fetch_naver_news(limit=5)
        return {
            "status": "success",
            "data": news
        }
    except Exception as e:
        logger.error(f"Error in /api/news: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


# ========================================
# 애플리케이션 이벤트
# ========================================

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작"""
    logger.info(f"🚀 {settings.APP_NAME} 서버 시작됨")
    logger.info(f"Debug mode: {settings.DEBUG}")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료"""
    logger.info(f"🛑 {settings.APP_NAME} 서버 종료됨")


# ========================================
# 실행 (개발용)
# ========================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
