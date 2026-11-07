import csv
import io

import pytest

from helpers import APPLE, BANANA, MILK, assert_error, bearer

PRODUCT = {"product_name": "Kiwi", "category": "Fruits & Vegetables", "quantity": 10, "price": 12.5,
           "unit": "kg", "manufacture_date": "2026-01-01", "expiry_date": "2026-02-01"}


def manager_products(client, token):
    response = client.get("/api/manager/dashboard", headers=bearer(token))
    assert response.status_code == 200
    return {p["product_name"]: p for c in response.get_json()["categories"] for p in c["products"]}


def categories(client, token):
    response = client.get("/api/manager/dashboard", headers=bearer(token))
    return {c["category_name"]: c for c in response.get_json()["categories"]}


# --- dashboard ----------------------------------------------------------------

def test_manager_dashboard_for_manager_and_admin(client, manager_token, admin_token):
    for token in (manager_token, admin_token):
        cats = categories(client, token)
        assert set(cats) == {"Fruits & Vegetables", "Cold Drinks", "Dairy", "Poultry", "Snacks"}
        apple = cats["Fruits & Vegetables"]["products"][0]
        assert apple["product_name"] == "Apple" and apple["quantity"] == 60


def test_manager_dashboard_cache_is_per_user(client, manager_token, shopper_token):
    assert client.get("/api/manager/dashboard", headers=bearer(manager_token)).status_code == 200
    assert_error(client.get("/api/manager/dashboard", headers=bearer(shopper_token)), 403)


# --- product CRUD -------------------------------------------------------------

@pytest.mark.parametrize("token_name", ["manager_token", "admin_token"])
def test_add_product(client, request, token_name, query):
    token = request.getfixturevalue(token_name)
    response = client.post("/api/manager/add_product", json=PRODUCT, headers=bearer(token))
    assert response.status_code == 201
    kiwi = manager_products(client, token)["Kiwi"]
    assert (kiwi["price"], kiwi["quantity"], kiwi["unit"]) == (12.5, 10, "kg")
    assert (kiwi["manufacture_date"], kiwi["expiry_date"]) == ("2026-01-01", "2026-02-01")
    assert query("SELECT categoryID FROM products WHERE name = 'Kiwi'") == [(1,)]
    # Shows up in the public catalog straight away (cache cleared).
    names = [row[1] for row in client.get("/api/user_dashboard").get_json()["products"]]
    assert "Kiwi" in names


@pytest.mark.parametrize("override,status", [
    ({"price": -1}, 400),
    ({"price": 0}, 400),
    ({"price": "abc"}, 400),
    ({"price": True}, 400),
    ({"quantity": "x"}, 400),
    ({"quantity": -5}, 400),
    ({"product_name": " "}, 400),
    ({"unit": None}, 400),
    ({"manufacture_date": ""}, 400),
    ({"expiry_date": "garbage"}, 400),
    ({"expiry_date": "2026-13-45"}, 400),
    ({"expiry_date": 20260201}, 400),
    ({"expiry_date": "2025-12-31"}, 400),  # before manufacture date
    ({"category": "Nope"}, 404),
])
def test_add_product_validation(client, manager_token, query, override, status):
    assert_error(client.post("/api/manager/add_product", json={**PRODUCT, **override},
                             headers=bearer(manager_token)), status)
    assert query("SELECT COUNT(*) FROM products")[0][0] == 14


def test_add_product_requires_body(client, manager_token):
    assert_error(client.post("/api/manager/add_product", headers=bearer(manager_token)), 400)


def test_add_product_accepts_zero_stock_and_string_numbers(client, manager_token):
    body = {**PRODUCT, "quantity": "0", "price": "9.99"}
    assert client.post("/api/manager/add_product", json=body, headers=bearer(manager_token)).status_code == 201
    kiwi = manager_products(client, manager_token)["Kiwi"]
    assert (kiwi["quantity"], kiwi["price"]) == (0, 9.99)


def test_edit_product(client, manager_token, query):
    body = {**PRODUCT, "product_id": str(BANANA), "price": "15", "quantity": "7", "category": "Snacks"}
    response = client.post("/api/manager/edit_product", json=body, headers=bearer(manager_token))
    assert response.status_code == 200
    assert query("SELECT name, price, categoryID FROM products WHERE productID = ?", BANANA) == [("Kiwi", 15.0, 5)]
    assert query("SELECT quantity FROM inventory WHERE productID = ?", BANANA) == [(7,)]


def test_edit_product_recreates_missing_inventory_row(client, manager_token, query, execute):
    execute("DELETE FROM inventory WHERE productID = ?", BANANA)
    body = {**PRODUCT, "product_id": BANANA, "quantity": 4}
    assert client.post("/api/manager/edit_product", json=body, headers=bearer(manager_token)).status_code == 200
    assert query("SELECT quantity FROM inventory WHERE productID = ?", BANANA) == [(4,)]


