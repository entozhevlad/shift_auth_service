FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-root

COPY poetry.lock pyproject.toml ./
COPY .env .env
COPY src /app/src
COPY alembic.ini /app/
COPY migrations /app/migrations

ENV PYTHONPATH=/app

RUN alembic revision --autogenerate -m "Create users table" || true

EXPOSE 82

ENTRYPOINT ["sh", "-c", "alembic upgrade head && uvicorn src.app.main:app --host 0.0.0.0 --port 82"]
