import os

_redis = os.environ.get("REDIS_URL", "redis://localhost:6379")
broker_url = os.environ.get("CELERY_BROKER_URL", _redis.rstrip("/") + "/1")
result_backend = os.environ.get("CELERY_RESULT_BACKEND", _redis.rstrip("/") + "/2")
timezone = "Asia/Kolkata"
broker_connection_retry_on_startup = True
