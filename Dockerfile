# --- Build the Vue frontend -------------------------------------------------
FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- Python runtime (Flask API + serves the built frontend) -----------------
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_ENV=production \
    PORT=8000
WORKDIR /app

# Dependencies first so code changes don't invalidate this layer.
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app.py celeryconfig.py gunicorn.conf.py ./
COPY applications/ ./applications/
COPY --from=frontend /frontend/dist ./frontend/dist

# Code stays root-owned (read-only for the app); only the data dir is writable.
RUN useradd --create-home --uid 10001 appuser && mkdir -p /app/data && chown appuser /app/data
USER appuser

EXPOSE 8000
# The slim image has no curl, so probe with Python's standard library.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/api/health' % os.environ.get('PORT', '8000'), timeout=4)" || exit 1

# Settings (bind to $PORT, 1 worker x 4 threads, logging) are in gunicorn.conf.py.
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
