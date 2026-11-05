"""Cart, coupon application, and checkout.

Order totals are always computed here from database prices. A total sent by
the browser is ignored.
"""

from datetime import date

from applications.database import get_db
from applications.errors import AppError, parse_positive_int


def _money(value):
    return round(float(value) + 0.0, 2)


def _cart_rows(db, email):
    return db.execute(
        """
        SELECT p.productID, p.name, p.price, p.unit, c.quantity AS cart_quantity,
               IFNULL(i.quantity, 0) AS stock
        FROM cart c
        JOIN products p ON p.productID = c.product_id
        LEFT JOIN inventory i ON i.productID = p.productID
        WHERE c.email = ?
        ORDER BY p.name
        """,
        (email,),
    ).fetchall()


def _active_coupon(db, email):
    row = db.execute(
        "SELECT coupon_code FROM cart_coupons WHERE email = ?",
        (email,),
    ).fetchone()
    if not row:
        return None, 0
    coupon = db.execute(
        "SELECT coupon_code, discount_percentage FROM coupons WHERE coupon_code = ?",
        (row["coupon_code"],),
    ).fetchone()
    if not coupon:
        return None, 0
    used = db.execute(
        "SELECT 1 FROM used_coupons WHERE user_email = ? AND coupon_code = ?",
        (email, coupon["coupon_code"]),
    ).fetchone()
    if used:
        return None, 0
    return coupon["coupon_code"], float(coupon["discount_percentage"])


def cart_quote(email):
    db = get_db()
    rows = _cart_rows(db, email)
    items = []
    subtotal = 0.0
    for row in rows:
        line_total = _money(row["price"] * row["cart_quantity"])
        subtotal += row["price"] * row["cart_quantity"]
        items.append(
            {
                "productID": row["productID"],
                "name": row["name"],
                "price": row["price"],
                "unit": row["unit"],
                "quantity": row["cart_quantity"],
                "stock": row["stock"],
                "line_total": line_total,
            }
        )
    subtotal = _money(subtotal)
    coupon_code, discount_percentage = _active_coupon(db, email)
    discount_amount = _money(subtotal * discount_percentage / 100.0)
    total = _money(subtotal - discount_amount)
    return {
        "cart": items,
        "subtotal": subtotal,
        "coupon_code": coupon_code,
        "discount_percentage": discount_percentage,
        "discount_amount": discount_amount,
        "total": total,
    }


def fetch_cart_items_by_email(email):
    return cart_quote(email)["cart"]


def insert_cart_item(email, product_id, quantity):
    quantity = parse_positive_int(quantity)
    db = get_db()
    product = db.execute(
        """
        SELECT p.productID, IFNULL(i.quantity, 0) AS stock
        FROM products p
        LEFT JOIN inventory i ON i.productID = p.productID
        WHERE p.productID = ?
        """,
        (product_id,),
    ).fetchone()
    if not product:
        raise AppError("Product not found.", 404)
    existing = db.execute(
        "SELECT quantity FROM cart WHERE email = ? AND product_id = ?",
        (email, product_id),
    ).fetchone()
    new_quantity = quantity + (existing["quantity"] if existing else 0)
    if product["stock"] < new_quantity:
        raise AppError(
            f"Insufficient stock for this product. Available in stock: {product['stock']}."
        )
    if existing:
        db.execute(
            "UPDATE cart SET quantity = ? WHERE email = ? AND product_id = ?",
            (new_quantity, email, product_id),
        )
    else:
        db.execute(
            "INSERT INTO cart (email, product_id, quantity) VALUES (?, ?, ?)",
            (email, product_id, new_quantity),
        )
    db.commit()


def update_cart_item(email, product_id, quantity):
    quantity = parse_positive_int(quantity)
    db = get_db()
    stock_row = db.execute(
        "SELECT quantity FROM inventory WHERE productID = ?",
        (product_id,),
    ).fetchone()
    stock = stock_row["quantity"] if stock_row else 0
    if quantity > stock:
        raise AppError(f"Insufficient stock for this product. Available in stock: {stock}.")
    updated = db.execute(
        "UPDATE cart SET quantity = ? WHERE email = ? AND product_id = ?",
        (quantity, email, product_id),
    )
    if updated.rowcount == 0:
        raise AppError("That product is not in your cart.", 404)
    db.commit()


