"""
Telegram 봇 라우터
"""

from fastapi import APIRouter
from telegram import Bot, Update
from services.finance import get_all_indices, get_stock_profile
from services.ai_summary import get_gemini_service
from utils.scraper import fetch_naver_news, extract_article_summary, get_youtube_transcript
from utils.logger import get_logger
from config.settings import get_settings
import asyncio

logger = get_logger(__name__)
router = APIRouter(prefix="/telegram", tags=["telegram"])

def get_bot():
    """봇 인스턴스 반환 (TOKEN 검증 포함)"""
    settings = get_settings()
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")
    return Bot(token=token)


# ========================================
# 명령어 핸들러
# ========================================

async def send_message(chat_id: int, text: str):
    """메시지 전송"""
    try:
        bot = get_bot()
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")


async def handle_start(chat_id: int):
    """시작 명령어"""
    message = """🤖 *AI 주식/금융 비서*

사용 가능한 명령어:
/indices - 📊 주요 지수 & 환율
/news - 📰 최신 금융 뉴스
/summarize_article - 📄 기사 요약
/summarize_youtube - 🎥 유튜브 요약
/analyze_stock - 📈 종목 분석

예시:
/indices
/news
/summarize_article https://news.naver.com/...
/summarize_youtube https://youtube.com/watch?v=...
/analyze_stock 삼성전자"""

    await send_message(chat_id, message)


async def handle_indices(chat_id: int):
    """지수/환율 조회"""
    try:
        await send_message(chat_id, "📊 지수를 불러오는 중...")

        indices_data = await get_all_indices()

        text_lines = ["📊 *주요 지수 & 환율*\n"]

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
        await send_message(chat_id, response_text)

    except Exception as e:
        logger.error(f"Error in indices: {str(e)}")
        await send_message(chat_id, "⚠️ 지수 조회 중 오류가 발생했습니다.")


async def handle_news(chat_id: int):
    """뉴스 헤드라인"""
    try:
        await send_message(chat_id, "📰 뉴스를 불러오는 중...")

        news_list = await fetch_naver_news(limit=5)

        if not news_list:
            await send_message(chat_id, "⚠️ 뉴스를 불러올 수 없습니다.")
            return

        text_lines = ["📰 *금융 뉴스 헤드라인*\n"]
        for i, news in enumerate(news_list, 1):
            text_lines.append(f"{i}. {news['title']}\n{news['url']}")

        response_text = "\n".join(text_lines)
        await send_message(chat_id, response_text)

    except Exception as e:
        logger.error(f"Error in news: {str(e)}")
        await send_message(chat_id, "⚠️ 뉴스 조회 중 오류가 발생했습니다.")


async def handle_summarize_article(chat_id: int, article_url: str):
    """기사 요약"""
    try:
        if not article_url:
            await send_message(chat_id, "📄 기사 URL을 입력해주세요.\n\n예: `/summarize_article https://news.naver.com/...`")
            return

        await send_message(chat_id, "📄 기사를 분석 중입니다... ⏳")

        article_text = await extract_article_summary(article_url)
        if not article_text:
            await send_message(chat_id, "⚠️ 기사를 추출할 수 없습니다. URL을 확인해주세요.")
            return

        gemini = get_gemini_service()
        summary, stocks, impact = await gemini.summarize_article(article_text)

        if not summary:
            await send_message(chat_id, "⚠️ 요약 생성에 실패했습니다.")
            return

        callback_msg = f"""📰 *기사 요약*

{summary}

📊 *영향받을 종목*
{', '.join(stocks) if stocks else '해당 종목 없음'}

⬆️/⬇️ *영향*: {impact if impact else '중립'}"""

        await send_message(chat_id, callback_msg)

    except Exception as e:
        logger.error(f"Error in summarize_article: {str(e)}")
        await send_message(chat_id, f"⚠️ 처리 중 오류: {str(e)}")


