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

try:
    import feedparser
except ImportError:
    feedparser = None

logger = get_logger(__name__)


class FinanceNewsScraper:
    """RSS 피드를 통한 금융 뉴스 스크래핑"""

    RSS_FEEDS = [
        "https://feeds.hankyung.com/hankyung/business.xml",  # 한국경제
        "https://rss.mt.co.kr/mtlist.xml",  # 매일경제
        "https://feeds.daum.net/financial/rss.xml",  # 다음 금융
        "https://www.yonhapnewstv.co.kr/browse/feed/",  # 연합뉴스
    ]

    @staticmethod
    async def get_finance_news(limit: int = 5) -> List[Dict[str, str]]:
        """금융 뉴스 헤드라인 (비동기)"""
        try:
            if not feedparser:
                logger.error("feedparser not installed")
                return []

            loop = asyncio.get_event_loop()

            def fetch_news():
                try:
                    all_articles = []

                    for feed_url in FinanceNewsScraper.RSS_FEEDS:
                        try:
                            feed = feedparser.parse(feed_url)

                            for entry in feed.entries[:limit]:
                                all_articles.append({
                                    "title": entry.get("title", ""),
                                    "url": entry.get("link", ""),
                                    "source": feed.feed.get("title", "Finance News")
                                })
                        except Exception as e:
                            logger.warning(f"Error parsing feed {feed_url}: {str(e)}")
                            continue

                    return all_articles[:limit]
                except Exception as e:
                    logger.error(f"RSS feed fetch error: {str(e)}")
                    return []

            news_list = await loop.run_in_executor(None, fetch_news)
            logger.info(f"Fetched {len(news_list)} news articles from RSS feeds")
            return news_list

        except Exception as e:
            logger.error(f"Error fetching finance news: {str(e)}")
            return []


class ArticleScraper:
    """기사 본문 텍스트 추출"""

    @staticmethod
    async def extract_article_text(url: str, timeout: float = 8.0) -> Optional[str]:
        """기사 URL에서 본문 텍스트 추출"""
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, verify=False) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                        "Referer": "https://www.naver.com/",
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
    """금융 뉴스 요약 함수 (RSS 피드)"""
    return await FinanceNewsScraper.get_finance_news(limit)


async def extract_article_summary(url: str) -> Optional[str]:
    """기사 텍스트 추출 함수"""
    return await ArticleScraper.extract_article_text(url)


async def get_youtube_transcript(url: str) -> Optional[str]:
    """유튜브 자막 추출 함수"""
    return await YouTubeTranscriptScraper.get_transcript(url)
