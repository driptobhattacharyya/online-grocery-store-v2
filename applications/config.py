import os
import secrets
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)


def _persisted_secret(env_name, filename):
    """Read a secret from the environment, or from a gitignored instance file.

    Nothing secret is hard-coded in source. A local file is created on first
    use so JWTs stay valid across restarts of a demo that has no .env yet.
    """
    configured = os.environ.get(env_name)
    if configured:
        return configured
    path = os.path.join(INSTANCE_DIR, filename)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            existing = handle.read().strip()
            if existing:
                return existing
    generated = secrets.token_hex(32)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(generated)
    return generated


def _cache_type():
    configured = os.environ.get("CACHE_TYPE")
    if configured:
        return configured
    try:
        import redis

        client = redis.Redis(
            host=os.environ.get("CACHE_REDIS_HOST", "localhost"),
            port=int(os.environ.get("CACHE_REDIS_PORT", "6379")),
            db=int(os.environ.get("CACHE_REDIS_DB", "3")),
            socket_connect_timeout=0.3,
        )
        client.ping()
        return "RedisCache"
    except Exception:
        return "SimpleCache"


class Config:
    SECRET_KEY = _persisted_secret("SECRET_KEY", "secret_key")
    JWT_SECRET_KEY = _persisted_secret("JWT_SECRET_KEY", "jwt_secret_key")
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get("JWT_EXPIRES_HOURS", "12")))

    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "instance", "grocery.db"))
    REPORT_DIR = os.environ.get("REPORT_DIR", os.path.join(INSTANCE_DIR, "reports"))

    CACHE_TYPE = _cache_type()
    CACHE_REDIS_HOST = os.environ.get("CACHE_REDIS_HOST", "localhost")
    CACHE_REDIS_PORT = int(os.environ.get("CACHE_REDIS_PORT", "6379"))
    CACHE_REDIS_DB = int(os.environ.get("CACHE_REDIS_DB", "3"))
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", "300"))

    CORS_ORIGINS = [
        origin.strip()
        for origin in os.environ.get(
            "CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
        ).split(",")
        if origin.strip()
    ]
