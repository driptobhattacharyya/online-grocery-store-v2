"""Per-customer wishlist. Moving an item adds it to the cart and removes it here."""

from datetime import datetime, timezone

from applications.cart_functions import insert_cart_item
from applications.database import get_db
from applications.errors import AppError


def list_wishlist(email):
    db = get_db()
    rows = db.execute(
        """
        SELECT p.productID, p.name, p.price, p.unit, IFNULL(i.quantity, 0) AS quantity,
               IFNULL(p.description, '') AS description
        FROM wishlist w
        JOIN products p ON p.productID = w.product_id
        LEFT JOIN inventory i ON i.productID = p.productID
        WHERE w.email = ?
        ORDER BY w.created_at DESC
        """,
        (email,),
    ).fetchall()
    return [dict(row) for row in rows]


def add_to_wishlist(email, product_id):
    db = get_db()
    product = db.execute(
        "SELECT productID FROM products WHERE productID = ?", (product_id,)
    ).fetchone()
    if not product:
        raise AppError("Product not found.", 404)
    db.execute(
        """
        INSERT INTO wishlist (email, product_id, created_at) VALUES (?, ?, ?)
        ON CONFLICT(email, product_id) DO NOTHING
        """,
        (email, product_id, datetime.now(timezone.utc).replace(microsecond=0).isoformat()),
    )
    db.commit()


def remove_from_wishlist(email, product_id):
    db = get_db()
    db.execute(
        "DELETE FROM wishlist WHERE email = ? AND product_id = ?",
        (email, product_id),
    )
    db.commit()


def move_to_cart(email, product_id, quantity=1):
    insert_cart_item(email, product_id, quantity)
    remove_from_wishlist(email, product_id)
