import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # SQLite database location. Defaults to ./data/grocery.db; created and
    # seeded with demo data on first start if it doesn't exist.
    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "data", "grocery.db"))

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_ACCESS_TOKEN_EXPIRES = False

    # Admin account (seeded into the `managers` table on first start)
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password")

    # Caching: Redis when REDIS_URL is set, in-process memory otherwise.
    REDIS_URL = os.environ.get("REDIS_URL")
    if REDIS_URL:
        CACHE_TYPE = "RedisCache"
        CACHE_REDIS_URL = REDIS_URL
    else:
        CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300

    # Comma-separated list of origins allowed to call the API cross-origin.
    # Not needed when the frontend is served by Flask itself (the default).
    CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]

    # Built Vue app served by Flask in production
    FRONTEND_DIST = os.environ.get("FRONTEND_DIST", os.path.join(BASE_DIR, "frontend", "dist"))
