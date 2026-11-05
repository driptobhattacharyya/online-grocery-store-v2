import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from applications.caching import cache
from applications.config import Config
from applications.database import close_db

app = Flask(__name__)
app.config.from_object(Config)

jwt = JWTManager(app)
cache.init_app(app)
CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)


@app.before_request
def prepare_database():
    from applications.schema import ensure_database

    ensure_database()


@app.teardown_appcontext
def teardown_db(exception=None):
    close_db(exception)


@jwt.unauthorized_loader
def unauthorized(reason):
    return jsonify({"error": "Authentication required."}), 401


@jwt.invalid_token_loader
def invalid_token(reason):
    return jsonify({"error": "Invalid token."}), 401


@jwt.expired_token_loader
def expired_token(header, payload):
    return jsonify({"error": "Token expired."}), 401


from applications.workers import celery_init_app

celery_app = celery_init_app(app)

with app.app_context():
    import applications.controllers  # noqa: E402,F401
    import applications.manager_controller  # noqa: E402,F401

from celery.schedules import crontab
from applications.backend_tasks import daily_reminder, low_stock_alert, monthly_report


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour=18, minute=0),
        daily_reminder.s(),
        name="daily reminder",
    )
    sender.add_periodic_task(
        crontab(hour=8, minute=0),
        low_stock_alert.s(),
        name="low stock alert",
    )
    sender.add_periodic_task(
        crontab(day_of_month="1", hour=9, minute=0),
        monthly_report.s(),
        name="monthly usage",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=os.environ.get("FLASK_DEBUG") == "1")
