# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    tesseract-ocr tesseract-ocr-rus \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python зависимости
# --mount=type=cache сохраняет скачанные пакеты между сборками →
# повторный docker compose up -d занимает секунды вместо минут
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# ── Предзагрузка ONNX-модели эмбеддингов в слой Docker ───────────────────
# fastembed скачивает модель (~25 МБ) один раз при сборке;
# при запуске контейнера модель уже на диске — старт мгновенный
RUN --mount=type=cache,target=/root/.cache/pip \
    python -c "\
from fastembed import TextEmbedding; \
print('Downloading intfloat/multilingual-e5-small (ONNX)...'); \
TextEmbedding('intfloat/multilingual-e5-small', cache_dir='/app/fastembed_cache'); \
print('Model cached OK')"

COPY . .

RUN mkdir -p /app/uploads

ENV FASTEMBED_CACHE_DIR=/app/fastembed_cache

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