async def handle_summarize_youtube(chat_id: int, youtube_url: str):
    """유튜브 요약"""
    try:
        if not youtube_url:
            await send_message(chat_id, "🎥 유튜브 URL을 입력해주세요.\n\n예: `/summarize_youtube https://youtube.com/watch?v=...`")
            return

        await send_message(chat_id, "🎥 영상을 분석 중입니다... ⏳")

        transcript = await get_youtube_transcript(youtube_url)
        if not transcript:
            await send_message(chat_id, "⚠️ 자막을 추출할 수 없습니다. URL을 확인해주세요.")
            return

        gemini = get_gemini_service()
        summary, insight, themes = await gemini.summarize_youtube(transcript)

        if not summary:
            await send_message(chat_id, "⚠️ 요약 생성에 실패했습니다.")
            return

        callback_msg = f"""🎥 *영상 요약*

{summary}

💡 *투자 인사이트*
{insight if insight else '특별한 인사이트 없음'}

🏷️ *관련 테마*
{', '.join(themes) if themes else '해당 테마 없음'}"""

        await send_message(chat_id, callback_msg)

    except Exception as e:
        logger.error(f"Error in summarize_youtube: {str(e)}")
        await send_message(chat_id, f"⚠️ 처리 중 오류: {str(e)}")


async def handle_analyze_stock(chat_id: int, ticker_or_name: str):
    """종목 분석"""
    try:
        if not ticker_or_name:
            await send_message(chat_id, "📈 종목명이나 티커를 입력해주세요.\n\n예: `/analyze_stock 삼성전자`")
            return

        await send_message(chat_id, "📈 종목을 분석 중입니다... ⏳")

        stock_info = await get_stock_profile(ticker_or_name)
        if not stock_info:
            await send_message(chat_id, "⚠️ 종목을 찾을 수 없습니다.")
            return

        news_list = await fetch_naver_news(limit=3)
        news_titles = [n["title"] for n in news_list]

        gemini = get_gemini_service()
        technical, news_impact, opinion = await gemini.analyze_stock(
            stock_name=ticker_or_name,
            current_price=stock_info.get("price", 0),
            week_52_high=stock_info.get("week_52_high", 0),
            week_52_low=stock_info.get("week_52_low", 0),
            recent_news=news_titles
        )

        callback_msg = f"""📊 *{ticker_or_name} 종합 분석*

💰 *현재가*: {stock_info.get('price', 'N/A'):,}원
📈 *52주*: {stock_info.get('week_52_high', 'N/A'):,} ~ {stock_info.get('week_52_low', 'N/A'):,}

*기술적 분석*
{technical if technical else 'N/A'}

*뉴스 영향*
{news_impact if news_impact else 'N/A'}

*투자 의견*
{opinion if opinion else 'N/A'}"""

        await send_message(chat_id, callback_msg)

    except Exception as e:
        logger.error(f"Error in analyze_stock: {str(e)}")
        await send_message(chat_id, f"⚠️ 처리 중 오류: {str(e)}")


# ========================================
# Webhook 엔드포인트
# ========================================

@router.post("/webhook")
async def telegram_webhook(request: dict):
    """Telegram 웹훅"""
    try:
        if "message" not in request:
            return {"ok": True}

        message = request["message"]
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        if not chat_id or not text:
            return {"ok": True}

        logger.info(f"[Telegram] {chat_id}: {text}")

        # 명령어 라우팅 (언더스코어와 공백 모두 지원)
        text_normalized = text.replace("_", " ").lower()

        if text == "/start":
            await handle_start(chat_id)
        elif text == "/indices":
            await handle_indices(chat_id)
        elif text == "/news":
            await handle_news(chat_id)
        elif text_normalized.startswith("/summarize article") or text.startswith("/summarize_article"):
            url = text.replace("/summarize_article", "").replace("/summarizearticle", "").replace("/summarize article", "").strip()
            await handle_summarize_article(chat_id, url)
        elif text_normalized.startswith("/summarize youtube") or text.startswith("/summarize_youtube"):
            url = text.replace("/summarize_youtube", "").replace("/summarizeyoutube", "").replace("/summarize youtube", "").strip()
            await handle_summarize_youtube(chat_id, url)
        elif text_normalized.startswith("/analyze stock") or text.startswith("/analyze_stock"):
            stock = text.replace("/analyze_stock", "").replace("/analyzestock", "").replace("/analyze stock", "").strip()
            await handle_analyze_stock(chat_id, stock)
        else:
            await send_message(chat_id, "❓ 명령어를 인식하지 못했습니다.\n/start 를 입력해주세요.")

        return {"ok": True}

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {"ok": True}
