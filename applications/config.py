"""Application configuration, read from environment variables.

Every variable is documented in `.env.example`. Development works with no
environment at all; with ``APP_ENV=production`` the app refuses to start until
real secrets are provided (see ``validate_config``).
"""
import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Insecure fallbacks that are only acceptable for local development.
DEV_SECRET_KEY = "dev-secret-change-me-do-not-use-in-production"
DEV_ADMIN_PASSWORD = "password"


def _env(name, default=None):
    """Environment variable, treating an empty value like an unset one."""
    value = os.environ.get(name, "").strip()
    return value if value else default


def _env_bool(name, default):
    value = _env(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


def _env_int(name, default):
    return int(_env(name, default))


class Config:
    # "production" turns on the secret checks, HSTS and proxy handling.
    APP_ENV = _env("APP_ENV", "development").strip().lower()
    IS_PRODUCTION = APP_ENV in ("production", "prod")

    SECRET_KEY = _env("SECRET_KEY") or DEV_SECRET_KEY

    # SQLite database location. Defaults to ./data/grocery.db; created and
    # seeded with demo data on first start if it doesn't exist.
    DATABASE_PATH = _env("DATABASE_PATH", os.path.join(BASE_DIR, "data", "grocery.db"))
    # Seconds a connection waits for a lock held by another connection.
    SQLITE_BUSY_TIMEOUT = float(_env("SQLITE_BUSY_TIMEOUT", "15"))

    # JWT
    JWT_SECRET_KEY = _env("JWT_SECRET_KEY") or SECRET_KEY
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=float(_env("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "12")))
    JWT_ERROR_MESSAGE_KEY = "error"

    # Admin account (seeded into the `managers` table on every start)
    ADMIN_USERNAME = _env("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = _env("ADMIN_PASSWORD") or DEV_ADMIN_PASSWORD

    # Caching: Redis when REDIS_URL is set, in-process memory otherwise.
    REDIS_URL = _env("REDIS_URL")
    if REDIS_URL:
        CACHE_TYPE = "RedisCache"
        CACHE_REDIS_URL = REDIS_URL
    else:
        CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300

    # Rate limiting of the login/signup endpoints (Flask-Limiter syntax).
    RATELIMIT_ENABLED = _env_bool("RATELIMIT_ENABLED", True)
    AUTH_RATE_LIMIT = _env("AUTH_RATE_LIMIT", "10 per minute; 100 per hour")
    RATELIMIT_STORAGE_URI = _env("RATELIMIT_STORAGE_URI") or REDIS_URL or "memory://"
    RATELIMIT_HEADERS_ENABLED = True

    # Number of reverse proxies in front of the app whose X-Forwarded-* headers
    # are trusted (Render has one). Use 0 when the app is exposed directly,
    # otherwise clients can spoof their IP and dodge the rate limit.
    TRUSTED_PROXY_COUNT = _env_int("TRUSTED_PROXY_COUNT", 1 if IS_PRODUCTION else 0)

    # Override the default Content-Security-Policy (see app.py) if needed.
    CONTENT_SECURITY_POLICY = _env("CONTENT_SECURITY_POLICY")

    LOG_LEVEL = _env("LOG_LEVEL", "INFO").upper()

    # Comma-separated list of origins allowed to call the API cross-origin.
    # Not needed when the frontend is served by Flask itself (the default).
    CORS_ORIGINS = [o.strip() for o in _env("CORS_ORIGINS", "").split(",") if o.strip()]

    # Built Vue app served by Flask in production
    FRONTEND_DIST = _env("FRONTEND_DIST", os.path.join(BASE_DIR, "frontend", "dist"))


class ConfigError(RuntimeError):
    """Raised when the app is started in production with unsafe settings."""


def validate_config(config):
    """Refuse to run in production with missing or default secrets.

    ``config`` is a mapping such as ``app.config``. Returns quietly in
    development so the app works out of the box.
    """
    if not config.get("IS_PRODUCTION"):
        return

    problems = []
    for key in ("SECRET_KEY", "JWT_SECRET_KEY"):
        if not _env(key):
            problems.append(f"{key} is not set")
        elif config.get(key) == DEV_SECRET_KEY:
            problems.append(f"{key} uses the development default")
        elif len(config.get(key)) < 32:
            problems.append(f"{key} is too short (at least 32 characters required)")

    admin_password = _env("ADMIN_PASSWORD")
    if not admin_password:
        problems.append("ADMIN_PASSWORD is not set")
    elif admin_password == DEV_ADMIN_PASSWORD:
        problems.append('ADMIN_PASSWORD must not be "password"')
    elif len(admin_password) < 8:
        problems.append("ADMIN_PASSWORD must be at least 8 characters")

    if problems:
        raise ConfigError(
            "Refusing to start with APP_ENV=production: "
            + "; ".join(problems)
            + ". Set these environment variables (e.g. `python -c \"import secrets; print(secrets.token_urlsafe(48))\"` "
            "for the keys), or unset APP_ENV for local development."
        )
