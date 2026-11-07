"""Gunicorn settings (loaded automatically from the working directory).

Run with: gunicorn app:app
"""
import os

bind = f"0.0.0.0:{os.environ.get('PORT') or '8000'}"

# Exactly one worker process on purpose: the SQLite database, the in-memory
# response cache (SimpleCache) and the in-memory rate-limit counters all live
# in a single process. More processes would each get their own cache and
# rate-limit counters (making limits N times looser and cache invalidation
# inconsistent) and would contend for SQLite's single writer lock. Concurrency
# comes from threads instead, which also suits the free tier's 512 MB of RAM.
# Raise GUNICORN_WORKERS only with REDIS_URL set (shared cache + limiter).
workers = int(os.environ.get("GUNICORN_WORKERS") or 1)
threads = int(os.environ.get("GUNICORN_THREADS") or 4)
worker_class = "gthread"

timeout = int(os.environ.get("GUNICORN_TIMEOUT") or 60)
graceful_timeout = 30
keepalive = 5

# Logs to stdout/stderr for Docker / Render.
accesslog = "-"
errorlog = "-"
loglevel = (os.environ.get("LOG_LEVEL") or "info").lower()
access_log_format = '%({x-forwarded-for}i)s %(h)s "%(r)s" %(s)s %(b)s %(M)sms "%(a)s"'

# Trust X-Forwarded-Proto etc. from the platform's proxy. The container is
# only reachable through it; client IPs are handled by ProxyFix in app.py.
forwarded_allow_ips = os.environ.get("FORWARDED_ALLOW_IPS") or "*"

# Heartbeat files in RAM rather than on the container's (possibly slow) disk.
if os.path.isdir("/dev/shm"):
    worker_tmp_dir = "/dev/shm"
