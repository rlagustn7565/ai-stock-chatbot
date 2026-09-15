"""
로깅 설정 (단순화 버전)
"""

import logging
from config.settings import get_settings


def setup_logging():
    """애플리케이션 로깅 초기화"""
    settings = get_settings()

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # 콘솔 핸들러
    if not root_logger.handlers:
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거 인스턴스 반환"""
    return logging.getLogger(name)
