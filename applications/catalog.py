"""Product catalog queries shared by the storefront and the manager tools."""

from applications.database import get_db
from applications.errors import AppError, parse_non_negative_int

PRODUCT_SELECT = """
SELECT
    p.productID,
    p.name,
    p.manufacture_date,
    p.expiry_date,
    p.price,
    p.unit,
    p.categoryID,
    c.category_name,
    IFNULL(i.quantity, 0) AS quantity,
    IFNULL(p.description, '') AS description,
    ROUND(IFNULL(AVG(r.rating), 0), 2) AS average_rating,
    COUNT(r.reviewID) AS review_count
FROM products p
JOIN categories c ON c.categoryID = p.categoryID
LEFT JOIN inventory i ON i.productID = p.productID
LEFT JOIN reviews r ON r.product_id = p.productID
"""


def _product_dict(row):
    return {
        "productID": row["productID"],
        "name": row["name"],
        "manufacture_date": row["manufacture_date"],
        "expiry_date": row["expiry_date"],
        "price": row["price"],
        "unit": row["unit"],
        "categoryID": row["categoryID"],
        "category_name": row["category_name"],
        "quantity": row["quantity"],
        "description": row["description"],
        "average_rating": row["average_rating"],
        "review_count": row["review_count"],
    }


def _fetch_products(where="", params=(), order_by="p.name"):
    db = get_db()
    query = PRODUCT_SELECT
    if where:
        query += " WHERE " + where
    query += f" GROUP BY p.productID ORDER BY {order_by}"
    rows = db.execute(query, params).fetchall()
    return [_product_dict(row) for row in rows]


def list_products():
    return _fetch_products()


def get_product(product_id):
    products = _fetch_products("p.productID = ?", (product_id,))
    if not products:
        raise AppError("Product not found.", 404)
    return products[0]


def get_categories():
    db = get_db()
    rows = db.execute(
        "SELECT categoryID, category_name FROM categories ORDER BY category_name"
    ).fetchall()
    return [[row["categoryID"], row["category_name"]] for row in rows]


def products_by_category(category_id):
    return _fetch_products("p.categoryID = ?", (category_id,))


def _blank(value):
    return value in (None, "", 0, "0")


def search_products(payload):
    payload = payload or {}
    query_text = (payload.get("search_query") or "").strip().lower()
    clauses = ["LOWER(p.name) LIKE ?"]
    params = [f"%{query_text}%"]

    min_price = payload.get("min_price") or 0
    try:
        min_price = float(min_price)
    except (TypeError, ValueError):
        min_price = 0
    clauses.append("p.price >= ?")
    params.append(min_price)

    max_price = payload.get("max_price")
    if max_price not in (None, "", 0, "0"):
        clauses.append("p.price <= ?")
        params.append(float(max_price))

    for column, key in (
        ("p.manufacture_date >= ?", "min_manufacture_date"),
        ("p.manufacture_date <= ?", "max_manufacture_date"),
        ("p.expiry_date >= ?", "min_expiry_date"),
        ("p.expiry_date <= ?", "max_expiry_date"),
    ):
        if not _blank(payload.get(key)):
            clauses.append(column)
            params.append(str(payload.get(key)))

    if payload.get("exclude_out_of_stock"):
        clauses.append("IFNULL(i.quantity, 0) > 0")

    products = _fetch_products(" AND ".join(clauses), tuple(params))
    if products:
        return {"products": products}

    db = get_db()
    categories = db.execute(
        "SELECT categoryID, category_name FROM categories WHERE LOWER(category_name) LIKE ?",
        (f"%{query_text}%",),
    ).fetchall()
    if categories:
        category_products = _fetch_products("p.categoryID = ?", (categories[0]["categoryID"],))
        if category_products:
            return {
                "products": category_products,
                "category_results": [dict(row) for row in categories],
            }
    return {"products": [], "no_results": True}


def categories_with_products():
    grouped = {
        category_id: {"categoryID": category_id, "category_name": name, "products": []}
        for category_id, name in get_categories()
    }
    for product in list_products():
        grouped[product["categoryID"]]["products"].append(
            {
                "productID": product["productID"],
                "product_name": product["name"],
                "price": product["price"],
                "unit": product["unit"],
                "quantity": product["quantity"],
                "manufacture_date": product["manufacture_date"],
                "expiry_date": product["expiry_date"],
                "description": product["description"],
                "average_rating": product["average_rating"],
                "review_count": product["review_count"],
                "category_name": product["category_name"],
            }
        )
    return list(grouped.values())


def _category_id(db, category_name, create=False):
    row = db.execute(
        "SELECT categoryID FROM categories WHERE category_name = ?",
        (category_name,),
    ).fetchone()
    if row:
        return row["categoryID"]
    if not create:
        raise AppError("Category not found.")
    cursor = db.execute("INSERT INTO categories (category_name) VALUES (?)", (category_name,))
    return cursor.lastrowid


