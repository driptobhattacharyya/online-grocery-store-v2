from applications.database import get_db
from applications.http_errors import Conflict, NotFound


def add_category_to_db(category_name):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT 1 FROM categories WHERE LOWER(category_name) = LOWER(?)", (category_name,))
        if cursor.fetchone() is not None:
            raise Conflict("A category with this name already exists")
        cursor.execute("INSERT INTO categories (category_name) VALUES (?)", (category_name,))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


def remove_category_from_db(category_id):
    """Delete a category together with its products, their stock and cart rows."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT 1 FROM categories WHERE categoryID = ?", (category_id,))
        if cursor.fetchone() is None:
            raise NotFound("Category not found")
        products = "(SELECT productID FROM products WHERE categoryID = ?)"
        cursor.execute(f"DELETE FROM inventory WHERE productID IN {products}", (category_id,))
        cursor.execute(f"DELETE FROM cart WHERE product_id IN {products}", (category_id,))
        cursor.execute("DELETE FROM products WHERE categoryID = ?", (category_id,))
        cursor.execute("DELETE FROM categories WHERE categoryID = ?", (category_id,))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


def add_product_to_category_in_db(category_id, product_name, quantity, manufacture_date, expiry_date, price, unit):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO products (name, manufacture_date, expiry_date, price, unit, categoryID) VALUES (?, ?, ?, ?, ?, ?)",
            (product_name, manufacture_date, expiry_date, price, unit, category_id),
        )
        cursor.execute("INSERT INTO inventory (productID, quantity) VALUES (?, ?)", (cursor.lastrowid, quantity))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


def remove_product_from_db(product_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT 1 FROM products WHERE productID = ?", (product_id,))
        if cursor.fetchone() is None:
            raise NotFound("Product not found")
        cursor.execute("DELETE FROM inventory WHERE productID = ?", (product_id,))
        cursor.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE productID = ?", (product_id,))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


def get_categories_with_products_from_db():
    cursor = get_db().cursor()
    try:
        cursor.execute("""
        SELECT c.categoryID, c.category_name, p.productID, p.name AS product_name, p.price, p.unit, i.quantity, p.manufacture_date, p.expiry_date
        FROM categories AS c
        LEFT JOIN products AS p ON c.categoryID = p.categoryID
        LEFT JOIN inventory AS i ON p.productID = i.productID
        """)
        rows = cursor.fetchall()
    finally:
        cursor.close()

    categories_with_products = {}
    for (category_id, category_name, product_id, product_name, price, unit,
         quantity, manufacture_date, expiry_date) in rows:
        category = categories_with_products.setdefault(
            category_id, {'categoryID': category_id, 'category_name': category_name, 'products': []}
        )
        if product_id is None:  # category with no products (LEFT JOIN)
            continue
        category['products'].append({
            'productID': product_id, 'product_name': product_name, 'price': price, 'unit': unit,
            'quantity': quantity, 'manufacture_date': manufacture_date, 'expiry_date': expiry_date,
        })
    return list(categories_with_products.values())


def update_product_in_db(product_id, product_name, category_id, quantity, price, unit, manufacture_date, expiry_date):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE products SET name=?, manufacture_date=?, expiry_date=?, price=?, unit=?, categoryID=? WHERE productID=?",
            (product_name, manufacture_date, expiry_date, price, unit, category_id, product_id),
        )
        if cursor.rowcount == 0:
            raise NotFound("Product not found")
        cursor.execute("UPDATE inventory SET quantity=? WHERE productID=?", (quantity, product_id))
        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO inventory (productID, quantity) VALUES (?, ?)", (product_id, quantity))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()
