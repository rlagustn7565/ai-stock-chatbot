"""
Gemini API 기반 AI 요약 및 분석 서비스
- 뉴스 기사 요약 및 관련 종목 태깅
- 유튜브 자막 요약 및 투자 인사이트
- 종목 시황 분석
"""

import asyncio
import google.generativeai as genai
from typing import Optional, List, Dict, Tuple
from utils.logger import get_logger
from config.settings import get_settings

logger = get_logger(__name__)


class GeminiService:
    """Google Gemini API 서비스"""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.GOOGLE_API_KEY
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not set")
        else:
            genai.configure(api_key=self.api_key)

        self.model = genai.GenerativeModel("gemini-1.5-pro")

    @staticmethod
    def _create_prompt_news_summary() -> str:
        """뉴스 요약 프롬프트"""
        return """다음 뉴스 기사를 읽고:

1. **핵심 내용**: 3줄 이내로 요약
2. **영향받을 종목**: 해당 기사와 관련된 한국 주식 종목 (최대 3개, "종목명(티커)" 형식)
3. **긍정/부정 영향**: 긍정적(수혜) 또는 부정적(악재) 여부 명시

기사:
{article_text}

응답 형식:
**요약**: [3줄 요약]
**관련종목**: [종목1, 종목2, ...]
**영향**: [긍정/부정]"""

    @staticmethod
    def _create_prompt_youtube_summary() -> str:
        """유튜브 요약 프롬프트"""
        return """다음은 YouTube 영상의 자막입니다. 다음을 분석해주세요:

1. **핵심 내용**: 영상의 주요 내용을 3-4줄로 요약
2. **투자 인사이트**: 주식/금융 투자 관점에서의 시사점
3. **관련 테마**: 언급된 산업/테마 (최대 2-3개)

자막:
{transcript}

응답 형식:
**요약**: [핵심 내용]
**투자인사이트**: [인사이트]
**테마**: [테마1, 테마2, ...]"""

    @staticmethod
    def _create_prompt_stock_analysis() -> str:
        """종목 분석 프롬프트"""
        return """다음 정보를 바탕으로 종목을 분석해주세요:

종목정보:
- 종목명: {stock_name}
- 현재가: {current_price}원
- 52주 최고: {week_52_high}원
- 52주 최저: {week_52_low}원

최근 뉴스:
{recent_news}

분석 내용:
1. **기술적 분석**: 현재 밸류에이션과 기술적 위치
2. **뉴스 영향**: 최근 뉴스가 주는 시사점
3. **투자 관점**: 단기/중기 투자 관점 의견

응답 형식:
**기술분석**: [분석]
**뉴스영향**: [영향]
**투자의견**: [의견]"""

    async def summarize_article(self, article_text: str) -> Tuple[Optional[str], Optional[List[str]], Optional[str]]:
        """뉴스 기사 요약 및 관련 종목 추출"""
        try:
            if not self.api_key:
                return None, None, None

            prompt = self._create_prompt_news_summary().format(article_text=article_text)

            loop = asyncio.get_event_loop()

            def generate():
                response = self.model.generate_content(prompt)
                return response.text

            result = await loop.run_in_executor(None, generate)

            # 응답 파싱
            lines = result.split("\n")
            summary = None
            stocks = None
            impact = None

            for line in lines:
                if "**요약**:" in line:
                    summary = line.replace("**요약**:", "").strip()
                elif "**관련종목**:" in line:
                    stocks_str = line.replace("**관련종목**:", "").strip()
                    stocks = [s.strip() for s in stocks_str.split(",")]
                elif "**영향**:" in line:
                    impact = line.replace("**영향**:", "").strip()

            logger.info("Article summary generated successfully")
            return summary, stocks, impact

        except Exception as e:
            logger.error(f"Error summarizing article: {str(e)}")
            return None, None, None

    async def summarize_youtube(self, transcript: str) -> Tuple[Optional[str], Optional[str], Optional[List[str]]]:
        """유튜브 자막 요약"""
        try:
            if not self.api_key:
                return None, None, None

            # 자막이 너무 길면 앞부분만 사용
            transcript = transcript[:5000]

            prompt = self._create_prompt_youtube_summary().format(transcript=transcript)

            loop = asyncio.get_event_loop()

            def generate():
                response = self.model.generate_content(prompt)
                return response.text

            result = await loop.run_in_executor(None, generate)

            # 응답 파싱
            lines = result.split("\n")
            summary = None
            insight = None
            themes = None

            for line in lines:
                if "**요약**:" in line:
                    summary = line.replace("**요약**:", "").strip()
                elif "**투자인사이트**:" in line:
                    insight = line.replace("**투자인사이트**:", "").strip()
                elif "**테마**:" in line:
                    themes_str = line.replace("**테마**:", "").strip()
                    themes = [t.strip() for t in themes_str.split(",")]

            logger.info("YouTube summary generated successfully")
            return summary, insight, themes

        except Exception as e:
            logger.error(f"Error summarizing YouTube: {str(e)}")
            return None, None, None

    async def analyze_stock(
        self,
        stock_name: str,
        current_price: float,
        week_52_high: float,
        week_52_low: float,
        recent_news: List[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """종목 종합 분석"""
        try:
            if not self.api_key:
                return None, None, None

            news_text = "\n".join([f"- {news}" for news in recent_news[:5]])

            prompt = self._create_prompt_stock_analysis().format(
                stock_name=stock_name,
                current_price=current_price,
                week_52_high=week_52_high,
                week_52_low=week_52_low,
                recent_news=news_text
            )

            loop = asyncio.get_event_loop()

            def generate():
                response = self.model.generate_content(prompt)
                return response.text

            result = await loop.run_in_executor(None, generate)

            # 응답 파싱
            lines = result.split("\n")
            technical = None
            news_impact = None
            opinion = None

            for line in lines:
                if "**기술분석**:" in line:
                    technical = line.replace("**기술분석**:", "").strip()
                elif "**뉴스영향**:" in line:
                    news_impact = line.replace("**뉴스영향**:", "").strip()
                elif "**투자의견**:" in line:
                    opinion = line.replace("**투자의견**:", "").strip()

            logger.info(f"Stock analysis for {stock_name} generated successfully")
            return technical, news_impact, opinion

        except Exception as e:
            logger.error(f"Error analyzing stock: {str(e)}")
            return None, None, None


# 싱글톤 인스턴스
_gemini_service = None


def get_gemini_service() -> GeminiService:
    """Gemini 서비스 싱글톤 인스턴스"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
