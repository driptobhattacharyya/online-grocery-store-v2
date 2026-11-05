import os

os.environ["SEED_DEMO_DATA"] = "0"
os.environ["CACHE_TYPE"] = "NullCache"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-with-32b-min"
os.environ["SECRET_KEY"] = "test-secret-key-with-32b-minimum"
os.environ["CORS_ORIGINS"] = "http://localhost:8080"
os.environ.pop("OPENAI_API_KEY", None)

import pytest

from app import app as flask_app
from applications.catalog import add_category, add_product
from applications.database import get_db
from applications.schema import reset_ready


@pytest.fixture
def app(tmp_path, monkeypatch):
    database = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(database))
    monkeypatch.setenv("REPORT_DIR", str(tmp_path / "reports"))
    monkeypatch.setenv("SEED_DEMO_DATA", "0")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    os.environ.pop("OPENAI_API_KEY", None)
    flask_app.config["DATABASE_PATH"] = str(database)
    flask_app.config["REPORT_DIR"] = str(tmp_path / "reports")
    reset_ready()
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def catalog(app):
    with app.app_context():
        from applications.schema import ensure_database

        ensure_database()
        add_category("Dairy")
        milk = add_product(
            {
                "product_name": "Milk",
                "category": "Dairy",
                "quantity": 10,
                "price": 100,
                "unit": "litre",
                "manufacture_date": "2026-10-01",
                "expiry_date": "2026-12-01",
                "description": "Fresh dairy milk, one litre.",
            }
        )
        bread = add_product(
            {
                "product_name": "Bread",
                "category": "Bakery",
                "quantity": 10,
                "price": 40,
                "unit": "loaf",
                "description": "Sliced sandwich bread.",
            }
        )
        egg = add_product(
            {
                "product_name": "Egg",
                "category": "Poultry",
                "quantity": 10,
                "price": 6,
                "unit": "piece",
                "description": "Farm eggs.",
            }
        )
    return {"milk": milk, "bread": bread, "egg": egg}


def signup(client, email, password="secret12", name="Tester", phone="9876543210"):
    response = client.post(
        "/api/signup",
        json={
            "email": email,
            "password": password,
            "name": name,
            "phoneNo": phone,
            "address": "1 Test Street",
        },
    )
    assert response.status_code == 201, response.get_json()
    return response


def promote(app, email, role):
    with app.app_context():
        db = get_db()
        db.execute("UPDATE users SET role = ? WHERE email = ?", (role, email.lower()))
        if role == "manager":
            db.execute(
                """
                INSERT INTO store_manager (email, manager_status) VALUES (?, 'approved')
                ON CONFLICT(email) DO UPDATE SET manager_status = 'approved'
                """,
                (email.lower(),),
            )
        db.commit()


def auth(client, app, email="shopper@example.com", role="customer", password="secret12"):
    signup(client, email, password=password, name=email.split("@")[0])
    if role != "customer":
        promote(app, email, role)
    response = client.post("/api/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.get_json()
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, response.get_json()
