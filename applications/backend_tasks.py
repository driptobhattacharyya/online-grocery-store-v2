"""Celery jobs: daily reminder, monthly report, sales CSV, low-stock mail."""

import csv
import os
from datetime import date, timedelta

from celery import shared_task
from jinja2 import Template

from applications.database import get_db
from applications.inventory_alerts import (
    get_threshold,
    low_stock_email_body,
    low_stock_products,
    manager_emails,
)
from applications.mail_service import send_message


def _safe_send(to, subject, body):
    try:
        send_message(to, subject, body)
    except Exception as exc:
        print(f"Mail to {to} failed: {exc}")


def monthly_usage(email):
    db = get_db()
    orders = db.execute("SELECT order_date, total_price FROM orders WHERE email = ?", (email,)).fetchall()
    today = date.today()
    start = today.replace(day=1) - timedelta(days=1)
    start = start.replace(day=1)
    total = 0
    for order in orders:
        try:
            ordered_on = date.fromisoformat(order["order_date"])
        except (TypeError, ValueError):
            continue
        if ordered_on >= start:
            total += order["total_price"] or 0
    template = Template(
        "<html><body><p>Hi {{ email }},</p>"
        "<p>You have ordered a total of ₹{{ total }} in the past month.</p>"
        "<p>Thanks for shopping with us.</p></body></html>"
    )
    return template.render(email=email, total=round(total, 2))


@shared_task(ignore_result=True)
def daily_reminder():
    db = get_db()
    emails = db.execute("SELECT email FROM users WHERE role = 'customer'").fetchall()
    for row in emails:
        _safe_send(row["email"], "Your grocery store misses you", "<p>Hey, we've been missing you. The shelves are stocked.</p>")
    return "OK"


@shared_task(ignore_result=True)
def monthly_report():
    db = get_db()
    emails = db.execute("SELECT email FROM users WHERE role = 'customer'").fetchall()
    for row in emails:
        _safe_send(row["email"], "Your monthly grocery report", monthly_usage(row["email"]))
    return "OK"


@shared_task(ignore_result=True)
def low_stock_alert():
    threshold = get_threshold()
    products = low_stock_products(threshold)
    body = low_stock_email_body(products, threshold)
    for email in manager_emails():
        _safe_send(email, "Low stock alert", body)
    return "OK"


@shared_task(ignore_result=False)
def generate_sales_report():
    """Build the sales CSV off the request thread. The route only queues this."""
    from flask import current_app

    db = get_db()
    rows = db.execute(
        """
        SELECT product_name,
               SUM(quantity) AS total_quantity,
               SUM(quantity * IFNULL(unit_price, 0)) AS total_price
        FROM order_items
        GROUP BY product_name
        ORDER BY product_name
        """
    ).fetchall()
    report_dir = current_app.config.get("REPORT_DIR")
    os.makedirs(report_dir, exist_ok=True)
    path = os.path.join(report_dir, f"sales-{generate_sales_report.request.id}.csv")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Product name", "Quantity sold", "Total amount"])
        for row in rows:
            writer.writerow([row["product_name"], row["total_quantity"], row["total_price"]])
    return path
