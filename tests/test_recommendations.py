from applications.database import get_db
from applications.recommendations import recommend
from tests.conftest import auth


def _order(app, email, product_quantities):
    with app.app_context():
        db = get_db()
        total = 0
        lines = []
        for product_id, quantity in product_quantities:
            product = db.execute(
                "SELECT name, price FROM products WHERE productID = ?", (product_id,)
            ).fetchone()
            total += product["price"] * quantity
            lines.append((product_id, product["name"], quantity, product["price"]))
        cursor = db.execute(
            "INSERT INTO orders (email, order_date, total_price) VALUES (?, '2026-11-01', ?)",
            (email, total),
        )
        for product_id, name, quantity, price in lines:
            db.execute(
                """
                INSERT INTO order_items (orderID, product_id, product_name, quantity, unit_price)
                VALUES (?, ?, ?, ?, ?)
                """,
                (cursor.lastrowid, product_id, name, quantity, price),
            )
        db.commit()


def test_cart_recommendations_rank_copurchase_and_explain_why(client, app, catalog):
    for index in range(1, 3):
        auth(client, app, f"buyer{index}@example.com")
        _order(app, f"buyer{index}@example.com", [(catalog["milk"], 1), (catalog["bread"], 1)])
    auth(client, app, "buyer3@example.com")
    _order(app, "buyer3@example.com", [(catalog["milk"], 1), (catalog["egg"], 1)])

    with app.app_context():
        db = get_db()
        spoiled = db.execute(
            """
            INSERT INTO products (name, price, unit, categoryID, description, manufacture_date, expiry_date)
            VALUES ('Spoiled', 10, 'kg', (SELECT categoryID FROM categories LIMIT 1), '', '2026-01-01', '2026-02-01')
            """
        )
        spoiled_id = spoiled.lastrowid
        db.execute(
            "INSERT INTO inventory (productID, quantity) VALUES (?, 0)", (spoiled_id,)
        )
        db.commit()
    _order(app, "buyer1@example.com", [(catalog["milk"], 1), (spoiled_id, 1)])

    shopper, _ = auth(client, app, "ada@example.com")
    client.post(
        "/api/add_to_cart",
        json={"product_id": catalog["milk"], "quantity": 1},
        headers=shopper,
    )
    response = client.get("/api/recommendations/cart", headers=shopper)
    body = response.get_json()["recommendations"]
    names = [item["name"] for item in body]
    assert names[0] == "Bread"
    assert "Because you added Milk" in body[0]["reason"]
    assert "Egg" in names
    assert "Milk" not in names
    assert "Spoiled" not in names
    assert body[0]["strategy"] == "cooccurrence"

    with app.app_context():
        direct = recommend([catalog["milk"]], limit=2)
    assert [item["name"] for item in direct] == ["Bread", "Egg"]


def test_empty_cart_falls_back_to_popularity(client, app, catalog):
    auth(client, app, "buyer@example.com")
    _order(app, "buyer@example.com", [(catalog["egg"], 1)])
    _order(app, "buyer@example.com", [(catalog["egg"], 1)])
    _order(app, "buyer@example.com", [(catalog["bread"], 1)])
    shopper, _ = auth(client, app, "ada@example.com")
    response = client.get("/api/recommendations/cart", headers=shopper)
    names = [item["name"] for item in response.get_json()["recommendations"]]
    assert names[0] == "Egg"
    assert response.get_json()["recommendations"][0]["strategy"] == "popularity"
