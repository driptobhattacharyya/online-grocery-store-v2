from datetime import date

from applications.database import get_db
from applications.http_errors import BadRequest, Conflict, NotFound


def _stock(cursor, product_id):
    cursor.execute("SELECT quantity FROM inventory WHERE productID = ?", (product_id,))
    row = cursor.fetchone()
    return row[0] if row and row[0] is not None else 0


def product_exists(product_id):
    cursor = get_db().cursor()
    try:
        cursor.execute("SELECT 1 FROM products WHERE productID = ?", (product_id,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()


def _cart_quantity(cursor, email, product_id):
    cursor.execute("SELECT quantity FROM cart WHERE email = ? AND product_id = ?", (email, product_id))
    row = cursor.fetchone()
    return row[0] if row else None


def _begin_immediate(db, cursor):
    """Start a write transaction now, so a read-check-write sequence can't
    interleave with another request's (which would lose an update)."""
    if db.in_transaction:
        db.commit()
    cursor.execute("BEGIN IMMEDIATE")


def insert_cart_item(email, product_id, quantity):
    db = get_db()
    cursor = db.cursor()
    try:
        _begin_immediate(db, cursor)
        if not product_exists(product_id):
            raise NotFound("Product not found")
        existing = _cart_quantity(cursor, email, product_id)
        new_quantity = (existing or 0) + quantity
        in_stock = _stock(cursor, product_id)
        if new_quantity > in_stock:
            raise Conflict(
                f"Insufficient stock for this product. Available in stock: {in_stock}"
                + (f" (you already have {existing} in your cart)" if existing else "")
            )
        if existing is not None:
            cursor.execute("UPDATE cart SET quantity = ? WHERE email = ? AND product_id = ?",
                           (new_quantity, email, product_id))
        else:
            cursor.execute("INSERT INTO cart (email, product_id, quantity) VALUES (?, ?, ?)",
                           (email, product_id, quantity))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


def fetch_cart_items_by_email(email):
    cursor = get_db().cursor()
    try:
        cursor.execute('''SELECT products.name, products.price, cart.quantity, products.productID
                        FROM cart
                        INNER JOIN products ON cart.product_id = products.productID
                        WHERE cart.email = ?''', (email,))
        return [
            {"name": name, "price": price, "quantity": quantity, "productID": product_id}
            for name, price, quantity, product_id in cursor.fetchall()
        ]
    finally:
        cursor.close()


def delete_cart_item(email, product_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM cart WHERE email = ? AND product_id = ?", (email, product_id))
        if cursor.rowcount == 0:
            raise NotFound("This product is not in your cart")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


def update_cart_item(email, product_id, quantity):
    """Set the cart quantity for a product; a quantity of 0 removes it."""
    db = get_db()
    cursor = db.cursor()
    try:
        _begin_immediate(db, cursor)
        if _cart_quantity(cursor, email, product_id) is None:
            raise NotFound("This product is not in your cart")
        if quantity == 0:
            cursor.execute("DELETE FROM cart WHERE email = ? AND product_id = ?", (email, product_id))
        else:
            in_stock = _stock(cursor, product_id)
            if quantity > in_stock:
                raise Conflict(f"Insufficient stock for this product. Available in stock: {in_stock}")
            cursor.execute("UPDATE cart SET quantity = ? WHERE email = ? AND product_id = ?",
                           (quantity, email, product_id))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


def checkout_cart(email):
    """Turn the user's cart into an order in a single transaction.

    Checks and decrements inventory, records the order (with a total computed
    from current product prices, never from the client) and its items, and
    empties the cart. Any failure rolls back every step.
    Returns ``(order_id, items, total)``.
    """
    db = get_db()
    cursor = db.cursor()
    try:
        # Take the write lock up front so concurrent checkouts can't oversell.
        _begin_immediate(db, cursor)
        cursor.execute(
            '''SELECT p.productID, p.name, p.price, c.quantity, COALESCE(i.quantity, 0)
               FROM cart c
               JOIN products p ON c.product_id = p.productID
               LEFT JOIN inventory i ON i.productID = p.productID
               WHERE c.email = ?''',
            (email,),
        )
        rows = cursor.fetchall()
        if not rows:
            raise BadRequest("Your cart is empty")

        items = []
        total = 0.0
        for product_id, name, price, quantity, in_stock in rows:
            if quantity > in_stock:
                raise Conflict(f"Not enough stock for '{name}'. Available: {in_stock}, requested: {quantity}")
            cursor.execute(
                "UPDATE inventory SET quantity = quantity - ? WHERE productID = ? AND quantity >= ?",
                (quantity, product_id, quantity),
            )
            if cursor.rowcount != 1:
                raise Conflict(f"Not enough stock for '{name}'")
            total += price * quantity
            items.append({"productID": product_id, "name": name, "price": price, "quantity": quantity})

        total = round(total, 2)
        cursor.execute("INSERT INTO orders (email, order_date, total_price) VALUES (?, ?, ?)",
                       (email, date.today().isoformat(), total))
        order_id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO order_items (orderID, product_name, quantity) VALUES (?, ?, ?)",
            [(order_id, item["name"], item["quantity"]) for item in items],
        )
        cursor.execute("DELETE FROM cart WHERE email = ?", (email,))
        db.commit()
        return order_id, items, total
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()
