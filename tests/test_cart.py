import pytest

from helpers import (
    APPLE, APPLE_PRICE, BANANA, BANANA_PRICE, MILK, MILK_PRICE, SPRITE, SPRITE_PRICE, SPRITE_STOCK,
    assert_error, bearer,
)


def add(client, token, product_id, quantity):
    return client.post("/api/add_to_cart", json={"product_id": product_id, "quantity": quantity},
                       headers=bearer(token))


def cart(client, token):
    response = client.get("/api/shopping_cart", headers=bearer(token))
    assert response.status_code == 200
    return {item["productID"]: item for item in response.get_json()["cart"]}


def stock(query, product_id):
    return query("SELECT quantity FROM inventory WHERE productID = ?", product_id)[0][0]


# --- add / update / delete -----------------------------------------------------------

def test_cart_starts_empty(client, shopper_token):
    assert cart(client, shopper_token) == {}


def test_add_update_delete(client, shopper_token):
    assert add(client, shopper_token, APPLE, 2).status_code == 200
    assert add(client, shopper_token, str(APPLE), "1").status_code == 200  # numeric strings accepted
    assert add(client, shopper_token, MILK, 3).status_code == 200
    items = cart(client, shopper_token)
    assert items[APPLE]["quantity"] == 3 and items[APPLE]["price"] == APPLE_PRICE
    assert items[MILK]["quantity"] == 3 and items[MILK]["name"] == "Milk"

    response = client.post("/api/shopping_cart/update_product", json={"product_id": APPLE, "quantity": 5},
                           headers=bearer(shopper_token))
    assert response.status_code == 200
    assert cart(client, shopper_token)[APPLE]["quantity"] == 5

    response = client.post("/api/shopping_cart/delete_product", json={"product_id": MILK},
                           headers=bearer(shopper_token))
    assert response.status_code == 200
    assert set(cart(client, shopper_token)) == {APPLE}
    assert_error(client.post("/api/shopping_cart/delete_product", json={"product_id": MILK},
                             headers=bearer(shopper_token)), 404)


def test_update_to_zero_removes_item(client, shopper_token):
    add(client, shopper_token, BANANA, 2)
    response = client.post("/api/shopping_cart/update_product", json={"product_id": BANANA, "quantity": 0},
                           headers=bearer(shopper_token))
    assert response.status_code == 200
    assert cart(client, shopper_token) == {}


@pytest.mark.parametrize("body", [
    None, {}, {"product_id": APPLE}, {"quantity": 1},
    {"product_id": APPLE, "quantity": 0}, {"product_id": APPLE, "quantity": -1},
    {"product_id": APPLE, "quantity": "abc"}, {"product_id": APPLE, "quantity": 1.5},
    {"product_id": APPLE, "quantity": True}, {"product_id": "x", "quantity": 1},
    {"product_id": -3, "quantity": 1},
])
def test_add_rejects_bad_input(client, shopper_token, query, body):
    assert_error(client.post("/api/add_to_cart", json=body, headers=bearer(shopper_token)), 400)
    assert query("SELECT COUNT(*) FROM cart")[0][0] == 0


def test_add_rejects_non_object_body(client, shopper_token):
    assert_error(client.post("/api/add_to_cart", json=[1, 2], headers=bearer(shopper_token)), 400)


def test_add_unknown_product_is_404(client, shopper_token):
    assert_error(add(client, shopper_token, 9999, 1), 404)


def test_add_beyond_stock_is_409(client, shopper_token):
    assert_error(add(client, shopper_token, SPRITE, SPRITE_STOCK + 1), 409)
    assert add(client, shopper_token, SPRITE, SPRITE_STOCK - 2).status_code == 200
    # Quantity already in the cart counts towards the stock check.
    message = assert_error(add(client, shopper_token, SPRITE, 3), 409)
    assert "already have" in message
    assert cart(client, shopper_token)[SPRITE]["quantity"] == SPRITE_STOCK - 2


def test_update_errors(client, shopper_token):
    headers = bearer(shopper_token)
    url = "/api/shopping_cart/update_product"
    assert_error(client.post(url, json={"product_id": BANANA, "quantity": 1}, headers=headers), 404)
    add(client, shopper_token, SPRITE, 1)
    assert_error(client.post(url, json={"product_id": SPRITE, "quantity": -3}, headers=headers), 400)
    assert_error(client.post(url, json={"product_id": SPRITE}, headers=headers), 400)
    assert_error(client.post(url, json={"product_id": SPRITE, "quantity": SPRITE_STOCK + 1}, headers=headers), 409)
    assert cart(client, shopper_token)[SPRITE]["quantity"] == 1


def test_delete_requires_product_id(client, shopper_token):
    assert_error(client.post("/api/shopping_cart/delete_product", headers=bearer(shopper_token)), 400)


def test_cart_routes_reject_get(client, shopper_token):
    for path in ("/api/add_to_cart", "/api/shopping_cart/update_product",
                 "/api/shopping_cart/delete_product", "/api/shopping_cart/checkout"):
        assert_error(client.get(path, headers=bearer(shopper_token)), 405)


# --- caching ----------------------------------------------------------------

