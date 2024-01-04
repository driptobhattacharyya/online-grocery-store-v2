from flask import Flask, g
from applications.database import close_db
from flask_jwt_extended import JWTManager
from applications.config import Config
from applications.caching import cache

app = Flask(__name__)
app.app_context().push()
app.config.from_object(Config)
jwt = JWTManager(app)
cache.init_app(app)

@app.teardown_appcontext
def teardown_db(exception=None):
    db = g.pop('db', None)
    print("hi")
    if db is not None:
        db.close()

from flask_cors import CORS
CORS(app, supports_credentials=True)

from applications.workers import celery_init_app
celery_app = celery_init_app(app)

from celery.schedules import crontab
from applications.backend_tasks import daily_reminder, monthly_report

@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour=22, minute=20),
        daily_reminder.s(),
        name="daily reminder",
    )
    sender.add_periodic_task(
        crontab(day_of_month='28', hour=22, minute=20),
        monthly_report.s(),
        name="monthly usage",
    )


# def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(
#         120,
#         
#         daily_reminder.s(),
#         name="daily reminder",
#     )






from applications.controllers import *
from applications.manager_controller import *

if __name__ == '__main__':
    app.run(debug=True)
