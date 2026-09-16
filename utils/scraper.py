"""
웹 스크래핑 유틸리티
- Naver 뉴스 헤드라인
- YouTube 자막 추출
- 기사 텍스트 추출
"""

import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from typing import Optional, List, Dict
from utils.logger import get_logger

try:
    import httpx
except ImportError:
    import requests as httpx

try:
    from trafilatura import extract
except ImportError:
    extract = None

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

logger = get_logger(__name__)


class NaverNewsScraper:
    """네이버 뉴스 스크래핑"""

    @staticmethod
    async def get_finance_news(limit: int = 5) -> List[Dict[str, str]]:
        """네이버 경제/금융 뉴스 헤드라인 (비동기)"""
        try:
            url = "https://finance.naver.com/news/"
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()

            soup = BeautifulSoup(response.content, "lxml")
            news_list = []

            # .type5 클래스의 dd 태그에서 뉴스 추출
            items = soup.find_all("dd", class_="")[:limit]

            for item in items:
                link_elem = item.find("a")
                if link_elem:
                    title = link_elem.get_text(strip=True)
                    href = link_elem.get("href", "")

                    if href.startswith("/"):
                        href = "https://finance.naver.com" + href

                    if title and href:
                        news_list.append({
                            "title": title,
                            "url": href,
                            "source": "Naver Finance"
                        })

            logger.info(f"Fetched {len(news_list)} news articles")
            return news_list

        except Exception as e:
            logger.error(f"Error fetching Naver news: {str(e)}")
            return []


class ArticleScraper:
    """기사 본문 텍스트 추출"""

    @staticmethod
    async def extract_article_text(url: str, timeout: float = 8.0) -> Optional[str]:
        """기사 URL에서 본문 텍스트 추출"""
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                )
                response.raise_for_status()

            # trafilatura로 기사 텍스트 추출
            text = extract(response.content, output_format="txt")

            if text:
                logger.info(f"Successfully extracted article from {url}")
                return text[:2000]  # 처음 2000자만 반환
            else:
                logger.warning(f"No article text extracted from {url}")
                return None

        except Exception as e:
            logger.error(f"Error extracting article from {url}: {str(e)}")
            return None


class YouTubeTranscriptScraper:
    """YouTube 자막 추출"""

    @staticmethod
    def get_video_id(url: str) -> Optional[str]:
        """YouTube URL에서 비디오 ID 추출"""
        try:
            # youtube.com/watch?v=ID
            parsed = urlparse(url)
            if parsed.netloc in ["www.youtube.com", "youtube.com"]:
                return parse_qs(parsed.query).get("v", [None])[0]

            # youtu.be/ID (단축 URL)
            elif parsed.netloc in ["youtu.be", "www.youtu.be"]:
                return parsed.path.lstrip("/")

            # youtube.com/shorts/ID
            elif "/shorts/" in url:
                return url.split("/shorts/")[1].split("?")[0]

        except Exception as e:
            logger.error(f"Error extracting video ID from {url}: {str(e)}")

        return None

    @staticmethod
    async def get_transcript(url: str) -> Optional[str]:
        """YouTube 영상 자막 추출 (비동기 래퍼)"""
        video_id = YouTubeTranscriptScraper.get_video_id(url)

        if not video_id:
            logger.error(f"Invalid YouTube URL: {url}")
            return None

        try:
            # 자막 추출 (동기 작업을 async로 래핑)
            loop = asyncio.get_event_loop()
            transcript_list = await loop.run_in_executor(
                None,
                YouTubeTranscriptApi.get_transcript,
                video_id,
                ["ko", "en"]  # 한글 우선, 영문 대체
            )

            # 자막 텍스트로 결합
            transcript_text = " ".join([item["text"] for item in transcript_list])

            logger.info(f"Extracted transcript from YouTube video: {video_id}")
            return transcript_text

        except Exception as e:
            logger.error(f"Error extracting YouTube transcript from {url}: {str(e)}")
            return None


# ========================================
# 편의 함수
# ========================================

async def fetch_naver_news(limit: int = 5) -> List[Dict[str, str]]:
    """네이버 뉴스 요약 함수"""
    return await NaverNewsScraper.get_finance_news(limit)


async def extract_article_summary(url: str) -> Optional[str]:
    """기사 텍스트 추출 함수"""
    return await ArticleScraper.extract_article_text(url)


async def get_youtube_transcript(url: str) -> Optional[str]:
    """유튜브 자막 추출 함수"""
    return await YouTubeTranscriptScraper.get_transcript(url)