def test_cart_cache_is_per_user(client, shopper_token, signup, login):
    other = login(signup("other@example.com"), "secret123")
    add(client, shopper_token, APPLE, 2)
    # Prime the cache for both users, then read again (served from cache).
    for _ in range(2):
        assert set(cart(client, shopper_token)) == {APPLE}
        assert cart(client, other) == {}
    add(client, other, BANANA, 1)
    assert set(cart(client, other)) == {BANANA}
    assert set(cart(client, shopper_token)) == {APPLE}


def test_cart_view_reflects_changes_immediately(client, shopper_token):
    assert cart(client, shopper_token) == {}  # cached empty response
    add(client, shopper_token, APPLE, 1)
    assert set(cart(client, shopper_token)) == {APPLE}


# --- checkout ----------------------------------------------------------------

def test_checkout_computes_total_on_server(client, shopper_token, query):
    add(client, shopper_token, APPLE, 2)
    add(client, shopper_token, MILK, 3)
    apple_stock, milk_stock = stock(query, APPLE), stock(query, MILK)

    response = client.post("/api/shopping_cart/checkout", json={"totalPrice": 1, "cart_items": []},
                           headers=bearer(shopper_token))
    assert response.status_code == 200
    body = response.get_json()
    expected = 2 * APPLE_PRICE + 3 * MILK_PRICE
    assert body["totalPrice"] == expected
    assert {(i["productID"], i["quantity"]) for i in body["cart_items"]} == {(APPLE, 2), (MILK, 3)}

    assert query("SELECT orderID, email, total_price FROM orders") == [
        (body["order_id"], "demo@grocery.app", expected)]
    assert sorted(query("SELECT product_name, quantity FROM order_items WHERE orderID = ?", body["order_id"])) == [
        ("Apple", 2), ("Milk", 3)]
    assert stock(query, APPLE) == apple_stock - 2 and stock(query, MILK) == milk_stock - 3
    assert cart(client, shopper_token) == {}

    dashboard = client.get("/api/dashboard", headers=bearer(shopper_token)).get_json()
    assert dashboard["user_orders"][0]["total_price"] == expected
    assert dashboard["user_orders"][0]["order_id"] == body["order_id"]


def test_checkout_uses_current_price(client, shopper_token, execute):
    add(client, shopper_token, BANANA, 2)
    execute("UPDATE products SET price = 50.5 WHERE productID = ?", BANANA)
    response = client.post("/api/shopping_cart/checkout", headers=bearer(shopper_token))
    assert response.get_json()["totalPrice"] == 101.0


def test_checkout_empty_cart_is_400(client, shopper_token, query):
    assert_error(client.post("/api/shopping_cart/checkout", headers=bearer(shopper_token)), 400)
    assert query("SELECT COUNT(*) FROM orders")[0][0] == 0


def test_checkout_is_atomic_when_stock_runs_out(client, shopper_token, query, execute):
    add(client, shopper_token, BANANA, 2)
    add(client, shopper_token, SPRITE, 5)
    execute("UPDATE inventory SET quantity = 3 WHERE productID = ?", SPRITE)  # stock drops under cart qty

    def snapshot():
        return (query("SELECT productID, quantity FROM inventory ORDER BY productID"),
                query("SELECT COUNT(*) FROM orders"), query("SELECT COUNT(*) FROM order_items"),
                query("SELECT product_id, quantity FROM cart ORDER BY product_id"))

    before = snapshot()
    message = assert_error(client.post("/api/shopping_cart/checkout", headers=bearer(shopper_token)), 409)
    assert "Sprite" in message
    assert snapshot() == before  # banana stock untouched, no order, cart intact

    execute("UPDATE inventory SET quantity = ? WHERE productID = ?", SPRITE_STOCK, SPRITE)
    response = client.post("/api/shopping_cart/checkout", headers=bearer(shopper_token))
    assert response.status_code == 200
    assert response.get_json()["totalPrice"] == 2 * BANANA_PRICE + 5 * SPRITE_PRICE
    assert stock(query, SPRITE) == SPRITE_STOCK - 5


def test_checkout_only_affects_buyers_cart(client, shopper_token, signup, login, query):
    other = login(signup("other@example.com"), "secret123")
    add(client, shopper_token, APPLE, 1)
    add(client, other, APPLE, 2)
    add(client, other, MILK, 1)

    response = client.post("/api/shopping_cart/checkout", headers=bearer(shopper_token))
    assert response.status_code == 200
    assert response.get_json()["totalPrice"] == APPLE_PRICE
    other_cart = cart(client, other)
    assert other_cart[APPLE]["quantity"] == 2 and other_cart[MILK]["quantity"] == 1
    assert query("SELECT email FROM orders") == [("demo@grocery.app",)]


def test_dashboard(client, shopper_token):
    response = client.get("/api/dashboard", headers=bearer(shopper_token))
    assert response.status_code == 200
    body = response.get_json()
    assert body["user_info"]["email"] == "demo@grocery.app"
    assert body["user_orders"] == []
    assert body["manager_status"] == "Not Applied"


def test_dashboard_without_profile_is_404(client, shopper_token, execute):
    execute("DELETE FROM user_profiles WHERE email = 'demo@grocery.app'")
    assert_error(client.get("/api/dashboard", headers=bearer(shopper_token)), 404)
