"""
KRX OpenAPI 기반 금융 데이터 서비스
- KOSPI, KOSDAQ 실시간 지수
"""

import asyncio
import httpx
from datetime import datetime
from typing import Optional, Dict
from utils.logger import get_logger
from config.settings import get_settings

logger = get_logger(__name__)


class KRXIndexService:
    """KRX OpenAPI를 이용한 지수 조회"""

    INDICES = {
        "KOSPI": "kospi",
        "KOSDAQ": "kosdaq",
    }

    @staticmethod
    async def get_index_info(index_name: str) -> Optional[Dict]:
        """KRX API로 지수 정보 조회"""
        if index_name not in KRXIndexService.INDICES:
            return None

        try:
            settings = get_settings()
            api_key = settings.KRX_API_KEY

            if not api_key:
                logger.error("KRX_API_KEY not set")
                return None

            index_code = KRXIndexService.INDICES[index_name]

            # KRX OpenAPI 엔드포인트
            url = f"https://data-dbg.krx.co.kr/svc/apis/idx/{index_code}_dd_trd"

            # 요청 파라미터
            params = {
                "basDd": datetime.now().strftime("%Y%m%d"),
                "apikey": api_key  # 소문자로 시도
            }

            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, params=params)
                data = response.json()

            # 응답 파싱
            if "OutBlock_1" not in data or not data["OutBlock_1"]:
                logger.warning(f"No data for {index_name}")
                return None

            item = data["OutBlock_1"][0]

            current_price = float(item.get("CLSPRC_IDX", 0))
            change = float(item.get("CMPPREVDD_IDX", 0))
            change_pct = float(item.get("FLUC_RT", 0))

            return {
                "name": index_name,
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching KRX index {index_name}: {str(e)}")
            return None

    @staticmethod
    async def get_all_indices() -> Dict[str, Dict]:
        """모든 주요 한국 지수 조회 (병렬)"""
        tasks = [
            KRXIndexService.get_index_info(name)
            for name in KRXIndexService.INDICES.keys()
        ]
        results = await asyncio.gather(*tasks)
        return {r["name"]: r for r in results if r}


async def get_kospi_kosdaq() -> Dict:
    """KOSPI와 KOSDAQ 조회"""
    return await KRXIndexService.get_all_indices()
