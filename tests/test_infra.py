import os
import subprocess
import sys

import pytest

from helpers import assert_error, bearer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200 and response.get_json() == {"status": "ok"}


def test_ready(client):
    response = client.get("/api/ready")
    assert response.status_code == 200 and response.get_json() == {"status": "ok"}


def test_ready_reports_database_failure(app, client, monkeypatch, tmp_path):
    # A path inside a missing directory can't be opened by SQLite.
    monkeypatch.setitem(app.config, "DATABASE_PATH", str(tmp_path / "missing" / "db.sqlite"))
    response = client.get("/api/ready")
    assert response.status_code == 503 and response.get_json() == {"status": "unavailable"}


@pytest.mark.parametrize("path", ["/api/nope", "/api", "/api/", "/api/getProduct", "/api/category/abc"])
def test_unknown_api_path_is_json_404(client, path):
    assert_error(client.get(path), 404)


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
def test_unknown_api_path_with_other_methods_is_json_404(client, method):
    # Regression: the GET-only SPA catch-all used to turn these into 405.
    assert_error(client.open("/api/nope", method=method, json={}), 404)


def test_unsupported_method_on_existing_post_route_is_405(client):
    assert_error(client.put("/api/login", json={}), 405)


@pytest.mark.parametrize("path", ["/api/login", "/api/signup", "/api/search", "/api/add_to_cart",
                                  "/api/manager/add_product", "/api/admin/accept_manager"])
def test_get_on_post_only_route_is_405(client, path):
    assert_error(client.get(path), 405)


def test_wrong_method_on_get_route_is_405(client):
    assert_error(client.post("/api/health"), 405)


def test_unexpected_error_is_generic_json_500(app, client, monkeypatch, shopper_token):
    import applications.controllers as controllers

    def boom(email):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(controllers, "fetch_cart_items_by_email", boom)
    message = assert_error(client.get("/api/shopping_cart", headers=bearer(shopper_token)), 500)
    assert "secret" not in message


def test_unhandled_error_outside_api_decorator_is_json_500(app, client, monkeypatch):
    import applications.controllers  # noqa: F401  (route already registered)

    def boom():
        raise RuntimeError("secret internal detail")

    monkeypatch.setitem(app.view_functions, "health", boom)
    assert assert_error(client.get("/api/health"), 500) == "Internal server error"


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cross-Origin-Opener-Policy": "same-origin",
}


@pytest.mark.parametrize("path", ["/api/health", "/api/nope", "/"])
def test_security_headers(client, path):
    response = client.get(path)
    for name, value in SECURITY_HEADERS.items():
        assert response.headers.get(name) == value, name
    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp and "frame-ancestors 'none'" in csp
    assert "Permissions-Policy" in response.headers
    assert "Strict-Transport-Security" not in response.headers  # development mode


def test_api_responses_are_not_cacheable(client):
    assert client.get("/api/health").headers["Cache-Control"] == "no-store"


# --- built frontend (SPA) -----------------------------------------------------------

@pytest.fixture
def frontend_dist(app, tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>Grocery SPA</title>")
    (dist / "assets" / "app-abc123.js").write_text("console.log('hi')")
    (dist / "favicon.ico").write_bytes(b"\x00\x00")
    monkeypatch.setitem(app.config, "FRONTEND_DIST", str(dist))
    return dist


@pytest.mark.parametrize("path", ["/", "/login", "/manage/edit_product/3", "/cart?x=1"])
def test_spa_fallback_serves_index(client, frontend_dist, path):
    response = client.get(path)
    assert response.status_code == 200
    assert b"Grocery SPA" in response.data
    assert response.headers["Cache-Control"] == "no-cache"


def test_spa_serves_static_files(client, frontend_dist):
    asset = client.get("/assets/app-abc123.js")
    assert asset.status_code == 200 and b"console.log" in asset.data
    assert "immutable" in asset.headers["Cache-Control"]
    assert client.get("/favicon.ico").status_code == 200


def test_spa_missing_asset_is_404_not_index(client, frontend_dist):
    response = client.get("/assets/missing.js")
    assert response.status_code == 404
    assert b"Grocery SPA" not in response.data


def test_spa_does_not_shadow_api(client, frontend_dist):
    assert_error(client.get("/api/nope"), 404)


def test_frontend_not_built(client):
    response = client.get("/")
    assert response.status_code == 404
    assert b"Frontend not built" in response.data


# --- production configuration check ------------------------------------------------

def _import_app(tmp_path, **env):
    clean = {k: v for k, v in os.environ.items()
             if k not in ("SECRET_KEY", "JWT_SECRET_KEY", "ADMIN_PASSWORD", "APP_ENV")}
    clean.update(DATABASE_PATH=str(tmp_path / "prod.db"), LOG_LEVEL="ERROR", **env)
    return subprocess.run([sys.executable, "-c", "import app"], cwd=ROOT, env=clean,
                          capture_output=True, text=True, timeout=120)


STRONG = {"SECRET_KEY": "s" * 48, "JWT_SECRET_KEY": "j" * 48, "ADMIN_PASSWORD": "a-strong-admin-password"}


@pytest.mark.parametrize("env,problem", [
    ({}, "SECRET_KEY is not set"),
    ({**STRONG, "SECRET_KEY": "short"}, "SECRET_KEY is too short"),
    ({**STRONG, "JWT_SECRET_KEY": "dev-secret-change-me-do-not-use-in-production"}, "JWT_SECRET_KEY uses the"),
    ({**STRONG, "ADMIN_PASSWORD": "password"}, 'ADMIN_PASSWORD must not be "password"'),
    ({**STRONG, "ADMIN_PASSWORD": "short"}, "ADMIN_PASSWORD must be at least 8"),
    ({k: v for k, v in STRONG.items() if k != "ADMIN_PASSWORD"}, "ADMIN_PASSWORD is not set"),
])
def test_production_refuses_weak_config(tmp_path, env, problem):
    result = _import_app(tmp_path, APP_ENV="production", **env)
    assert result.returncode != 0
    assert "Refusing to start with APP_ENV=production" in result.stderr
    assert problem in result.stderr


def test_production_starts_with_strong_secrets(tmp_path):
    result = _import_app(tmp_path, APP_ENV="production", **STRONG)
    assert result.returncode == 0, result.stderr


def test_production_sends_hsts(app, client, monkeypatch):
    monkeypatch.setitem(app.config, "IS_PRODUCTION", True)
    assert "max-age=" in client.get("/api/health").headers["Strict-Transport-Security"]
