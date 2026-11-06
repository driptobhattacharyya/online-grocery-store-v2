from applications.database import get_db


def get_categories():
    cursor = get_db().cursor()
    try:
        cursor.execute("SELECT * FROM categories")
        return cursor.fetchall()
    finally:
        cursor.close()


def category_exists(category_id):
    cursor = get_db().cursor()
    try:
        cursor.execute("SELECT 1 FROM categories WHERE categoryID = ?", (category_id,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()


def get_category_id_by_name(category_name):
    cursor = get_db().cursor()
    try:
        cursor.execute("SELECT categoryID FROM categories WHERE category_name = ?", (category_name,))
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        cursor.close()


def get_products_by_category(category_id):
    """Same row shape as get_10_products: product columns, then inventoryId, productID, stock."""
    cursor = get_db().cursor()
    try:
        cursor.execute(
            "SELECT products.*, inventory.inventoryId, products.productID, COALESCE(inventory.quantity, 0) "
            "FROM products LEFT JOIN inventory ON products.productID = inventory.productID "
            "WHERE products.categoryID = ?",
            (category_id,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()


def get_10_products():
    """All products with their inventory row (the name is historical)."""
    cursor = get_db().cursor()
    try:
        cursor.execute("SELECT * FROM products INNER JOIN inventory ON products.productID = inventory.productID")
        return cursor.fetchall()
    finally:
        cursor.close()
