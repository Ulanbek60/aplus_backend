# Dockerfile
FROM python:3.12-slim as base
# базовый слой

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Устанавливаем зависимости — копируем только requirements сначала (для кеша)
COPY requirements.txt /app/requirements.txt
RUN apt-get update && apt-get install -y build-essential libpq-dev gcc \
    && pip install --upgrade pip \
    && pip install -r /app/requirements.txt \
    && apt-get remove -y build-essential gcc \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Копируем проект
COPY . /app

# Создаём пользователя (по желанию)
RUN useradd -m appuser || true
USER appuser

# Для dev: команда по умолчанию запускается через docker-compose override,
# в prod — используем gunicorn/daphne + uvicorn workers
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "aplus_backend.asgi:application"]
