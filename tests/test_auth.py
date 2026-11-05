import hashlib

import jwt

from applications.database import get_db
from tests.conftest import auth, signup


def test_signup_stores_salted_hash_not_sha256(client, app):
    signup(client, "ada@example.com", password="secret12")
    with app.app_context():
        row = get_db().execute(
            "SELECT password FROM users WHERE email = ?", ("ada@example.com",)
        ).fetchone()
    assert row["password"].startswith("pbkdf2:sha256:")
    assert row["password"] != hashlib.sha256(b"secret12").hexdigest()


def test_login_token_expires_and_protected_route_requires_it(client, app):
    headers, body = auth(client, app, "ada@example.com")
    payload = jwt.decode(body["access_token"], options={"verify_signature": False})
    assert payload["exp"] > payload["iat"]
    assert payload["role"] == "customer"

    missing = client.get("/api/shopping_cart")
    assert missing.status_code == 401

    cart = client.get("/api/shopping_cart", headers=headers)
    assert cart.status_code == 200
    assert cart.get_json()["cart"] == []


def test_customer_cannot_become_manager_via_query_param(client, app):
    headers, _body = auth(client, app, "ada@example.com")
    response = client.get("/api/manager/dashboard?is_manager=true", headers=headers)
    assert response.status_code == 403


def test_login_rejects_bad_password(client, app):
    signup(client, "ada@example.com")
    response = client.post(
        "/api/login", json={"email": "ada@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_mutating_routes_reject_get(client):
    assert client.get("/api/add_to_cart").status_code == 405
    assert client.get("/api/shopping_cart/checkout").status_code == 405
    assert client.get("/api/apply_manager").status_code == 405
    assert client.get("/api/manager/prepare_report").status_code == 405
