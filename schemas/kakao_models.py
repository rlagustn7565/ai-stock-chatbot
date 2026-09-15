"""
카카오 i 오픈빌더 요청/응답 스키마
- SkillResponse: 즉시응답 (< 2초)
- Callback: 비동기 콜백 응답 (5초 초과 시)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ========================================
# 카카오 스킬 요청 모델
# ========================================

class UserRequest(BaseModel):
    """사용자 입력 정보"""
    text: str
    params: Optional[Dict[str, Any]] = None


class SkillRequest(BaseModel):
    """카카오 스킬 요청"""
    version: str = "2.0"
    user_id: Optional[str] = None
    utterance: Optional[str] = None
    blocks: Optional[List[Dict[str, Any]]] = None
    properties: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None
    contexts: Optional[List[Dict[str, Any]]] = None

    class Config:
        extra = "allow"  # 추가 필드 허용


# ========================================
# 카카오 스킬 응답 모델 (즉시응답)
# ========================================

class SimpleText(BaseModel):
    """단순 텍스트 블록"""
    text: str


class ButtonText(BaseModel):
    """버튼 텍스트 블록"""
    text: str
    action: str = "message"
    label: str = ""


class Button(BaseModel):
    """버튼 액션"""
    text: str
    action: str = "message"
    label: Optional[str] = None


class CommerceCard(BaseModel):
    """상품 카드 (뉴스 링크용)"""
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    url: str
    buttons: Optional[List[ButtonText]] = None


class SkillTemplate(BaseModel):
    """스킬 응답 템플릿"""
    outputs: List[Dict[str, Any]] = Field(default_factory=list)


class SkillResponse(BaseModel):
    """카카오 즉시응답 (< 2초)"""
    version: str = "2.0"
    template: SkillTemplate


# ========================================
# 비동기 콜백 응답 모델
# ========================================

class KakaoMessage(BaseModel):
    """카카오 메시지 블록"""
    text: Optional[str] = None
    typing: Optional[bool] = None  # 타이핑 표시


class CallbackResponse(BaseModel):
    """비동기 콜백 응답
    카카오 콜백 URL에 POST로 전송
    """
    kakaoMessage: Optional[KakaoMessage] = None
    contexts: Optional[List[Dict[str, Any]]] = None

    class Config:
        extra = "allow"


# ========================================
# 도메인별 커스텀 응답 모델
# ========================================

class FinanceData(BaseModel):
    """금융 데이터 응답"""
    symbol: str
    name: str
    price: Optional[float] = None
    change_percent: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class NewsArticle(BaseModel):
    """뉴스 기사"""
    title: str
    url: str
    source: str = "Naver"
    summary: Optional[str] = None
    related_stocks: Optional[List[str]] = None


class YouTubeSummary(BaseModel):
    """유튜브 영상 요약"""
    url: str
    title: Optional[str] = None
    summary: str
    investment_insight: Optional[str] = None
    transcribed_at: datetime = Field(default_factory=datetime.now)


class StockAnalysis(BaseModel):
    """종목 분석 결과"""
    ticker: str
    company_name: str
    current_price: float
    market_cap: Optional[str] = None
    per: Optional[float] = None  # Price-Earnings Ratio
    pbr: Optional[float] = None  # Price-Book Ratio
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    analysis_text: Optional[str] = None
    recent_news: Optional[List[NewsArticle]] = None
