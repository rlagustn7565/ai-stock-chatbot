"""
금융 데이터 수집 서비스
- KRX OpenAPI: KOSPI, KOSDAQ 실시간 지수
- 기본값: 해외 지수, 환율
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict
from utils.logger import get_logger
from services.krx_finance import KRXIndexService

logger = get_logger(__name__)


class IndexService:
    """글로벌 지수 및 환율 서비스"""

    MAJOR_INDICES = {
        "KOSPI": "^KS11",
        "KOSDAQ": "^KQ11",
        "S&P500": "^GSPC",
        "NASDAQ": "^IXIC",
    }

    CURRENCIES = {
        "USD/KRW": "USDKRW=X",
        "EUR/KRW": "EURKRW=X",
        "JPY/KRW": "JPYKRW=X",
    }

    @staticmethod
    async def get_index_info(index_name: str) -> Optional[Dict]:
        """지수 정보 조회"""
        if index_name not in IndexService.MAJOR_INDICES:
            return None

        # KOSPI/KOSDAQ은 KRX API 사용
        if index_name in ["KOSPI", "KOSDAQ"]:
            return await KRXIndexService.get_index_info(index_name)

        # 해외 지수는 기본값 반환
        ticker = IndexService.MAJOR_INDICES[index_name]
        fallback_prices = {
            "S&P500": 5900.0,
            "NASDAQ": 18500.0
        }
        base_price = fallback_prices.get(index_name, 100.0)

        return {
            "name": index_name,
            "ticker": ticker,
            "price": base_price,
            "change": 0,
            "change_percent": 0,
            "timestamp": datetime.now().isoformat(),
            "note": "Demo data"
        }

    @staticmethod
    async def get_currency_rate(currency_pair: str) -> Optional[Dict]:
        """환율 정보 조회 (기본값)"""
        if currency_pair not in IndexService.CURRENCIES:
            return None

        fallback_rates = {
            "USD/KRW": 1230.5,
            "EUR/KRW": 1350.0,
            "JPY/KRW": 8.5
        }
        base_rate = fallback_rates.get(currency_pair, 1000.0)

        return {
            "pair": currency_pair,
            "rate": base_rate,
            "change": 0,
            "change_percent": 0,
            "timestamp": datetime.now().isoformat(),
            "note": "Demo data"
        }

    @staticmethod
    async def get_all_major_indices() -> Dict[str, Dict]:
        """모든 주요 지수 조회 (병렬)"""
        tasks = [
            IndexService.get_index_info(name)
            for name in IndexService.MAJOR_INDICES.keys()
        ]
        results = await asyncio.gather(*tasks)
        return {r["name"]: r for r in results if r}


class StockService:
    """주식 정보 서비스"""

    @staticmethod
    async def get_stock_info(ticker: str) -> Optional[Dict]:
        """종목 정보 조회 (기본값)"""
        return {
            "ticker": ticker,
            "price": 0.0,
            "week_52_high": 0.0,
            "week_52_low": 0.0,
            "timestamp": datetime.now().isoformat()
        }


# ========================================
# 편의 함수
# ========================================

async def get_all_indices() -> Dict:
    """모든 주요 지수 조회"""
    indices = await IndexService.get_all_major_indices()
    currencies = {}

    for currency_pair in IndexService.CURRENCIES.keys():
        rate = await IndexService.get_currency_rate(currency_pair)
        if rate:
            currencies[currency_pair] = rate

    return {
        "indices": indices,
        "currencies": currencies
    }


async def get_stock_profile(ticker_or_name: str) -> Optional[Dict]:
    """종목 정보 조회"""
    return await StockService.get_stock_info(ticker_or_name)
