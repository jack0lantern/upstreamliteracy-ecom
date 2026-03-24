# Monorepo build for Railway: context is the repository root (see railway.toml).
# Local backend-only builds still use backend/Dockerfile via docker-compose.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir .

COPY backend/ .

EXPOSE 8000
# Railway (and other hosts) set PORT; default 8000 for local docker-compose parity.
CMD gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
