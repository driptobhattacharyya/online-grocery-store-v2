from applications.database import get_db


def fetch_order_history(email):
    cursor = get_db().cursor()
    try:
        cursor.execute(
            "SELECT orderID, order_date, total_price FROM orders WHERE email = ? "
            "ORDER BY order_date DESC, orderID DESC",
            (email,),
        )
        user_orders = []
        for order_id, order_date, total_price in cursor.fetchall():
            cursor.execute("SELECT product_name, quantity FROM order_items WHERE orderID = ?", (order_id,))
            items = [{'product_name': name, 'quantity': quantity} for name, quantity in cursor.fetchall()]
            user_orders.append({
                'order_id': order_id,
                'order_date': order_date,
                'items': items,
                'total_price': total_price,
            })
        return user_orders
    finally:
        cursor.close()


def fetch_user_info(email):
    """Return the user's profile as a dict, or None if there isn't one."""
    cursor = get_db().cursor()
    try:
        cursor.execute("SELECT email, name, address, phone FROM user_profiles WHERE email = ?", (email,))
        row = cursor.fetchone()
    finally:
        cursor.close()
    if row is None:
        return None
    email, name, address, phone_no = row
    return {'email': email, 'name': name, 'address': address, 'phone_no': phone_no}