def add_category(category_name):
    name = (category_name or "").strip()
    if not name:
        raise AppError("Category name is required.")
    db = get_db()
    existing = db.execute(
        "SELECT 1 FROM categories WHERE LOWER(category_name) = LOWER(?)",
        (name,),
    ).fetchone()
    if existing:
        raise AppError("Category already exists.")
    db.execute("INSERT INTO categories (category_name) VALUES (?)", (name,))
    db.commit()


def delete_category(category_id):
    db = get_db()
    row = db.execute(
        "SELECT categoryID FROM categories WHERE categoryID = ?", (category_id,)
    ).fetchone()
    if not row:
        raise AppError("Category not found.", 404)
    product_ids = [
        item["productID"]
        for item in db.execute(
            "SELECT productID FROM products WHERE categoryID = ?", (category_id,)
        ).fetchall()
    ]
    for product_id in product_ids:
        _delete_product_rows(db, product_id)
    db.execute("DELETE FROM categories WHERE categoryID = ?", (category_id,))
    db.commit()


def add_product(payload):
    name = (payload.get("product_name") or "").strip()
    category = (payload.get("category") or "").strip()
    unit = (payload.get("unit") or "").strip()
    if not name or not category or not unit:
        raise AppError("Name, category and unit are required.")
    quantity = parse_non_negative_int(payload.get("quantity"), "quantity")
    try:
        price = float(payload.get("price"))
    except (TypeError, ValueError) as exc:
        raise AppError("Invalid price.") from exc
    if price < 0:
        raise AppError("Invalid price.")
    db = get_db()
    category_id = _category_id(db, category, create=True)
    cursor = db.execute(
        """
        INSERT INTO products
            (name, manufacture_date, expiry_date, price, unit, categoryID, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            payload.get("manufacture_date") or "",
            payload.get("expiry_date") or "",
            price,
            unit,
            category_id,
            (payload.get("description") or "").strip(),
        ),
    )
    db.execute(
        "INSERT INTO inventory (productID, quantity) VALUES (?, ?)",
        (cursor.lastrowid, quantity),
    )
    db.commit()
    return cursor.lastrowid


def update_product(payload):
    product_id = payload.get("product_id")
    name = (payload.get("product_name") or "").strip()
    category = (payload.get("category") or "").strip()
    unit = (payload.get("unit") or "").strip()
    if not product_id or not name or not category or not unit:
        raise AppError("Product id, name, category and unit are required.")
    quantity = parse_non_negative_int(payload.get("quantity"), "quantity")
    try:
        price = float(payload.get("price"))
    except (TypeError, ValueError) as exc:
        raise AppError("Invalid price.") from exc
    db = get_db()
    existing = db.execute(
        "SELECT productID FROM products WHERE productID = ?", (product_id,)
    ).fetchone()
    if not existing:
        raise AppError("Product not found.", 404)
    category_id = _category_id(db, category, create=False)
    description = payload.get("description")
    if description is None:
        current = db.execute(
            "SELECT description FROM products WHERE productID = ?", (product_id,)
        ).fetchone()
        description = current["description"] if current else ""
    db.execute(
        """
        UPDATE products
        SET name = ?, manufacture_date = ?, expiry_date = ?, price = ?, unit = ?, categoryID = ?,
            description = ?
        WHERE productID = ?
        """,
        (
            name,
            payload.get("manufacture_date") or "",
            payload.get("expiry_date") or "",
            price,
            unit,
            category_id,
            description,
            product_id,
        ),
    )
    db.execute(
        "UPDATE inventory SET quantity = ? WHERE productID = ?",
        (quantity, product_id),
    )
    db.commit()


def _delete_product_rows(db, product_id):
    db.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
    db.execute("DELETE FROM wishlist WHERE product_id = ?", (product_id,))
    db.execute("DELETE FROM reviews WHERE product_id = ?", (product_id,))
    db.execute("DELETE FROM inventory WHERE productID = ?", (product_id,))
    db.execute("DELETE FROM products WHERE productID = ?", (product_id,))


def delete_product(product_id):
    db = get_db()
    row = db.execute(
        "SELECT categoryID FROM products WHERE productID = ?", (product_id,)
    ).fetchone()
    if not row:
        raise AppError("Product not found.", 404)
    category_id = row["categoryID"]
    _delete_product_rows(db, product_id)
    remaining = db.execute(
        "SELECT COUNT(*) AS count FROM products WHERE categoryID = ?",
        (category_id,),
    ).fetchone()["count"]
    if remaining == 0:
        db.execute("DELETE FROM categories WHERE categoryID = ?", (category_id,))
    db.commit()
