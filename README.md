# 🤖 AI 주식/금융 비서 (카카오톡 챗봇 백엔드)

카카오 i 오픈빌더 기반의 **AI 주식/금융 비서** 백엔드 시스템입니다.

네이버 뉴스 요약, 유튜브 자막 분석, 실시간 금융 지수, 종목 분석 등을 제공하며, **Render 무료 서버에서 24시간 안정적으로 배포**됩니다.

---

## 🎯 주요 기능

| 기능 | 설명 | 응답 시간 | 타입 |
|------|------|---------|------|
| **지수/환율 조회** | KOSPI, S&P500, 환율 등 실시간 조회 | ~2초 | 즉시응답 |
| **금융 뉴스** | 네이버 금융 헤드라인 5개 | ~2초 | 즉시응답 |
| **기사 요약** | 뉴스 URL → 3줄 요약 + 관련 종목 | 5~10초 | 비동기 콜백 |
| **유튜브 요약** | 유튜브 URL → 자막 추출 + 투자 인사이트 | 8~15초 | 비동기 콜백 |
| **종목 분석** | 종목명/티커 → 재무정보 + LLM 분석 | 8~12초 | 비동기 콜백 |

---

## 🏗️ 기술 스택

### Backend
- **Framework**: FastAPI + Uvicorn (비동기)
- **LLM**: Google Gemini API (요약 & 분석)
- **Financial Data**: yfinance + pykrx (실시간 데이터)
- **Web Scraping**: BeautifulSoup4 + Trafilatura + YouTube API

### Deployment
- **Cloud**: Render (무료 플랜)
- **Container**: Docker
- **Monitoring**: UptimeRobot (24시간 가동)

---

## 📋 설치 및 실행

### 1. 사전 준비

- Python 3.11+
- Git
- API 키:
  - **Google Gemini API Key**: https://ai.google.dev/
  - **카카오 앱**: https://developers.kakao.com/

### 2. 로컬 설치

```bash
# 저장소 클론
git clone <repo-url>
cd 주식챗봇

# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에 API 키 입력
```

### 3. 로컬 실행

```bash
# FastAPI 개발 서버 실행
python main.py

# 또는
uvicorn main:app --reload --port 8000

# 브라우저에서 확인
# - 메인: http://localhost:8000
# - API 문서: http://localhost:8000/docs
# - 헬스체크: http://localhost:8000/health
```

---

## 🚀 Render 배포 (24시간 무료)

### 1단계: GitHub에 푸시

```bash
git add .
git commit -m "Initial commit: AI Stock Chatbot"
git push origin main
```

### 2단계: Render 대시보드에서 배포

1. https://render.com 접속 → 회원가입
2. "New +" → "Web Service"
3. GitHub 저장소 선택
4. 배포 설정:
   - **Name**: `ai-stock-chatbot`
   - **Environment**: `Python 3.11`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`
   - **Plan**: `Free`

### 3단계: 환경 변수 설정

Render 대시보드 → Environment 탭에서 추가:

```
GOOGLE_API_KEY=your_key_here
KAKAO_APP_ID=your_id_here
KAKAO_APP_SECRET=your_secret_here
KAKAO_CALLBACK_URL=https://your-app.onrender.com/v1/callback
DEBUG=False
```

### 4단계: UptimeRobot으로 24시간 가동 설정

1. https://uptimerobot.com 접속 → 무료 가입
2. "Add New Monitor"
3. 설정:
   - **Monitor Type**: `HTTP(s)`
   - **URL**: `https://your-app.onrender.com/health`
   - **Monitoring Interval**: `5 minutes` (또는 10분)
   - **Alert Contacts**: 이메일 추가

⚠️ **매우 중요**: Render 무료 플랜은 15분 미요청 시 자동으로 슬립 상태 진입
→ UptimeRobot의 주기적 핑이 서버를 깨워 **24시간 상시 가동**

---

## 🔌 카카오 i 오픈빌더 연동

### API 엔드포인트

```
POST /v1/blocks/indices         → 지수/환율 조회 (즉시응답)
POST /v1/blocks/news            → 뉴스 헤드라인 (즉시응답)
POST /v1/blocks/summarize-article   → 기사 요약 (비동기 콜백)
POST /v1/blocks/summarize-youtube   → 유튜브 요약 (비동기 콜백)
POST /v1/blocks/stock-analysis      → 종목 분석 (비동기 콜백)
```

### 카카오 블록 설정 예시

**인텐트**: "주식 정보 조회"
- **블록 1**: `/v1/blocks/indices` → 지수/환율 즉시 반환
- **블록 2**: "기사 URL 입력" → `/v1/blocks/summarize-article` → 콜백으로 결과 전송

---

## 📊 응답 예시

### 지수/환율 (즉시응답)

```
📊 **주요 지수 & 환율**

📈 KOSPI: 2,950.45 (+1.23%)
📉 S&P500: 5,234.80 (-0.45%)
📈 USD/KRW: 1,234.50 (+0.12%)
```

### 기사 요약 (콜백)

```
📰 **기사 요약**

삼성전자 1분기 영업이익 5% 감소했으나,
칩 수요 회복으로 2분기 개선 전망.

📊 **영향받을 종목**
삼성전자, SK하이닉스, 인텔

⬆️ **영향**: 긍정적
```

---

## 🔧 환경 변수

[.env.example](.env.example) 참고

```
# LLM
GOOGLE_API_KEY=your_gemini_api_key

# 카카오 챗봇
KAKAO_APP_ID=your_kakao_app_id
KAKAO_APP_SECRET=your_kakao_app_secret
KAKAO_CALLBACK_URL=https://your-app.onrender.com/v1/callback

# 서버
DEBUG=False
HOST=0.0.0.0
PORT=8000
```

---

## 📁 프로젝트 구조

```
주식챗봇/
├── main.py                    # FastAPI 메인 진입점
├── requirements.txt           # Python 의존성
├── Dockerfile                 # 컨테이너 이미지
├── render.yaml               # Render 배포 설정
│
├── config/
│   └── settings.py           # 환경 변수 관리
│
├── services/
│   ├── finance.py            # 금융 데이터 (지수/환율/종목)
│   └── ai_summary.py         # Gemini 기반 요약/분석
│
├── routers/
│   └── kakao.py              # 카카오 챗봇 블록 핸들러
│
├── schemas/
│   └── kakao_models.py       # Pydantic 요청/응답 모델
│
└── utils/
    ├── scraper.py            # 웹 스크래핑 (Naver, YouTube)
    └── logger.py             # 구조화된 로깅
```

---

## 🐛 문제 해결

### 1. Render에서 "Application crashed"

**원인**: Python 의존성 설치 실패
**해결**: requirements.txt 확인 및 재배포

```bash
git push origin main  # 자동 재배포
```

### 2. 카카오 콜백이 안 됨

**원인**: KAKAO_CALLBACK_URL이 잘못됨
**확인**:
```
https://your-app.onrender.com/v1/callback
```

카카오 오픈빌더 → 기술 설정 → 콜백 URL 확인

### 3. "GOOGLE_API_KEY not set"

**원인**: 환경 변수 미설정
**해결**: Render 대시보드 → Environment 탭에서 설정

---

## 📞 지원 & 문의

- FastAPI 문서: https://fastapi.tiangolo.com/
- Render 가이드: https://render.com/docs
- Google Gemini API: https://ai.google.dev/docs
- 카카오 개발자: https://developers.kakao.com/

---

## 📄 라이선스

MIT License

---

**Made with ❤️ for Korean Investors** 🇰🇷📈
