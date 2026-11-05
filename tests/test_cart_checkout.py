from applications.database import get_db
from tests.conftest import auth


def _stock(app, product_id):
    with app.app_context():
        row = get_db().execute(
            "SELECT quantity FROM inventory WHERE productID = ?", (product_id,)
        ).fetchone()
        return row["quantity"]


def test_carts_are_isolated_between_users(client, app, catalog):
    ada, _ = auth(client, app, "ada@example.com")
    grace, _ = auth(client, app, "grace@example.com")
    added = client.post(
        "/api/add_to_cart",
        json={"product_id": catalog["milk"], "quantity": 2},
        headers=ada,
    )
    assert added.status_code == 200, added.get_json()

    ada_cart = client.get("/api/shopping_cart", headers=ada).get_json()
    grace_cart = client.get("/api/shopping_cart", headers=grace).get_json()
    assert [item["name"] for item in ada_cart["cart"]] == ["Milk"]
    assert grace_cart["cart"] == []
    assert grace_cart["total"] == 0


def test_checkout_reduces_only_this_users_stock_and_ignores_client_total(client, app, catalog):
    ada, _ = auth(client, app, "ada@example.com")
    grace, _ = auth(client, app, "grace@example.com")
    client.post(
        "/api/add_to_cart",
        json={"product_id": catalog["milk"], "quantity": 2},
        headers=ada,
    )
    client.post(
        "/api/add_to_cart",
        json={"product_id": catalog["milk"], "quantity": 3},
        headers=grace,
    )
    before = _stock(app, catalog["milk"])
    response = client.post(
        "/api/shopping_cart/checkout",
        json={"totalPrice": 1},
        headers=ada,
    )
    body = response.get_json()
    assert response.status_code == 200, body
    assert body["total"] == 200
    assert body["total"] != 1
    assert _stock(app, catalog["milk"]) == before - 2

    grace_cart = client.get("/api/shopping_cart", headers=grace).get_json()
    assert grace_cart["cart"][0]["quantity"] == 3
    grace_checkout = client.post("/api/shopping_cart/checkout", headers=grace)
    assert grace_checkout.status_code == 200
    assert _stock(app, catalog["milk"]) == before - 5
