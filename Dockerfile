FROM python:3.12-slim

WORKDIR /app

ENV POETRY_VERSION=1.8.3

COPY poetry.lock pyproject.toml ./

RUN apt-get update && \
    apt-get install --no-install-recommends -y && \
    apt-get install -y python3-pip && \
    pip install "poetry==$POETRY_VERSION"

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-root

COPY .env .env

COPY src /app/src

COPY alembic.ini /app/

COPY migrations /app/migrations

ENV PYTHONPATH=/app

# Выполняем команду alembic revision
RUN alembic revision --autogenerate -m "Create users table" || true

EXPOSE 82

# Запускаем миграции и приложение
ENTRYPOINT ["sh", "-c", "alembic upgrade head && uvicorn src.app.main:app --host 0.0.0.0 --port 82"]
