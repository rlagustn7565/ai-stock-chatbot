# 경량 Python 이미지 (512MB 무료 환경 최적화)
FROM python:3.11-slim

# 작업 디렉터리
WORKDIR /app

# 시스템 패키지 (최소한만)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2 \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 환경 변수
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False

# 포트
EXPOSE 8000

# Uvicorn 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
