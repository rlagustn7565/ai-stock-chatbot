"""
카카오 i 오픈빌더 블록 라우터
- 즉시응답 (SkillResponse) < 2초
- 비동기 콜백 (BackgroundTasks) 5~10초
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from schemas.kakao_models import (
    SkillRequest, SkillResponse, SkillTemplate, KakaoMessage, CallbackResponse
)
from services.finance import get_all_indices, get_stock_profile
from services.ai_summary import get_gemini_service
from utils.scraper import (
    fetch_naver_news, extract_article_summary, get_youtube_transcript
)
from utils.logger import get_logger
import asyncio
import requests
from config.settings import get_settings

logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["kakao"])


def create_skill_response(text: str) -> SkillResponse:
    """단순 텍스트 응답 생성"""
    return SkillResponse(
        version="2.0",
        template=SkillTemplate(
            outputs=[{"simpleText": {"text": text}}]
        )
    )


async def send_callback(callback_text: str):
    """카카오 콜백 URL로 메시지 전송 (비동기)"""
    try:
        settings = get_settings()
        if not settings.KAKAO_CALLBACK_URL:
            logger.error("KAKAO_CALLBACK_URL not configured")
            return

        payload = {
            "kakaoMessage": {
                "text": callback_text,
                "typing": True
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.KAKAO_CALLBACK_URL,
                json=payload
            )
            response.raise_for_status()
            logger.info("Callback sent successfully")

    except Exception as e:
        logger.error(f"Error sending callback: {str(e)}")


# ========================================
# BLOCK 1: 지수/환율 조회 (즉시응답)
# ========================================

@router.post("/blocks/indices")
async def get_indices_block(request: SkillRequest) -> SkillResponse:
    """
    블록: 주요 지수 & 환율 조회
    응답 시간: ~ 2초 (즉시응답)
    """
    try:
        indices_data = await get_all_indices()

        # 응답 텍스트 구성
        text_lines = ["📊 **주요 지수 & 환율**\n"]

        for idx_name, idx_info in indices_data["indices"].items():
            symbol = "📈" if idx_info["change"] > 0 else "📉"
            text_lines.append(
                f"{symbol} {idx_name}: {idx_info['price']:,.0f} "
                f"({idx_info['change_percent']:+.2f}%)"
            )

        text_lines.append("")

        for curr_pair, curr_info in indices_data["currencies"].items():
            symbol = "📈" if curr_info["change"] > 0 else "📉"
            text_lines.append(
                f"{symbol} {curr_pair}: {curr_info['rate']:,.2f} "
                f"({curr_info['change_percent']:+.2f}%)"
            )

        response_text = "\n".join(text_lines)
        return create_skill_response(response_text)

    except Exception as e:
        logger.error(f"Error in indices block: {str(e)}")
        return create_skill_response("⚠️ 지수 조회 중 오류가 발생했습니다.")


# ========================================
# BLOCK 2: 금융 뉴스 조회 (즉시응답)
# ========================================

@router.post("/blocks/news")
async def get_news_block(request: SkillRequest) -> SkillResponse:
    """
    블록: 네이버 금융 뉴스 헤드라인
    응답 시간: ~ 1~2초 (즉시응답)
    """
    try:
        news_list = await fetch_naver_news(limit=5)

        if not news_list:
            return create_skill_response("⚠️ 뉴스를 불러올 수 없습니다.")

        text_lines = ["📰 **금융 뉴스 헤드라인**\n"]
        for i, news in enumerate(news_list, 1):
            text_lines.append(f"{i}. {news['title']}\n   🔗 {news['url']}")

        response_text = "\n".join(text_lines)
        return create_skill_response(response_text)

    except Exception as e:
        logger.error(f"Error in news block: {str(e)}")
        return create_skill_response("⚠️ 뉴스 조회 중 오류가 발생했습니다.")


# ========================================
# BLOCK 3: 기사 요약 (비동기 콜백) - 타임아웃 대응
# ========================================

@router.post("/blocks/summarize-article")
async def summarize_article_block(
    request: SkillRequest,
    background_tasks: BackgroundTasks
) -> SkillResponse:
    """
    블록: 뉴스 기사 URL 입력 → 요약 및 종목 태깅
    응답 시간: 5~10초 (비동기 콜백 처리)

    카카오로 즉시 빈 응답을 보내고, 백그라운드에서 요약 후 콜백 URL로 전송
    """
    try:
        # 사용자 입력 추출 (카카오 형식)
        article_url = None
        if request.utterance:
            article_url = request.utterance.strip()

        if not article_url:
            return create_skill_response("📄 기사 URL을 입력해주세요.")

        # 즉시 응답 (카카오 타임아웃 방지)
        response = create_skill_response("요약 중입니다... 잠깐만 기다려주세요. ⏳")

        # 백그라운드 작업: 기사 추출 → 요약 → 콜백
        async def process_article():
            try:
                # 1. 기사 텍스트 추출
                article_text = await extract_article_summary(article_url)
                if not article_text:
                    await send_callback("기사를 추출할 수 없습니다. URL을 확인해주세요.")
                    return

                # 2. Gemini로 요약
                gemini = get_gemini_service()
                summary, stocks, impact = await gemini.summarize_article(article_text)

                if not summary:
                    await send_callback("요약 생성에 실패했습니다.")
                    return

                # 3. 콜백 메시지 구성
                callback_msg = f"""
