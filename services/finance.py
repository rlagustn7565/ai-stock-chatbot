"""
금융 데이터 수집 서비스 (Finnhub API 기반)
- Finnhub: 지수, 환율, 글로벌 주식
"""

import asyncio
import httpx
from datetime import datetime
from typing import Optional, Dict
from utils.logger import get_logger
from config.settings import get_settings

logger = get_logger(__name__)


class IndexService:
    """글로벌 지수 및 환율 서비스"""

    MAJOR_INDICES = {
        "KOSPI": "^KS11",      # 한국 종합주가지수
        "KOSDAQ": "^KQ11",     # 한국 코스닥
        "S&P500": "^GSPC",     # 미국 S&P 500
        "NASDAQ": "^IXIC",     # 미국 나스닥
    }

    CURRENCIES = {
        "USD/KRW": "USDKRW=X",  # 원달러 환율
        "EUR/KRW": "EURKRW=X",  # 유로원 환율
        "JPY/KRW": "JPYKRW=X",  # 엔원 환율
    }

    @staticmethod
    async def get_index_info(index_name: str) -> Optional[Dict]:
        """Finnhub API로 지수 정보 조회"""
        if index_name not in IndexService.MAJOR_INDICES:
            return None

        try:
            settings = get_settings()
            api_key = settings.FINNHUB_API_KEY

            if not api_key:
                logger.error("FINNHUB_API_KEY not set")
                return None

            ticker = IndexService.MAJOR_INDICES[index_name]

            async with httpx.AsyncClient(timeout=8.0) as client:
                url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={api_key}"
                response = await client.get(url)
                data = response.json()

            if not data or data.get("error"):
                logger.warning(f"Finnhub error for {ticker}: {data}")
                return None

            current_price = data.get("c", 0)
            prev_close = data.get("pc", 0)
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            return {
                "name": index_name,
                "ticker": ticker,
                "price": round(float(current_price), 2),
                "change": round(float(change), 2),
                "change_percent": round(float(change_pct), 2),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching index {index_name}: {str(e)}")
            return None

    @staticmethod
    async def get_currency_rate(currency_pair: str) -> Optional[Dict]:
        """Finnhub API로 환율 조회"""
        if currency_pair not in IndexService.CURRENCIES:
            return None

        try:
            settings = get_settings()
            api_key = settings.FINNHUB_API_KEY

            if not api_key:
                logger.error("FINNHUB_API_KEY not set")
                return None

            ticker = IndexService.CURRENCIES[currency_pair]

            async with httpx.AsyncClient(timeout=8.0) as client:
                url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={api_key}"
                response = await client.get(url)
                data = response.json()

            if not data or data.get("error"):
                logger.warning(f"Finnhub error for {ticker}: {data}")
                return None

            current_rate = data.get("c", 0)
            prev_close = data.get("pc", 0)
            change = current_rate - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            return {
                "pair": currency_pair,
                "rate": round(float(current_rate), 2),
                "change": round(float(change), 2),
                "change_percent": round(float(change_pct), 2),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching currency {currency_pair}: {str(e)}")
            return None

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
        """종목 정보 조회"""
        try:
            settings = get_settings()
            api_key = settings.FINNHUB_API_KEY

            if not api_key:
                return None

            async with httpx.AsyncClient(timeout=8.0) as client:
                url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={api_key}"
                response = await client.get(url)
                data = response.json()

            if not data or data.get("error"):
                return None

            current_price = data.get("c", 0)
            high_52w = data.get("h52", 0)
            low_52w = data.get("l52", 0)

            return {
                "ticker": ticker,
                "price": float(current_price),
                "week_52_high": float(high_52w),
                "week_52_low": float(low_52w),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching stock info for {ticker}: {str(e)}")
            return None


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
