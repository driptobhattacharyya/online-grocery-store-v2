from applications.database import get_db
from tests.conftest import auth


def test_coupon_discount_is_server_side_and_single_use(client, app, catalog):
    manager, _ = auth(client, app, "manager@example.com", role="manager")
    created = client.post(
        "/api/manager/coupons",
        json={"coupon_code": "save20", "discount_percentage": 20},
        headers=manager,
    )
    assert created.status_code == 201, created.get_json()
    assert created.get_json()["coupon"]["coupon_code"] == "SAVE20"

    shopper, _ = auth(client, app, "ada@example.com")
    client.post(
        "/api/add_to_cart",
        json={"product_id": catalog["milk"], "quantity": 2},
        headers=shopper,
    )
    applied = client.post(
        "/api/shopping_cart/apply_coupon",
        json={"coupon_code": "save20"},
        headers=shopper,
    )
    quote = applied.get_json()
    assert applied.status_code == 200, quote
    assert quote["subtotal"] == 200
    assert quote["discount_percentage"] == 20
    assert quote["discount_amount"] == 40
    assert quote["total"] == 160

    checked = client.post(
        "/api/shopping_cart/checkout",
        json={"totalPrice": 9999},
        headers=shopper,
    )
    assert checked.status_code == 200, checked.get_json()
    assert checked.get_json()["total"] == 160

    with app.app_context():
        order = get_db().execute(
            "SELECT total_price, coupon_code FROM orders WHERE email = ?",
            ("ada@example.com",),
        ).fetchone()
    assert order["total_price"] == 160
    assert order["coupon_code"] == "SAVE20"

    client.post(
        "/api/add_to_cart",
        json={"product_id": catalog["bread"], "quantity": 1},
        headers=shopper,
    )
    reused = client.post(
        "/api/shopping_cart/apply_coupon",
        json={"coupon_code": "SAVE20"},
        headers=shopper,
    )
    assert reused.status_code == 400
    assert "already used" in reused.get_json()["error"].lower()

    missing = client.post(
        "/api/shopping_cart/apply_coupon",
        json={"coupon_code": "NOPE"},
        headers=shopper,
    )
    assert missing.status_code == 400


def test_customer_cannot_create_coupons_and_manager_can_delete(client, app):
    shopper, _ = auth(client, app, "ada@example.com")
    denied = client.post(
        "/api/manager/coupons",
        json={"coupon_code": "FREE", "discount_percentage": 10},
        headers=shopper,
    )
    assert denied.status_code == 403

    manager, _ = auth(client, app, "manager@example.com", role="manager")
    client.post(
        "/api/manager/coupons",
        json={"coupon_code": "WELCOME10", "discount_percentage": 10},
        headers=manager,
    )
    listed = client.get("/api/manager/coupons", headers=manager).get_json()["coupons"]
    assert listed[0]["coupon_code"] == "WELCOME10"
    deleted = client.delete("/api/manager/coupons/WELCOME10", headers=manager)
    assert deleted.status_code == 200
    assert client.get("/api/manager/coupons", headers=manager).get_json()["coupons"] == []