📰 **기사 요약**

{summary}

📊 **영향받을 종목**
{', '.join(stocks) if stocks else '해당 종목 없음'}

⬆️/⬇️ **영향**: {impact if impact else '중립'}
"""

                # 4. 카카오로 콜백 전송
                await send_callback(callback_msg)

            except Exception as e:
                logger.error(f"Error processing article: {str(e)}")
                await send_callback(f"처리 중 오류 발생: {str(e)}")

        # 백그라운드 작업 등록
        background_tasks.add_task(process_article)

        return response

    except Exception as e:
        logger.error(f"Error in summarize-article block: {str(e)}")
        return create_skill_response("⚠️ 오류가 발생했습니다.")


# ========================================
# BLOCK 4: 유튜브 요약 (비동기 콜백)
# ========================================

@router.post("/blocks/summarize-youtube")
async def summarize_youtube_block(
    request: SkillRequest,
    background_tasks: BackgroundTasks
) -> SkillResponse:
    """
    블록: 유튜브 URL 입력 → 자막 추출 → 요약
    응답 시간: 8~15초 (비동기 콜백 처리)
    """
    try:
        youtube_url = request.utterance.strip() if request.utterance else None

        if not youtube_url:
            return create_skill_response("🎥 유튜브 URL을 입력해주세요.")

        response = create_skill_response("영상 요약 중입니다... ⏳")

        async def process_youtube():
            try:
                # 1. 자막 추출
                transcript = await get_youtube_transcript(youtube_url)
                if not transcript:
                    await send_callback("자막을 추출할 수 없습니다. 유튜브 URL을 확인해주세요.")
                    return

                # 2. Gemini로 요약
                gemini = get_gemini_service()
                summary, insight, themes = await gemini.summarize_youtube(transcript)

                if not summary:
                    await send_callback("요약 생성에 실패했습니다.")
                    return

                # 3. 콜백 메시지
                callback_msg = f"""
🎥 **영상 요약**

{summary}

💡 **투자 인사이트**
{insight if insight else '특별한 인사이트 없음'}

🏷️ **관련 테마**
{', '.join(themes) if themes else '해당 테마 없음'}
"""

                await send_callback(callback_msg)

            except Exception as e:
                logger.error(f"Error processing YouTube: {str(e)}")
                await send_callback(f"처리 중 오류: {str(e)}")

        background_tasks.add_task(process_youtube)

        return response

    except Exception as e:
        logger.error(f"Error in summarize-youtube block: {str(e)}")
        return create_skill_response("⚠️ 오류가 발생했습니다.")


# ========================================
# BLOCK 5: 종목 분석 (비동기 콜백)
# ========================================

@router.post("/blocks/stock-analysis")
async def stock_analysis_block(
    request: SkillRequest,
    background_tasks: BackgroundTasks
) -> SkillResponse:
    """
    블록: 종목명/티커 입력 → 재무정보 + 뉴스 + LLM 분석
    응답 시간: 8~12초 (비동기 콜백)
    """
    try:
        ticker_or_name = request.utterance.strip() if request.utterance else None

        if not ticker_or_name:
            return create_skill_response("📈 종목명이나 티커를 입력해주세요.")

        response = create_skill_response("종목 분석 중입니다... ⏳")

        async def analyze_stock():
            try:
                # 1. 종목 정보 조회
                stock_info = await get_stock_profile(ticker_or_name)
                if not stock_info:
                    await send_callback("종목을 찾을 수 없습니다.")
                    return

                # 2. 뉴스 조회
                news_list = await fetch_naver_news(limit=3)
                news_titles = [n["title"] for n in news_list]

                # 3. Gemini 분석
                gemini = get_gemini_service()
                technical, news_impact, opinion = await gemini.analyze_stock(
                    stock_name=ticker_or_name,
                    current_price=stock_info.get("price", 0),
                    week_52_high=stock_info.get("week_52_high", 0),
                    week_52_low=stock_info.get("week_52_low", 0),
                    recent_news=news_titles
                )

                # 4. 콜백 메시지
                callback_msg = f"""
📊 **{ticker_or_name} 종합 분석**

💰 **현재가**: {stock_info.get('price', 'N/A'):,}원
📈 **52주**: {stock_info.get('week_52_high', 'N/A'):,} ~ {stock_info.get('week_52_low', 'N/A'):,}

**기술적 분석**
{technical if technical else 'N/A'}

**뉴스 영향**
{news_impact if news_impact else 'N/A'}

**투자 의견**
{opinion if opinion else 'N/A'}
"""

                await send_callback(callback_msg)

            except Exception as e:
                logger.error(f"Error analyzing stock: {str(e)}")
                await send_callback(f"분석 중 오류: {str(e)}")

        background_tasks.add_task(analyze_stock)

        return response

    except Exception as e:
        logger.error(f"Error in stock-analysis block: {str(e)}")
        return create_skill_response("⚠️ 오류가 발생했습니다.")
