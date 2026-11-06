import os

from flask import Flask, abort, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from applications.caching import cache
from applications.config import Config
from applications.database import close_db, init_db
from applications.workers import celery_init_app

app = Flask(__name__)
app.config.from_object(Config)
app.app_context().push()

jwt = JWTManager(app)
cache.init_app(app)
if app.config["CORS_ORIGINS"]:
    CORS(app, origins=app.config["CORS_ORIGINS"])
app.teardown_appcontext(close_db)

init_db(app)

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


import applications.controllers  # noqa: E402,F401  (registers routes)
import applications.manager_controller  # noqa: E402,F401


# Serve the built Vue single-page app (frontend/dist) for every non-API path.
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def spa(path):
    dist = app.config["FRONTEND_DIST"]
    if path.startswith("api/"):
        abort(404)
    if path and os.path.isfile(os.path.join(dist, path)):
        return send_from_directory(dist, path)
    if os.path.isfile(os.path.join(dist, "index.html")):
        return send_from_directory(dist, "index.html")
    return "Frontend not built. Run `npm run build` in ./frontend, or use `npm run dev` for development.", 404


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "1") == "1", port=int(os.environ.get("PORT", 5000)))
