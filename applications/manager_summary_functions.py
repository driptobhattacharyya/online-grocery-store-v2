"""Sales summary numbers for the manager charts.

The version 1 app drew these with matplotlib on the server. The API now
returns the same series as JSON and the Vue page draws them in the browser.

* Bar: units sold per product over the last 7 days (top 10).
* Pie: how many products sit in each category.
"""

from datetime import date, timedelta

from applications.database import get_db


def summary():
    db = get_db()
    end = date.today()
    start = end - timedelta(days=7)
    bar_rows = db.execute(
        """
        SELECT p.name AS product_name, SUM(oi.quantity) AS total_sales
        FROM products p
        JOIN order_items oi ON oi.product_id = p.productID
        JOIN orders o ON o.orderID = oi.orderID
        WHERE o.order_date >= ? AND o.order_date <= ?
        GROUP BY p.productID
        ORDER BY total_sales DESC
        LIMIT 10
        """,
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    pie_rows = db.execute(
        """
        SELECT c.category_name AS category_name, COUNT(p.productID) AS product_count
        FROM categories c
        LEFT JOIN products p ON p.categoryID = c.categoryID
        GROUP BY c.categoryID
        ORDER BY c.category_name
        """
    ).fetchall()
    return {
        "bar": [
            {"product": row["product_name"], "quantity": row["total_sales"]}
            for row in bar_rows
        ],
        "pie": [
            {"category": row["category_name"], "count": row["product_count"]}
            for row in pie_rows
        ],
        "window": {"start": start.isoformat(), "end": end.isoformat()},
    }