def delete_cart_item(email, product_id):
    db = get_db()
    db.execute(
        "DELETE FROM cart WHERE email = ? AND product_id = ?",
        (email, product_id),
    )
    db.commit()


def apply_coupon(email, coupon_code):
    """Attach a coupon to the cart. It is consumed only when checkout succeeds."""
    code = (coupon_code or "").strip().upper()
    if not code:
        raise AppError("Enter a coupon code.")
    db = get_db()
    coupon = db.execute(
        "SELECT coupon_code, discount_percentage FROM coupons WHERE coupon_code = ?",
        (code,),
    ).fetchone()
    if not coupon:
        raise AppError("No such coupon code available.")
    used = db.execute(
        "SELECT 1 FROM used_coupons WHERE user_email = ? AND coupon_code = ?",
        (email, code),
    ).fetchone()
    if used:
        raise AppError("You've already used this coupon code.")
    db.execute(
        """
        INSERT INTO cart_coupons (email, coupon_code) VALUES (?, ?)
        ON CONFLICT(email) DO UPDATE SET coupon_code = excluded.coupon_code
        """,
        (email, code),
    )
    db.commit()
    quote = cart_quote(email)
    quote["message"] = "Coupon code applied."
    return quote


def remove_coupon(email):
    db = get_db()
    db.execute("DELETE FROM cart_coupons WHERE email = ?", (email,))
    db.commit()
    return cart_quote(email)


def checkout_order(email):
    """Record an order and reduce stock for this user's cart only."""
    db = get_db()
    try:
        rows = _cart_rows(db, email)
        if not rows:
            raise AppError("Your cart is empty.")
        subtotal = 0.0
        for row in rows:
            if row["cart_quantity"] > row["stock"]:
                raise AppError(
                    f"Not enough inventory for '{row['name']}'. "
                    f"Available: {row['stock']}, requested: {row['cart_quantity']}."
                )
            subtotal += row["price"] * row["cart_quantity"]
        subtotal = _money(subtotal)
        coupon_code, discount_percentage = _active_coupon(db, email)
        discount_amount = _money(subtotal * discount_percentage / 100.0)
        total = _money(subtotal - discount_amount)
        cursor = db.execute(
            """
            INSERT INTO orders (email, order_date, total_price, coupon_code, discount_percentage)
            VALUES (?, ?, ?, ?, ?)
            """,
            (email, date.today().isoformat(), total, coupon_code, discount_percentage),
        )
        order_id = cursor.lastrowid
        items = []
        for row in rows:
            db.execute(
                """
                INSERT INTO order_items
                    (orderID, product_id, product_name, quantity, unit_price)
                VALUES (?, ?, ?, ?, ?)
                """,
                (order_id, row["productID"], row["name"], row["cart_quantity"], row["price"]),
            )
            db.execute(
                "UPDATE inventory SET quantity = quantity - ? WHERE productID = ?",
                (row["cart_quantity"], row["productID"]),
            )
            items.append(
                {
                    "productID": row["productID"],
                    "name": row["name"],
                    "quantity": row["cart_quantity"],
                    "price": row["price"],
                }
            )
        if coupon_code:
            db.execute(
                "INSERT INTO used_coupons (user_email, coupon_code) VALUES (?, ?)",
                (email, coupon_code),
            )
            db.execute("DELETE FROM cart_coupons WHERE email = ?", (email,))
        db.execute("DELETE FROM cart WHERE email = ?", (email,))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "success": "Checkout successful",
        "order_id": order_id,
        "cart_items": items,
        "subtotal": subtotal,
        "coupon_code": coupon_code,
        "discount_percentage": discount_percentage,
        "discount_amount": discount_amount,
        "total": total,
        "totalPrice": total,
    }
