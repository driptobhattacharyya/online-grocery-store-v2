"""Shared fixtures.

``app.py`` builds the Flask app at import time from environment variables, so
the test environment (a throw-away SQLite file, rate limiting off, development
mode) is set up here, *before* ``app`` is imported.

Every test gets a freshly seeded database: the seeded DB created by the import
is saved once, then copied over the test DB (SQLite backup API) before each
test. The Flask cache is cleared too.
"""
import os
import shutil
import sqlite3
import sys
import tempfile

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

_TMP = tempfile.mkdtemp(prefix="grocery-tests-")

# Settings the app reads at import time. Anything inherited from the
# developer's shell that would change behaviour is removed.
for _key in ("REDIS_URL", "CORS_ORIGINS", "CONTENT_SECURITY_POLICY", "SECRET_KEY", "JWT_SECRET_KEY",
             "ADMIN_USERNAME", "ADMIN_PASSWORD", "TRUSTED_PROXY_COUNT", "AUTH_RATE_LIMIT"):
    os.environ.pop(_key, None)
os.environ.update({
    "APP_ENV": "development",
    "DATABASE_PATH": os.path.join(_TMP, "test.db"),
    "RATELIMIT_ENABLED": "false",
    "RATELIMIT_STORAGE_URI": "memory://",
    "FRONTEND_DIST": os.path.join(_TMP, "no-frontend"),
    "LOG_LEVEL": "WARNING",
})

from app import app as flask_app  # noqa: E402
from applications.caching import cache  # noqa: E402
from helpers import ADMIN, DEMO_MANAGER, DEMO_USER  # noqa: E402

PRISTINE_DB = os.path.join(_TMP, "pristine.db")


def _copy_db(src_path, dst_path):
    src = sqlite3.connect(src_path)
    dst = sqlite3.connect(dst_path)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


@pytest.fixture(scope="session")
def app():
    flask_app.config.update(TESTING=True)
    # Importing app already created and seeded DATABASE_PATH; keep a copy.
    _copy_db(flask_app.config["DATABASE_PATH"], PRISTINE_DB)
    yield flask_app
    shutil.rmtree(_TMP, ignore_errors=True)


@pytest.fixture(autouse=True)
def clean_state(app):
    """Fresh seeded database and empty cache for every test."""
    _copy_db(PRISTINE_DB, app.config["DATABASE_PATH"])
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def query(app):
    """Run a read query directly against the test database."""

    def run(sql, *params):
        conn = sqlite3.connect(app.config["DATABASE_PATH"])
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    return run


@pytest.fixture
def execute(app):
    """Run a write statement directly against the test database."""

    def run(sql, *params):
        conn = sqlite3.connect(app.config["DATABASE_PATH"])
        try:
            conn.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    return run


def _login(client, path, email, password):
    response = client.post(path, json={"email": email, "password": password})
    assert response.status_code == 200, response.get_json()
    return response.get_json()["access_token"]


@pytest.fixture
def login(client):
    """Log a shopper/manager in and return the access token."""
    return lambda email, password: _login(client, "/api/login", email, password)


@pytest.fixture
def shopper_token(client):
    return _login(client, "/api/login", *DEMO_USER)


@pytest.fixture
def manager_token(client):
    return _login(client, "/api/login", *DEMO_MANAGER)


@pytest.fixture
def admin_token(client):
    return _login(client, "/api/admin/login", *ADMIN)


@pytest.fixture
def signup(client):
    """Create a shopper account and return its email."""

    def run(email="new@example.com", password="secret123", name="New Shopper", phone="1234567890"):
        response = client.post("/api/signup", json={
            "name": name, "email": email, "password": password, "phoneNo": phone, "address": "1 Test Road",
        })
        assert response.status_code == 201, response.get_json()
        return email

    return run
