from tests.conftest import auth


def test_reviews_require_a_purchase_and_wishlist_moves_into_the_cart(client, app, catalog):
    shopper, _ = auth(client, app, "ada@example.com")
    blocked = client.post(
        f"/api/products/{catalog['milk']}/reviews",
        json={"rating": 5, "body": "Too soon"},
        headers=shopper,
    )
    assert blocked.status_code == 403

    client.post(
        "/api/wishlist",
        json={"product_id": catalog["bread"]},
        headers=shopper,
    )
    listed = client.get("/api/wishlist", headers=shopper).get_json()["wishlist"]
    assert [item["name"] for item in listed] == ["Bread"]

    moved = client.post(f"/api/wishlist/{catalog['bread']}/move-to-cart", headers=shopper)
    assert moved.status_code == 200
    assert client.get("/api/wishlist", headers=shopper).get_json()["wishlist"] == []
    cart = client.get("/api/shopping_cart", headers=shopper).get_json()
    assert cart["cart"][0]["name"] == "Bread"

    client.post("/api/shopping_cart/checkout", headers=shopper)
    saved = client.post(
        f"/api/products/{catalog['bread']}/reviews",
        json={"rating": 4, "body": "Soft crust"},
        headers=shopper,
    )
    assert saved.status_code == 201, saved.get_json()
    detail = client.get(f"/api/products/{catalog['bread']}").get_json()["product"]
    assert detail["average_rating"] == 4
    assert detail["review_count"] == 1
    assert detail["reviews"][0]["body"] == "Soft crust"

    updated = client.post(
        f"/api/products/{catalog['bread']}/reviews",
        json={"rating": 5, "body": "Even better toasted"},
        headers=shopper,
    )
    assert updated.status_code == 201
    detail = client.get(f"/api/products/{catalog['bread']}").get_json()["product"]
    assert detail["review_count"] == 1
    assert detail["average_rating"] == 5


def test_low_stock_threshold_and_summary_and_async_report(client, app, catalog):
    manager, _ = auth(client, app, "manager@example.com", role="manager")
    shopper, _ = auth(client, app, "ada@example.com")

    dashboard = client.get("/api/manager/dashboard", headers=manager).get_json()
    assert dashboard["low_stock_threshold"] == 10
    # Catalog fixture stocks every item at 10, so all of them are at the threshold.
    assert {item["name"] for item in dashboard["low_stock"]} >= {"Milk", "Bread", "Egg"}

    raised = client.put(
        "/api/manager/low-stock-threshold",
        json={"threshold": 0},
        headers=manager,
    )
    assert raised.status_code == 200
    assert raised.get_json()["low_stock"] == []

    denied = client.post("/api/manager/prepare_report", headers=shopper)
    assert denied.status_code == 403

    client.post(
        "/api/add_to_cart",
        json={"product_id": catalog["milk"], "quantity": 1},
        headers=shopper,
    )
    client.post("/api/shopping_cart/checkout", headers=shopper)

    summary = client.get("/api/manager/summary", headers=manager)
    assert summary.status_code == 200
    bar = summary.get_json()["bar"]
    assert bar[0]["product"] == "Milk"
    assert bar[0]["quantity"] == 1
    categories = {slice_["category"] for slice_ in summary.get_json()["pie"]}
    assert "Dairy" in categories

    queued = client.post("/api/manager/prepare_report", headers=manager)
    assert queued.status_code == 202
    task_id = queued.get_json()["task_id"]
    assert "Product name" not in queued.get_data(as_text=True)
    state = client.get(f"/api/manager/report/{task_id}", headers=manager).get_json()
    assert state["state"] == "SUCCESS"
    download = client.get(f"/api/manager/report/{task_id}/download", headers=manager)
    assert download.status_code == 200
    assert download.data.startswith(b"Product name")
    assert b"Milk" in download.data
