from applications.database import get_db

PRODUCT_FIELDS = ("productID", "name", "manufacture_date", "expiry_date", "price",
                  "dynamic_price", "is_recommended", "categoryID", "unit")


def _filters(min_price, max_price, min_manufacture_date, max_manufacture_date,
             min_expiry_date, max_expiry_date, exclude_out_of_stock):
    clauses = ["price >= ?"]
    params = [min_price]
    if max_price is not None:
        clauses.append("price <= ?")
        params.append(max_price)
    for column, op, value in (("manufacture_date", ">=", min_manufacture_date),
                              ("manufacture_date", "<=", max_manufacture_date),
                              ("expiry_date", ">=", min_expiry_date),
                              ("expiry_date", "<=", max_expiry_date)):
        if value:
            clauses.append(f"{column} {op} ?")
            params.append(value)
    if exclude_out_of_stock:
        clauses.append("productID IN (SELECT productID FROM inventory WHERE quantity > 0)")
    return clauses, params


STOCK = "COALESCE((SELECT quantity FROM inventory WHERE inventory.productID = products.productID), 0)"


def _query_products(where, params):
    cursor = get_db().cursor()
    try:
        cursor.execute(
            f"SELECT {', '.join(PRODUCT_FIELDS)}, {STOCK} FROM products WHERE {' AND '.join(where)}", params
        )
        return [dict(zip(PRODUCT_FIELDS + ("stock",), row)) for row in cursor.fetchall()]
    finally:
        cursor.close()


def search_products_in_db(search_query, min_price=0, max_price=None,
                          min_manufacture_date='', max_manufacture_date='',
                          min_expiry_date='', max_expiry_date='', exclude_out_of_stock=False):
    clauses, params = _filters(min_price, max_price, min_manufacture_date, max_manufacture_date,
                               min_expiry_date, max_expiry_date, exclude_out_of_stock)
    return _query_products(["LOWER(name) LIKE ?"] + clauses, [f"%{search_query}%"] + params)


def search_categories_in_db(search_query):
    cursor = get_db().cursor()
    try:
        cursor.execute("SELECT * FROM categories WHERE LOWER(category_name) LIKE ?", (f"%{search_query}%",))
        return cursor.fetchall()
    finally:
        cursor.close()


def get_products_by_category_search(category_rows, min_price=0, max_price=None,
                                    min_manufacture_date='', max_manufacture_date='',
                                    min_expiry_date='', max_expiry_date='', exclude_out_of_stock=False):
    """Products in any of the matched categories, with the same filters applied."""
    category_ids = [row[0] for row in category_rows]
    if not category_ids:
        return []
    clauses, params = _filters(min_price, max_price, min_manufacture_date, max_manufacture_date,
                               min_expiry_date, max_expiry_date, exclude_out_of_stock)
    placeholders = ", ".join("?" for _ in category_ids)
    return _query_products([f"categoryID IN ({placeholders})"] + clauses, category_ids + params)
