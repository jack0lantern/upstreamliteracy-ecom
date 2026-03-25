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

# Bake static assets at build time (avoids shell chaining in Railway preDeploy).
RUN SECRET_KEY=build-not-secret RAILWAY_ENVIRONMENT=production \
    DATABASE_URL=postgresql://build:build@127.0.0.1:5432/build \
    REDIS_URL=redis://127.0.0.1:6379/0 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    python manage.py collectstatic --noinput

EXPOSE 8000
# Railway (and other hosts) set PORT; default 8000 for local docker-compose parity.
CMD gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
