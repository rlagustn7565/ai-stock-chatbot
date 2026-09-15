"""
Pydantic v2 기반 환경변수 관리
- 타입 안전성 보장
- IDE 자동완성 지원
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """프로젝트 전역 설정"""

    # 서버 설정
    APP_NAME: str = "AI 주식/금융 비서"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # LLM (Gemini API)
    GOOGLE_API_KEY: str = ""

    # 카카오 챗봇 설정
    KAKAO_APP_ID: str = ""
    KAKAO_APP_SECRET: str = ""
    KAKAO_CALLBACK_URL: str = ""  # 콜백 URL (e.g., https://yourapp.com/v1/callback)

    # 타임아웃 설정 (밀리초)
    HTTP_TIMEOUT: int = 8000
    FINANCE_TIMEOUT: int = 5000
    SUMMARY_TIMEOUT: int = 10000

    # 로깅
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """싱글톤 패턴으로 설정 객체 반환"""
    return Settings()
