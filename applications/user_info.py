from applications.database import get_db
from applications.errors import AppError


def fetch_order_history(email):
    db = get_db()
    orders = db.execute(
        """
        SELECT orderID, order_date, total_price, coupon_code, discount_percentage
        FROM orders
        WHERE email = ?
        ORDER BY order_date DESC, orderID DESC
        """,
        (email,),
    ).fetchall()
    history = []
    for order in orders:
        items = db.execute(
            """
            SELECT product_id, product_name, quantity, unit_price
            FROM order_items
            WHERE orderID = ?
            """,
            (order["orderID"],),
        ).fetchall()
        history.append(
            {
                "order_id": order["orderID"],
                "order_date": order["order_date"],
                "total_price": order["total_price"],
                "coupon_code": order["coupon_code"],
                "discount_percentage": order["discount_percentage"],
                "items": [
                    {
                        "product_id": item["product_id"],
                        "product_name": item["product_name"],
                        "quantity": item["quantity"],
                        "unit_price": item["unit_price"],
                    }
                    for item in items
                ],
            }
        )
    return history


def fetch_user_info(email):
    db = get_db()
    row = db.execute(
        "SELECT email, name, address, phone FROM user_profiles WHERE email = ?",
        (email,),
    ).fetchone()
    if not row:
        raise AppError("Profile not found.", 404)
    return {
        "email": row["email"],
        "name": row["name"],
        "address": row["address"],
        "phone_no": row["phone"],
    }
