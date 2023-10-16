FROM python:3.10-slim

RUN apt-get update -y && apt-get install -y libsnappy-dev
RUN pip install poetry

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
COPY . /app

RUN poetry install && rm -rf $POETRY_CACHE_DIR

CMD ["python", "main.py"]