def test_edit_product_errors(client, manager_token, shopper_token):
    url = "/api/manager/edit_product"
    assert_error(client.post(url, json={**PRODUCT, "product_id": 9999}, headers=bearer(manager_token)), 404)
    assert_error(client.post(url, json=PRODUCT, headers=bearer(manager_token)), 400)
    assert_error(client.post(url, json={**PRODUCT, "product_id": APPLE, "price": -2},
                             headers=bearer(manager_token)), 400)
    assert_error(client.post(url, json={**PRODUCT, "product_id": APPLE, "category": "Nope"},
                             headers=bearer(manager_token)), 404)
    assert_error(client.post(url, json={**PRODUCT, "product_id": APPLE}, headers=bearer(shopper_token)), 403)


def test_delete_product_removes_cart_and_inventory_rows(client, manager_token, shopper_token, query):
    client.post("/api/add_to_cart", json={"product_id": MILK, "quantity": 2}, headers=bearer(shopper_token))
    client.post("/api/add_to_cart", json={"product_id": APPLE, "quantity": 1}, headers=bearer(shopper_token))
    assert client.get("/api/shopping_cart", headers=bearer(shopper_token)).status_code == 200  # cache it

    response = client.post("/api/manager/delete_product", json={"product_id": MILK}, headers=bearer(manager_token))
    assert response.status_code == 200
    assert query("SELECT COUNT(*) FROM products WHERE productID = ?", MILK)[0][0] == 0
    assert query("SELECT COUNT(*) FROM inventory WHERE productID = ?", MILK)[0][0] == 0
    assert query("SELECT product_id FROM cart") == [(APPLE,)]
    cart = client.get("/api/shopping_cart", headers=bearer(shopper_token)).get_json()["cart"]
    assert [item["productID"] for item in cart] == [APPLE]
    # The category keeps existing even with one product left.
    assert "Dairy" in categories(client, manager_token)


def test_delete_product_errors(client, manager_token, shopper_token):
    url = "/api/manager/delete_product"
    assert_error(client.post(url, json={"product_id": 9999}, headers=bearer(manager_token)), 404)
    assert_error(client.post(url, json={}, headers=bearer(manager_token)), 400)
    assert_error(client.post(url, json={"product_id": APPLE}, headers=bearer(shopper_token)), 403)


# --- categories -----------------------------------------------------------------

def test_add_category_admin_only(client, admin_token, manager_token, query):
    url = "/api/manager/categories/add_category"
    assert_error(client.post(url, json={"category_name": "Bakery"}, headers=bearer(manager_token)), 403)
    assert_error(client.post(url, json={"category_name": " "}, headers=bearer(admin_token)), 400)
    assert_error(client.post(url, json={}, headers=bearer(admin_token)), 400)
    assert client.post(url, json={"category_name": "Bakery"}, headers=bearer(admin_token)).status_code == 201
    assert_error(client.post(url, json={"category_name": "bakery"}, headers=bearer(admin_token)), 409)
    assert_error(client.post(url, json={"category_name": "Dairy"}, headers=bearer(admin_token)), 409)
    assert query("SELECT COUNT(*) FROM categories WHERE category_name = 'Bakery'")[0][0] == 1
    # Public category list is refreshed (cache cleared on change).
    assert "Bakery" in [row[1] for row in client.get("/api/getCategories").get_json()]
    assert categories(client, admin_token)["Bakery"]["products"] == []


def test_delete_category_removes_products_inventory_and_cart(client, admin_token, manager_token,
                                                             shopper_token, query):
    client.post("/api/add_to_cart", json={"product_id": MILK, "quantity": 1}, headers=bearer(shopper_token))
    client.post("/api/add_to_cart", json={"product_id": APPLE, "quantity": 1}, headers=bearer(shopper_token))
    dairy_id = query("SELECT categoryID FROM categories WHERE category_name = 'Dairy'")[0][0]
    dairy_products = [r[0] for r in query("SELECT productID FROM products WHERE categoryID = ?", dairy_id)]

    url = "/api/manager/categories/delete_category"
    assert_error(client.post(url, json={"categoryID": dairy_id}, headers=bearer(manager_token)), 403)
    assert_error(client.post(url, json={"categoryID": 9999}, headers=bearer(admin_token)), 404)
    assert_error(client.post(url, json={"categoryID": "abc"}, headers=bearer(admin_token)), 400)
    assert client.post(url, json={"categoryID": dairy_id}, headers=bearer(admin_token)).status_code == 200

    marks = ",".join("?" * len(dairy_products))
    assert query("SELECT COUNT(*) FROM categories WHERE categoryID = ?", dairy_id)[0][0] == 0
    assert query(f"SELECT COUNT(*) FROM products WHERE productID IN ({marks})", *dairy_products)[0][0] == 0
    assert query(f"SELECT COUNT(*) FROM inventory WHERE productID IN ({marks})", *dairy_products)[0][0] == 0
    assert query("SELECT product_id FROM cart") == [(APPLE,)]
    assert_error(client.get(f"/api/category/{dairy_id}"), 404)


