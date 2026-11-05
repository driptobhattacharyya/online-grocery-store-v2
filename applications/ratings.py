"""One review per customer per product, and only after they have bought it."""

from datetime import datetime, timezone

from applications.database import get_db
from applications.errors import AppError


def _has_purchased(db, email, product_id):
    row = db.execute(
        """
        SELECT 1
        FROM order_items oi
        JOIN orders o ON o.orderID = oi.orderID
        WHERE o.email = ? AND oi.product_id = ?
        """,
        (email, product_id),
    ).fetchone()
    return row is not None


def list_reviews(product_id):
    db = get_db()
    rows = db.execute(
        """
        SELECT r.rating, r.body, r.created_at, r.email, p.name
        FROM reviews r
        JOIN user_profiles p ON p.email = r.email
        WHERE r.product_id = ?
        ORDER BY r.created_at DESC
        """,
        (product_id,),
    ).fetchall()
    return [
        {
            "rating": row["rating"],
            "body": row["body"],
            "created_at": row["created_at"],
            "author": row["name"],
        }
        for row in rows
    ]


def upsert_review(email, product_id, rating, body):
    try:
        rating = int(rating)
    except (TypeError, ValueError) as exc:
        raise AppError("Rating must be a whole number from 1 to 5.") from exc
    if rating < 1 or rating > 5:
        raise AppError("Rating must be a whole number from 1 to 5.")
    db = get_db()
    product = db.execute(
        "SELECT productID FROM products WHERE productID = ?", (product_id,)
    ).fetchone()
    if not product:
        raise AppError("Product not found.", 404)
    if not _has_purchased(db, email, product_id):
        raise AppError("You can review a product after you have purchased it.", 403)
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    db.execute(
        """
        INSERT INTO reviews (email, product_id, rating, body, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(email, product_id) DO UPDATE SET
            rating = excluded.rating,
            body = excluded.body,
            created_at = excluded.created_at
        """,
        (email, product_id, rating, (body or "").strip(), created_at),
    )
    db.commit()
    return {"rating": rating, "body": (body or "").strip(), "created_at": created_at}
