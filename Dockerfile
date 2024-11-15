FROM python:3.12-slim-bookworm AS builder


RUN mkdir /app
WORKDIR /app
ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  BABEL_CACHE=0

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    python -m pip install -U pip poetry

# Copy poetry files first
COPY pyproject.toml poetry.lock ./

RUN pip install poetry
RUN poetry config virtualenvs.create true && \ 
    poetry config virtualenvs.in-project true && \
    poetry install --no-interaction --no-root --only main

FROM python:3.12-slim-bookworm
WORKDIR /app

COPY --from=builder /app/.venv .venv/

# NOTE: this includes .dev.env file
COPY . .

EXPOSE 8080

CMD ["/app/.venv/bin/uvicorn", "main:app", "--host=0.0.0.0", "--port=8080"]