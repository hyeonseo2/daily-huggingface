# daily-huggingface/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 시스템 의존성(필요 최소)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl tzdata && \
    rm -rf /var/lib/apt/lists/*

# 타임존 기본값: Asia/Seoul
ENV TZ=Asia/Seoul

# 코드 복사
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app /app/app

# 출력 디렉터리(컨테이너 내부): /data
RUN mkdir -p /data
VOLUME ["/data"]

# 기본 실행: 매일 한 번 생성하는 스크립트(수동 실행 시에도 1회 생성)
ENV NEWSLETTER_TOP_N=12
CMD ["python", "-m", "app.main"]
