import os

task_always_eager = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"
task_eager_propagates = True
task_store_eager_result = True
timezone = "Asia/Kolkata"
broker_connection_retry_on_startup = True

if task_always_eager:
    # In-process execution for tests. No Redis required.
    broker_url = "memory://"
    result_backend = "cache+memory://"
else:
    broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1")
    result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
