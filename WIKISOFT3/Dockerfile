# WIKISOFT3 백엔드 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드
COPY . .

# 환경변수
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 포트
EXPOSE 8004

# 실행
CMD ["uvicorn", "external.api.main:app", "--host", "0.0.0.0", "--port", "8004"]
