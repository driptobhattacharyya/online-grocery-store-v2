"""Constants and assertion helpers shared by the test modules."""

DEMO_USER = ("demo@grocery.app", "demo1234")
DEMO_MANAGER = ("manager@grocery.app", "manager1234")
ADMIN = ("admin", "password")

# Seeded product ids (see applications/database.py DEMO_CATALOG).
APPLE, BANANA, SPRITE, MILK = 1, 2, 7, 8
APPLE_PRICE, BANANA_PRICE, SPRITE_PRICE, MILK_PRICE = 180.0, 48.0, 40.0, 54.0
SPRITE_STOCK = 8


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def assert_error(response, status):
    """Every API error is JSON ``{"error": "<message>"}`` with the right status."""
    assert response.status_code == status, (response.status_code, response.get_data(as_text=True))
    assert response.is_json, response.get_data(as_text=True)
    body = response.get_json()
    assert isinstance(body, dict) and isinstance(body.get("error"), str) and body["error"], body
    return body["error"]
