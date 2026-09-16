"""
금융 데이터 수집 서비스 (단순화 버전)
- pykrx: 한국 주가지수 (KOSPI, KOSDAQ)
- hardcoded fallback: 해외 지수, 환율 (yfinance 불안정성 대비)
"""

import asyncio
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, Dict
from utils.logger import get_logger

try:
    from pykrx import stock
except ImportError:
    stock = None

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
        """지수 정보 조회 (비동기)"""
        if index_name not in IndexService.MAJOR_INDICES:
            return None

        try:
            ticker = IndexService.MAJOR_INDICES[index_name]
            loop = asyncio.get_event_loop()

            # pykrx 사용: 한국 지수
            if index_name in ["KOSPI", "KOSDAQ"] and stock:
                def fetch_kr():
                    try:
                        end_date = datetime.now().strftime("%Y%m%d")
                        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")

                        if index_name == "KOSPI":
                            return stock.get_index_ohlcv(start_date, end_date, "1001")
                        else:  # KOSDAQ
                            return stock.get_index_ohlcv(start_date, end_date, "2001")
                    except Exception as e:
                        logger.error(f"pykrx error: {str(e)}")
                        return None

                hist = await loop.run_in_executor(None, fetch_kr)

                if hist is None or hist.empty:
                    return {
                        "name": index_name,
                        "ticker": ticker,
                        "price": 0,
                        "change": 0,
                        "change_percent": 0,
                        "timestamp": datetime.now().isoformat(),
                        "note": "데이터를 불러올 수 없습니다"
                    }

                price = hist["종가"].iloc[-1]
                open_price = hist["시가"].iloc[-1]
                change = price - open_price
                change_pct = (change / open_price * 100) if open_price != 0 else 0

                return {
                    "name": index_name,
                    "ticker": ticker,
                    "price": round(float(price), 2),
                    "change": round(float(change), 2),
                    "change_percent": round(float(change_pct), 2),
                    "timestamp": datetime.now().isoformat()
                }

            # yfinance: 해외 지수 (fallback with hardcoded mock data)
            else:
                def fetch():
                    try:
                        data = yf.Ticker(ticker, session=None)
                        hist = data.history(period="5d")
                        return hist
                    except Exception:
                        return None

                hist = await loop.run_in_executor(None, fetch)

                if hist is None or hist.empty:
                    # 해외 지수는 기본값으로 반환 (데이터 소스 문제로 인한 임시 조치)
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
                        "note": "실시간 데이터 불가 (기본값)"
                    }

                price = hist["Close"].iloc[-1]
                open_price = hist["Open"].iloc[-1]
                change = price - open_price
                change_pct = (change / open_price * 100) if open_price != 0 else 0

                return {
                    "name": index_name,
                    "ticker": ticker,
                    "price": round(float(price), 2),
                    "change": round(float(change), 2),
                    "change_percent": round(float(change_pct), 2),
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error fetching index {index_name}: {str(e)}")
            return None

    @staticmethod
    async def get_currency_rate(currency_pair: str) -> Optional[Dict]:
        """환율 정보 조회"""
        if currency_pair not in IndexService.CURRENCIES:
            return None

        try:
            ticker = IndexService.CURRENCIES[currency_pair]
            loop = asyncio.get_event_loop()

            # yfinance 시도 (불안정할 가능성 높음)
            def fetch():
                try:
                    data = yf.Ticker(ticker, session=None)
                    hist = data.history(period="5d")
                    return hist
                except Exception:
                    return None

            hist = await loop.run_in_executor(None, fetch)

            if hist is None or hist.empty:
                # 환율은 기본값으로 반환 (실시간 데이터 불가)
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
                    "note": "실시간 데이터 불가 (기본값)"
                }

            price = hist["Close"].iloc[-1]
            open_price = hist["Open"].iloc[-1]
            change = price - open_price
            change_pct = (change / open_price * 100) if open_price != 0 else 0

            return {
                "pair": currency_pair,
                "rate": round(float(price), 2),
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
    """주식 정보 서비스 (단순화)"""

    @staticmethod
    async def get_stock_info(ticker: str) -> Optional[Dict]:
        """종목 정보 조회"""
        try:
            loop = asyncio.get_event_loop()

            def fetch():
                data = yf.Ticker(ticker)
                hist = data.history(period="1y")
                return hist

            hist = await loop.run_in_executor(None, fetch)

            if hist.empty:
                return None

            current_price = hist["Close"].iloc[-1]
            week_52_high = hist["High"].max()
            week_52_low = hist["Low"].min()

            return {
                "ticker": ticker,
                "price": float(current_price),
                "week_52_high": float(week_52_high),
                "week_52_low": float(week_52_low),
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
