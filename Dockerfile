FROM python:3.12-slim

# install pg_isready
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

# Создаём пользователя (по желанию)
RUN useradd -m appuser || true
USER appuser

# Для dev: команда по умолчанию запускается через docker-compose override,
# в prod — используем gunicorn/daphne + uvicorn workers
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "aplus_backend.asgi:application"]
