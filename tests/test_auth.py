import os
import subprocess
import sys
import textwrap

import pytest
from flask_jwt_extended import create_access_token

from helpers import ADMIN, DEMO_USER, assert_error, bearer, mint_token

VALID_SIGNUP = {"name": "Alice", "email": "alice@example.com", "password": "secret123",
                "phoneNo": "123-456-7890", "address": " 5 Elm St "}


# --- signup -------------------------------------------------------------------

def test_signup_creates_user_and_profile(client, query, login):
    response = client.post("/api/signup", json=VALID_SIGNUP)
    assert response.status_code == 201
    assert response.get_json() == {"message": "Success"}

    assert query("SELECT email FROM users WHERE email = ?", "alice@example.com") == [("alice@example.com",)]
    # Phone and address are stored trimmed; the password is hashed.
    assert query("SELECT name, address, phone FROM user_profiles WHERE email = ?", "alice@example.com") == [
        ("Alice", "5 Elm St", "123-456-7890")]
    assert query("SELECT password FROM users WHERE email = ?", "alice@example.com")[0][0] != "secret123"

    login("alice@example.com", "secret123")


@pytest.mark.parametrize("override", [
    {"name": ""},
    {"name": None},
    {"email": "not-an-email"},
    {"email": ""},
    {"phoneNo": "12"},
    {"phoneNo": None},
    {"password": ""},
    {"password": "12345"},  # under 6 characters
    {"address": 42},
])
def test_signup_rejects_invalid_fields(client, query, override):
    assert_error(client.post("/api/signup", json={**VALID_SIGNUP, **override}), 400)
    assert query("SELECT COUNT(*) FROM users")[0][0] == 2  # only the seeded accounts


@pytest.mark.parametrize("body", [None, b"{not json", b"[1, 2]"])
def test_signup_rejects_missing_or_malformed_body(client, body):
    assert_error(client.post("/api/signup", data=body, content_type="application/json"), 400)


def test_signup_duplicate_email_is_409(client, query):
    assert_error(client.post("/api/signup", json={**VALID_SIGNUP, "email": DEMO_USER[0]}), 409)
    assert client.post("/api/signup", json=VALID_SIGNUP).status_code == 201
    assert_error(client.post("/api/signup", json=VALID_SIGNUP), 409)
    assert query("SELECT COUNT(*) FROM user_profiles WHERE email = ?", VALID_SIGNUP["email"])[0][0] == 1


# --- login --------------------------------------------------------------------

def test_shopper_login(client):
    response = client.post("/api/login", json={"email": DEMO_USER[0], "password": DEMO_USER[1]})
    assert response.status_code == 200
    body = response.get_json()
    assert body["access_token"] and body["name"] == "Demo Shopper" and body["is_manager"] is False


def test_manager_login_reports_manager(client):
    response = client.post("/api/login", json={"email": "manager@grocery.app", "password": "manager1234"})
    assert response.status_code == 200
    assert response.get_json()["is_manager"] is True


def test_login_wrong_password_and_unknown_user_look_the_same(client):
    wrong = assert_error(client.post("/api/login", json={"email": DEMO_USER[0], "password": "nope"}), 401)
    unknown = assert_error(client.post("/api/login", json={"email": "ghost@example.com", "password": "x"}), 401)
    assert wrong == unknown


@pytest.mark.parametrize("body", [None, {}, {"email": DEMO_USER[0]}, {"password": "x"},
                                  {"email": DEMO_USER[0], "password": 123}])
def test_login_missing_fields_is_400(client, body):
    assert_error(client.post("/api/login", json=body), 400)


def test_login_accepts_legacy_sha256_password(client, execute):
    import hashlib
    execute("UPDATE users SET password = ? WHERE email = ?",
            hashlib.sha256(b"legacy-pass").hexdigest(), DEMO_USER[0])
    assert client.post("/api/login", json={"email": DEMO_USER[0], "password": "legacy-pass"}).status_code == 200
    assert_error(client.post("/api/login", json={"email": DEMO_USER[0], "password": "demo1234"}), 401)


def test_admin_login(client):
    response = client.post("/api/admin/login", json={"email": ADMIN[0], "password": ADMIN[1]})
    assert response.status_code == 200
    assert response.get_json()["access_token"]
    assert_error(client.post("/api/admin/login", json={"email": ADMIN[0], "password": "wrong"}), 401)
    assert_error(client.post("/api/admin/login", json={}), 400)
    assert_error(client.post("/api/admin/login", json={"email": ADMIN[0]}), 400)
    # Shopper credentials don't work on the admin endpoint.
    assert_error(client.post("/api/admin/login", json={"email": DEMO_USER[0], "password": DEMO_USER[1]}), 401)


# --- tokens -------------------------------------------------------------------

@pytest.mark.parametrize("method,path", [
    ("GET", "/api/shopping_cart"),
    ("GET", "/api/dashboard"),
    ("POST", "/api/add_to_cart"),
    ("POST", "/api/shopping_cart/checkout"),
    ("POST", "/api/apply_manager"),
    ("GET", "/api/manager/dashboard"),
    ("POST", "/api/manager/add_product"),
    ("GET", "/api/manager/prepare_report"),
    ("GET", "/api/admin/manager_requests"),
    ("POST", "/api/admin/accept_manager"),
])
def test_protected_routes_require_token(client, method, path):
    assert_error(client.open(path, method=method, json={}), 401)


