import os

_redis = (os.environ.get("REDIS_URL") or "redis://localhost:6379").rstrip("/")
broker_url = os.environ.get("CELERY_BROKER_URL") or _redis + "/1"
result_backend = os.environ.get("CELERY_RESULT_BACKEND") or _redis + "/2"
timezone = "Asia/Kolkata"
broker_connection_retry_on_startup = True
