FROM python:3.11-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    tesseract-ocr tesseract-ocr-rus \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Предзагрузка модели эмбеддингов в слой Docker ────────────────────────
# Выполняется при сборке образа — при запуске модель уже на диске
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
print('Downloading intfloat/multilingual-e5-small...'); \
SentenceTransformer('intfloat/multilingual-e5-small'); \
print('Model cached OK')"

COPY . .

RUN mkdir -p /app/uploads

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