# --- manager requests ----------------------------------------------------------------

def test_manager_request_accept_flow(client, signup, login, admin_token, manager_token):
    token = login(signup("hopeful@example.com"), "secret123")
    assert_error(client.get("/api/apply_manager", headers=bearer(token)), 405)
    assert_error(client.get("/api/manager/dashboard", headers=bearer(token)), 403)

    assert client.post("/api/apply_manager", headers=bearer(token)).status_code == 200
    assert_error(client.post("/api/apply_manager", headers=bearer(token)), 409)
    assert client.get("/api/dashboard", headers=bearer(token)).get_json()["manager_status"] == "pending"

    requests = client.get("/api/admin/manager_requests", headers=bearer(admin_token))
    assert requests.status_code == 200
    assert [r["email"] for r in requests.get_json()["manager_requests"]] == ["hopeful@example.com"]
    assert requests.get_json()["manager_requests"][0]["name"] == "New Shopper"
    # The admin's cached response must not be served to a manager.
    assert_error(client.get("/api/admin/manager_requests", headers=bearer(manager_token)), 403)

    url = "/api/admin/accept_manager"
    assert_error(client.post(url, headers=bearer(admin_token)), 400)
    assert_error(client.post(url, json={"email": "nobody@example.com"}, headers=bearer(admin_token)), 404)
    assert client.post(url, json={"email": "hopeful@example.com"}, headers=bearer(admin_token)).status_code == 200
    assert_error(client.post("/api/admin/reject_manager", json={"email": "hopeful@example.com"},
                             headers=bearer(admin_token)), 404)

    # Same token now works on manager routes: the role is looked up per request.
    assert client.get("/api/manager/dashboard", headers=bearer(token)).status_code == 200
    assert_error(client.post("/api/apply_manager", headers=bearer(token)), 409)
    assert client.get("/api/admin/manager_requests", headers=bearer(admin_token)).get_json() == {
        "manager_requests": []}
    assert login("hopeful@example.com", "secret123")  # and login reports is_manager
    body = client.post("/api/login", json={"email": "hopeful@example.com", "password": "secret123"}).get_json()
    assert body["is_manager"] is True


def test_manager_request_reject_then_reapply(client, signup, login, admin_token):
    token = login(signup("hopeful@example.com"), "secret123")
    client.post("/api/apply_manager", headers=bearer(token))
    url = "/api/admin/reject_manager"
    assert client.post(url, json={"email": "hopeful@example.com"}, headers=bearer(admin_token)).status_code == 200
    assert_error(client.get("/api/manager/dashboard", headers=bearer(token)), 403)
    assert client.get("/api/dashboard", headers=bearer(token)).get_json()["manager_status"] == "Denied"
    # Re-applying after a denial is allowed.
    assert client.post("/api/apply_manager", headers=bearer(token)).status_code == 200


def test_existing_manager_cannot_apply(client, manager_token):
    assert "already" in assert_error(client.post("/api/apply_manager", headers=bearer(manager_token)), 409)


# --- CSV report ----------------------------------------------------------------

def test_report_requires_manager(client, shopper_token):
    assert_error(client.get("/api/manager/prepare_report"), 401)
    assert_error(client.get("/api/manager/prepare_report", headers=bearer(shopper_token)), 403)


def test_report_contents(client, shopper_token, manager_token, admin_token):
    for product_id, quantity in ((APPLE, 2), (MILK, 3)):
        client.post("/api/add_to_cart", json={"product_id": product_id, "quantity": quantity},
                    headers=bearer(shopper_token))
    assert client.post("/api/shopping_cart/checkout", headers=bearer(shopper_token)).status_code == 200
    client.post("/api/add_to_cart", json={"product_id": APPLE, "quantity": 1}, headers=bearer(shopper_token))
    assert client.post("/api/shopping_cart/checkout", headers=bearer(shopper_token)).status_code == 200

    for token in (manager_token, admin_token):
        response = client.get("/api/manager/prepare_report", headers=bearer(token))
        assert response.status_code == 200
        assert response.mimetype == "text/csv"
        assert "attachment" in response.headers["Content-Disposition"]
        rows = list(csv.reader(io.StringIO(response.get_data(as_text=True))))
        assert rows[0] == ["Product name", "Quantity sold", "Total amount"]
        assert sorted(rows[1:]) == [["Apple", "3", "540.0"], ["Milk", "3", "162.0"]]


def test_report_empty(client, manager_token):
    response = client.get("/api/manager/prepare_report", headers=bearer(manager_token))
    assert response.get_data(as_text=True).strip() == "Product name,Quantity sold,Total amount"
