FROM python:3.12-slim

WORKDIR /app

# Установите Poetry
ENV POETRY_VERSION=1.8.3
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && poetry --version \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копируйте файлы зависимостей и установите их
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-root

# Копируйте проект
COPY .env .env
COPY src /app/src

ENV PYTHONPATH=/app

EXPOSE 82

# Запустите приложение
ENTRYPOINT ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "82"]
