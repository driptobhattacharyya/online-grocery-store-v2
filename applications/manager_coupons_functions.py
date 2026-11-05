"""Manager coupon administration, ported from the version 1 store."""

from applications.database import get_db
from applications.errors import AppError


def list_coupons():
    db = get_db()
    rows = db.execute(
        """
        SELECT c.coupon_code, c.discount_percentage, COUNT(u.user_email) AS usage_count
        FROM coupons c
        LEFT JOIN used_coupons u ON u.coupon_code = c.coupon_code
        GROUP BY c.coupon_code, c.discount_percentage
        ORDER BY c.coupon_code
        """
    ).fetchall()
    return [
        {
            "coupon_code": row["coupon_code"],
            "discount_percentage": row["discount_percentage"],
            "count": row["usage_count"],
        }
        for row in rows
    ]


def add_coupon(code, discount):
    normalized = (code or "").strip().upper()
    if not normalized or len(normalized) > 20 or not normalized.replace("-", "").isalnum():
        raise AppError("Coupon code must be 1-20 letters, numbers or hyphens.")
    try:
        percentage = float(discount)
    except (TypeError, ValueError) as exc:
        raise AppError("Discount percentage must be a number.") from exc
    if percentage <= 0 or percentage > 100:
        raise AppError("Discount percentage must be between 1 and 100.")
    db = get_db()
    existing = db.execute(
        "SELECT 1 FROM coupons WHERE coupon_code = ?", (normalized,)
    ).fetchone()
    if existing:
        raise AppError("Coupon code already exists.")
    db.execute(
        "INSERT INTO coupons (coupon_code, discount_percentage) VALUES (?, ?)",
        (normalized, percentage),
    )
    db.commit()
    return {"coupon_code": normalized, "discount_percentage": percentage}


def remove_coupon(code):
    normalized = (code or "").strip().upper()
    db = get_db()
    existing = db.execute(
        "SELECT 1 FROM coupons WHERE coupon_code = ?", (normalized,)
    ).fetchone()
    if not existing:
        raise AppError("Coupon not found.", 404)
    db.execute("DELETE FROM cart_coupons WHERE coupon_code = ?", (normalized,))
    db.execute("DELETE FROM used_coupons WHERE coupon_code = ?", (normalized,))
    db.execute("DELETE FROM coupons WHERE coupon_code = ?", (normalized,))
    db.commit()
