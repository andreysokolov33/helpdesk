# syntax=docker/dockerfile:1

# --- React (Vite) → app/static/helpdesk ---
FROM node:22-alpine AS frontend

WORKDIR /build/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
# brandLogos.ts импортирует SVG из app/static/images/
COPY app/static/images/ ../app/static/images/

RUN npm run build

# --- FastAPI ---
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Moscow \
    HOST=0.0.0.0 \
    PORT=8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo "${TZ}" > /etc/timezone \
    && apt-get clean \
    && apt-get nano \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Собранный SPA (vite.config.ts → ../app/static/helpdesk)
COPY --from=frontend /build/app/static/helpdesk ./app/static/helpdesk

RUN mkdir -p logs uploads

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker main:app -b ${HOST}:${PORT} --workers ${WEB_CONCURRENCY:-4} --timeout ${TIMEOUT:-120}"]
