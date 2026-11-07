import pytest

from helpers import SPRITE, assert_error


def names(products):
    return sorted(p["name"] for p in products)


def search(client, **body):
    response = client.post("/api/search", json=body)
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def test_user_dashboard_lists_products_with_stock(client):
    response = client.get("/api/user_dashboard")
    assert response.status_code == 200
    products = response.get_json()["products"]
    assert len(products) == 14
    apple = next(row for row in products if row[1] == "Apple")
    assert apple[-1] == 60  # inventory quantity is the last column


def test_categories(client):
    response = client.get("/api/getCategories")
    assert response.status_code == 200
    assert [row[1] for row in response.get_json()] == [
        "Fruits & Vegetables", "Cold Drinks", "Dairy", "Poultry", "Snacks"]


def test_category_products_include_stock(client, execute):
    execute("UPDATE inventory SET quantity = 3 WHERE productID = ?", SPRITE)
    response = client.get("/api/category/2")
    assert response.status_code == 200
    rows = response.get_json()
    assert sorted(row[1] for row in rows) == ["Pepsi", "Sprite"]
    sprite = next(row for row in rows if row[1] == "Sprite")
    assert len(sprite) == 12 and sprite[11] == 3


def test_unknown_category_is_404(client):
    assert_error(client.get("/api/category/999"), 404)


def test_search_by_product_name(client):
    body = search(client, search_query="  APPLE ")
    assert names(body["products"]) == ["Apple", "Pineapple"]
    assert all("stock" in p for p in body["products"])


def test_search_without_body_returns_everything(client):
    response = client.post("/api/search")
    assert response.status_code == 200
    assert len(response.get_json()["products"]) == 14


def test_search_no_results(client):
    assert search(client, search_query="zzzz") == {"no_results": True}


def test_search_falls_back_to_category(client):
    body = search(client, search_query="dairy", min_price=0, max_price=0, min_manufacture_date=0,
                  max_manufacture_date=0, min_expiry_date="", max_expiry_date="", exclude_out_of_stock=True)
    assert [row[1] for row in body["category_results"]] == ["Dairy"]
    assert names(body["products_in_category"]) == ["Milk", "Paneer"]


def test_category_search_applies_filters(client, execute):
    execute("UPDATE inventory SET quantity = 0 WHERE productID = (SELECT productID FROM products WHERE name='Milk')")
    body = search(client, search_query="dairy", exclude_out_of_stock=True)
    assert names(body["products_in_category"]) == ["Paneer"]
    body = search(client, search_query="dairy", min_price=1000)
    assert body["no_results"] is True and "category_results" in body


def test_search_price_filters(client):
    assert names(search(client, search_query="", min_price=100, max_price="200")["products"]) == [
        "Apple", "Strawberry"]
    assert names(search(client, search_query="", max_price=10)["products"]) == ["Egg", "Munch"]


def test_search_excludes_out_of_stock(client, execute):
    execute("UPDATE inventory SET quantity = 0 WHERE productID = ?", SPRITE)
    assert names(search(client, search_query="sprite")["products"]) == ["Sprite"]
    assert search(client, search_query="sprite", exclude_out_of_stock=True) == {"no_results": True}


def test_search_date_filters(client, execute):
    execute("UPDATE products SET manufacture_date = '2020-01-01', expiry_date = '2020-06-01' WHERE name = 'Egg'")
    assert names(search(client, search_query="", max_manufacture_date="2021-01-01")["products"]) == ["Egg"]
    assert names(search(client, search_query="", max_expiry_date="2020-12-31")["products"]) == ["Egg"]
    assert "Egg" not in names(search(client, search_query="", min_expiry_date="2021-01-01")["products"])
    assert "Egg" not in names(search(client, search_query="", min_manufacture_date="2021-01-01")["products"])


@pytest.mark.parametrize("body", [
    {"search_query": "a", "min_price": "abc"},
    {"search_query": "a", "max_price": -1},
    {"search_query": "a", "min_price": 50, "max_price": 10},
    {"search_query": "a", "min_expiry_date": "2024-13-45"},
    {"search_query": "a", "max_manufacture_date": 12345},
    {"search_query": 42},
    [1, 2, 3],
])
def test_search_rejects_bad_filters(client, body):
    assert_error(client.post("/api/search", json=body), 400)
