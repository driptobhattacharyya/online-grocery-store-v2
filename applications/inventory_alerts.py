"""Low-stock listing and the body of the manager alert email."""

from applications.database import get_db
from applications.errors import AppError

THRESHOLD_KEY = "low_stock_threshold"


def get_threshold():
    db = get_db()
    row = db.execute(
        "SELECT value FROM app_settings WHERE key = ?", (THRESHOLD_KEY,)
    ).fetchone()
    if not row:
        return 10
    return int(row["value"])


def set_threshold(value):
    try:
        threshold = int(value)
    except (TypeError, ValueError) as exc:
        raise AppError("Threshold must be a whole number.") from exc
    if threshold < 0:
        raise AppError("Threshold must be zero or greater.")
    db = get_db()
    db.execute(
        """
        INSERT INTO app_settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (THRESHOLD_KEY, str(threshold)),
    )
    db.commit()
    return threshold


def low_stock_products(threshold=None):
    if threshold is None:
        threshold = get_threshold()
    db = get_db()
    rows = db.execute(
        """
        SELECT p.productID, p.name, p.unit, c.category_name, IFNULL(i.quantity, 0) AS quantity
        FROM products p
        JOIN categories c ON c.categoryID = p.categoryID
        LEFT JOIN inventory i ON i.productID = p.productID
        WHERE IFNULL(i.quantity, 0) <= ?
        ORDER BY quantity ASC, p.name
        """,
        (threshold,),
    ).fetchall()
    return [dict(row) for row in rows]


def manager_emails():
    db = get_db()
    rows = db.execute(
        "SELECT email FROM users WHERE role IN ('manager', 'admin')"
    ).fetchall()
    return [row["email"] for row in rows]


def low_stock_email_body(products, threshold):
    if not products:
        items = "<li>Nothing is at or below the threshold.</li>"
    else:
        items = "".join(
            f"<li>{product['name']} — {product['quantity']} {product['unit']} left</li>"
            for product in products
        )
    return (
        "<html><body>"
        f"<p>These products are at or below the low-stock threshold of {threshold}:</p>"
        f"<ul>{items}</ul>"
        "</body></html>"
    )
