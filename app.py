import logging
import os
import sys

from flask import Flask, abort, g, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException, InternalServerError, NotFound
from werkzeug.middleware.proxy_fix import ProxyFix

from applications.caching import cache
from applications.config import Config, validate_config
from applications.database import close_db, get_db, init_db
from applications.workers import celery_init_app


def configure_logging(level):
    """Log to stdout so Docker/Render/gunicorn collect everything in one stream."""
    root = logging.getLogger()
    if not any(getattr(h, "_grocery", False) for h in root.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(process)d] [%(levelname)s] %(name)s: %(message)s"))
        handler._grocery = True
        root.addHandler(handler)
    root.setLevel(level)


app = Flask(__name__)
app.config.from_object(Config)
configure_logging(app.config["LOG_LEVEL"])
log = logging.getLogger("grocery")

try:
    validate_config(app.config)
except Exception as exc:
    log.critical("%s", exc)
    raise

# Behind a reverse proxy (Render), trust its X-Forwarded-For/-Proto headers so
# request.remote_addr is the real client (used by the rate limiter) and
# request.scheme is https. X-Forwarded-Host/-Port are not trusted: nothing
# builds absolute URLs, and the platform's proxy already sets Host.
if app.config["TRUSTED_PROXY_COUNT"] > 0:
    n = app.config["TRUSTED_PROXY_COUNT"]
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=n, x_proto=n)

jwt = JWTManager(app)
cache.init_app(app)
if app.config["CORS_ORIGINS"]:
    CORS(app, origins=app.config["CORS_ORIGINS"])
app.teardown_appcontext(close_db)

# In-memory storage is per process, which is consistent because gunicorn runs
# a single worker (see gunicorn.conf.py); with REDIS_URL it is shared.
limiter = Limiter(get_remote_address, app=app, storage_uri=app.config["RATELIMIT_STORAGE_URI"])

init_db(app)


# --- JWT errors: always JSON 401 ------------------------------------------------
@jwt.expired_token_loader
def _expired_token(jwt_header, jwt_payload):
    return jsonify({"error": "Session expired, please log in again"}), 401


@jwt.invalid_token_loader
def _invalid_token(reason):
    return jsonify({"error": "Invalid authorization token"}), 401


@jwt.unauthorized_loader
def _missing_token(reason):
    return jsonify({"error": "Missing authorization token"}), 401


# Tokens outlive the database on an ephemeral disk (redeploy, restart, idle
# spin-down) because the signing key persists. Each token carries the id of
# the database it was issued against ("dbid"); reject it when that database is
# gone or its account no longer exists (e.g. a deleted user whose e-mail was
# re-registered by someone else).
@jwt.token_verification_loader
def _token_matches_database(jwt_header, jwt_payload):
    cache_key = (jwt_payload.get("jti"), jwt_payload.get("dbid"))
    checked = g.get("_token_checked")
    if checked is not None and checked[0] == cache_key:
        return checked[1]  # per_user_cache_key verifies the same token again
    table = "managers" if jwt_payload.get("role") == "admin" else "users"
    row = get_db().execute(
        f"SELECT (SELECT value FROM meta WHERE key = 'db_instance_id'), "
        f"EXISTS (SELECT 1 FROM {table} WHERE email = ?)",
        (jwt_payload.get("sub"),),
    ).fetchone()
    ok = bool(jwt_payload.get("dbid")) and row[0] == jwt_payload.get("dbid") and bool(row[1])
    g._token_checked = (cache_key, ok)
    return ok


@jwt.token_verification_failed_loader
def _stale_token(jwt_header, jwt_payload):
    return jsonify({"error": "Session is no longer valid, please log in again"}), 401


# Background jobs (daily reminder + monthly report e-mails). Only active when
# a Celery worker/beat is running against Redis; the web app works without it.
celery_app = celery_init_app(app)

from celery.schedules import crontab  # noqa: E402
from applications.backend_tasks import daily_reminder, monthly_report  # noqa: E402


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour=22, minute=20), daily_reminder.s(), name="daily reminder")
    sender.add_periodic_task(
        crontab(day_of_month="28", hour=22, minute=20), monthly_report.s(), name="monthly usage"
    )


# The route modules register themselves on `current_app` at import time.
with app.app_context():
    import applications.controllers  # noqa: E402,F401
    import applications.manager_controller  # noqa: E402,F401