@pytest.mark.parametrize("header", [
    "Bearer garbage.token.value",
    "Bearer ",
    "Token abc",
])
def test_invalid_token_is_json_401(client, header):
    assert_error(client.get("/api/shopping_cart", headers={"Authorization": header}), 401)


def test_token_signed_with_other_key_is_rejected(app, client):
    import jwt as pyjwt
    forged = pyjwt.encode({"sub": DEMO_USER[0], "role": "admin", "type": "access", "fresh": False,
                           "jti": "x", "iat": 0, "nbf": 0, "exp": 4102444800},
                          "some-other-secret-key-of-sufficient-length", algorithm="HS256")
    assert_error(client.get("/api/admin/manager_requests", headers=bearer(forged)), 401)


def test_expired_token_is_json_401(app, client):
    from datetime import timedelta
    with app.app_context():
        token = create_access_token(identity=DEMO_USER[0], expires_delta=timedelta(seconds=-10))
    assert "expired" in assert_error(client.get("/api/shopping_cart", headers=bearer(token)), 401).lower()


# --- roles --------------------------------------------------------------------

@pytest.mark.parametrize("method,path,body", [
    ("GET", "/api/manager/dashboard?is_manager=true", None),
    ("GET", "/api/manager/prepare_report?is_manager=true", None),
    ("POST", "/api/manager/add_product?is_manager=true",
     {"product_name": "X", "category": "Dairy", "quantity": 1, "price": 1, "unit": "kg",
      "manufacture_date": "2026-01-01", "expiry_date": "2026-02-01", "is_manager": True}),
    ("POST", "/api/manager/delete_product?is_manager=true", {"product_id": 1, "is_manager": True}),
    ("POST", "/api/manager/categories/add_category?is_admin=true", {"category_name": "X", "role": "admin"}),
    ("GET", "/api/admin/manager_requests?is_admin=true", None),
    ("POST", "/api/admin/accept_manager", {"email": DEMO_USER[0]}),
])
def test_shopper_cannot_use_manager_or_admin_routes(client, shopper_token, query, method, path, body):
    assert_error(client.open(path, method=method, json=body, headers=bearer(shopper_token)), 403)
    assert query("SELECT COUNT(*) FROM products")[0][0] == 14


def test_manager_cannot_use_admin_routes(client, manager_token):
    headers = bearer(manager_token)
    assert_error(client.get("/api/admin/manager_requests", headers=headers), 403)
    assert_error(client.post("/api/manager/categories/add_category", json={"category_name": "X"}, headers=headers), 403)
    assert_error(client.post("/api/manager/categories/delete_category", json={"categoryID": 1}, headers=headers), 403)
    assert_error(client.post("/api/admin/accept_manager", json={"email": "a@b.co"}, headers=headers), 403)
    assert_error(client.post("/api/admin/reject_manager", json={"email": "a@b.co"}, headers=headers), 403)


def test_role_is_checked_against_database_not_token(app, client, execute, manager_token):
    # Revoking manager status takes effect immediately, even with an old token.
    execute("UPDATE store_manager SET manager_status = 'Denied' WHERE email = 'manager@grocery.app'")
    assert_error(client.get("/api/manager/dashboard", headers=bearer(manager_token)), 403)
    # A shopper token with a forged "manager" role claim gets nothing either.
    with app.app_context():
        token = mint_token(DEMO_USER[0], role="manager")
    assert_error(client.get("/api/manager/dashboard", headers=bearer(token)), 403)


# --- rate limiting ----------------------------------------------------------------

RATE_LIMIT_SCRIPT = textwrap.dedent("""
    import app
    client = app.app.test_client()
    statuses = [client.post("/api/login", json={"email": "demo@grocery.app", "password": "wrong"}).status_code
                for _ in range(4)]
    blocked = client.post("/api/login", json={"email": "demo@grocery.app", "password": "demo1234"})
    signup = [client.post("/api/signup", json={}).status_code for _ in range(4)]
    print(statuses, blocked.status_code, blocked.get_json(), signup)
    assert statuses == [401, 401, 401, 429], statuses
    assert blocked.status_code == 429 and "error" in blocked.get_json()
    assert blocked.headers.get("Retry-After")
    assert signup == [400, 400, 400, 429], signup
""")


def test_auth_endpoints_are_rate_limited(tmp_path):
    """Runs in a fresh interpreter: the limiter is configured at import time."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = {k: v for k, v in os.environ.items() if not k.startswith(("RATELIMIT", "AUTH_RATE"))}
    env.update(RATELIMIT_ENABLED="true", AUTH_RATE_LIMIT="3 per minute", APP_ENV="development",
               DATABASE_PATH=str(tmp_path / "rl.db"), LOG_LEVEL="ERROR")
    result = subprocess.run([sys.executable, "-c", RATE_LIMIT_SCRIPT], cwd=root, env=env,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
