FROM python:3.12.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Moscow

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nano \
        git \
        tzdata \
        libpq-dev \
        gcc \
        # Зависимости WeasyPrint
        libglib2.0-0 \
        libcairo2 \
        libpango1.0-0 \
        libffi-dev \
        shared-mime-info \
        && \
    ln -snf /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo "Europe/Moscow" > /etc/timezone && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:8000 --workers ${WEB_CONCURRENCY:-4} --timeout ${TIMEOUT:-120}"]