# --- Rate limiting of credential endpoints ---------------------------------------
# Applied here (rather than as decorators in the route modules) by wrapping the
# already-registered view functions.
for _endpoint in ("login_route", "manager_login_route", "signup_route"):
    app.view_functions[_endpoint] = limiter.limit(app.config["AUTH_RATE_LIMIT"])(app.view_functions[_endpoint])


@app.get("/api/ready")
def ready():
    """Readiness probe: like /api/health, but also checks the database."""
    try:
        get_db().execute("SELECT 1").fetchone()
    except Exception:
        log.exception("Readiness check failed")
        return jsonify({"status": "unavailable"}), 503
    return jsonify({"status": "ok"})


# --- Error handlers: JSON under /api/ ---------------------------------------------
def _is_api_request():
    return request.path == "/api" or request.path.startswith("/api/")


def _only_spa_matches(exc):
    """True when a 405 comes only from the GET-only SPA catch-all, i.e. no API
    route exists at this path (e.g. POST /api/nope): that is a 404."""
    # A routing 405 lists the allowed methods; spa()'s own abort(405) doesn't.
    if not exc.valid_methods or not set(exc.valid_methods) <= {"GET", "HEAD", "OPTIONS"}:
        return False
    try:
        endpoint, _ = app.url_map.bind("").match(request.path, method="GET")
    except HTTPException:
        return False
    return endpoint == "spa"


@app.errorhandler(HTTPException)
def _http_error(exc):
    if not _is_api_request():
        return exc
    if exc.code == 405 and _only_spa_matches(exc):
        exc = NotFound()
    response = exc.get_response()
    if exc.code == 429:
        message = "Too many attempts. Please wait a minute and try again."
    else:
        message = exc.description or exc.name
    response.data = jsonify({"error": message}).get_data()
    response.content_type = "application/json"
    return response


@app.errorhandler(Exception)
def _unhandled_error(exc):
    log.exception("Unhandled error on %s %s", request.method, request.path)
    if _is_api_request():
        return jsonify({"error": "Internal server error"}), 500
    return InternalServerError()


# --- Security and cache headers ---------------------------------------------------
# The built Vite app loads only same-origin scripts/styles (Bootstrap is bundled);
# Vue applies `style` bindings through the CSSOM, which CSP doesn't restrict.
# Bootstrap's CSS uses data: SVGs for some icons.
DEFAULT_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "font-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; "
    "form-action 'self'; frame-ancestors 'none'"
)


@app.after_request
def _security_headers(response):
    headers = response.headers
    headers.setdefault("X-Content-Type-Options", "nosniff")
    headers.setdefault("X-Frame-Options", "DENY")
    headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    headers.setdefault("Content-Security-Policy", app.config["CONTENT_SECURITY_POLICY"] or DEFAULT_CSP)
    if app.config["IS_PRODUCTION"]:
        headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if _is_api_request():
        # API responses are per-user (JWT); keep them out of shared caches.
        headers.setdefault("Cache-Control", "no-store")
    return response


# --- Built Vue single-page app (frontend/dist) for every non-API path ---------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def spa(path):
    dist = app.config["FRONTEND_DIST"]
    if path == "api" or path.startswith("api/"):
        # The catch-all only matches GET, so a GET to a POST-only API route
        # lands here; answer 405 for those rather than 404.
        adapter = app.url_map.bind("")
        try:
            adapter.match("/" + path, method="POST")
        except Exception:
            abort(404)
        abort(405)
    if path and os.path.isfile(os.path.join(dist, path)):
        response = send_from_directory(dist, path)
        if path.startswith("assets/"):
            # Vite fingerprints everything under assets/, so it never changes.
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response
    if path.startswith("assets/"):
        abort(404)  # a missing bundle must not be answered with index.html
    if os.path.isfile(os.path.join(dist, "index.html")):
        response = send_from_directory(dist, "index.html")
        response.headers["Cache-Control"] = "no-cache"
        return response
    return "Frontend not built. Run `npm run build` in ./frontend, or use `npm run dev` for development.", 404


if __name__ == "__main__":
    debug_default = "0" if app.config["IS_PRODUCTION"] else "1"
    app.run(debug=os.environ.get("FLASK_DEBUG", debug_default) == "1", port=int(os.environ.get("PORT", 5000)))
