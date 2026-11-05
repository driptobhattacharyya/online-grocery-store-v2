import os

from flask import jsonify, request, send_file
from flask_jwt_extended import create_access_token, get_jwt_identity

from applications.backend_tasks import generate_sales_report
from applications.caching import cache
from applications.catalog import (
    add_category,
    add_product,
    categories_with_products,
    delete_category,
    delete_product,
    update_product,
)
from applications.errors import AppError
from applications.inventory_alerts import get_threshold, low_stock_products, set_threshold
from applications.login_manager import login
from applications.manager_coupons_functions import add_coupon, list_coupons, remove_coupon
from applications.manager_summary_functions import summary
from applications.security import resolve_admin_email, roles_required
from applications.store_manager import approve_manager, deny_manager, get_manager_requests
from flask import current_app as app
from applications.controllers import _json, api_view


def _manager_payload():
    threshold = get_threshold()
    return {
        "categories": categories_with_products(),
        "low_stock": low_stock_products(threshold),
        "low_stock_threshold": threshold,
    }


@app.post("/api/admin/login")
@api_view
def manager_login_route():
    payload = _json()
    email = resolve_admin_email(payload.get("email") or payload.get("username"))
    user = login(email, payload.get("password"))
    if user["role"] != "admin":
        raise AppError("Invalid email or password.", 401)
    token = create_access_token(identity=user["email"], additional_claims={"role": user["role"]})
    return jsonify({"access_token": token, "role": user["role"]})


@app.get("/api/manager/dashboard")
@roles_required("admin", "manager")
@api_view
def manager_dashboard_route():
    return jsonify(_manager_payload())


@app.post("/api/manager/add_product")
@roles_required("admin", "manager")
@api_view
def add_product_route():
    add_product(_json())
    cache.clear()
    return jsonify({"success": "Product added to the category."})


@app.post("/api/manager/edit_product")
@roles_required("admin", "manager")
@api_view
def edit_product():
    update_product(_json())
    cache.clear()
    return jsonify({"success": "Product updated."})


@app.post("/api/manager/delete_product")
@roles_required("admin", "manager")
@api_view
def remove_product_route():
    delete_product(_json().get("product_id"))
    cache.clear()
    return jsonify({"success": "Product deleted."})


@app.post("/api/manager/categories")
@roles_required("admin")
@api_view
def add_category_route():
    add_category(_json().get("category_name"))
    cache.clear()
    return jsonify({"success": "Category added successfully."})


@app.delete("/api/manager/categories/<int:category_id>")
@roles_required("admin")
@api_view
def remove_category(category_id):
    delete_category(category_id)
    cache.clear()
    return jsonify({"success": "Category deleted successfully."})


@app.get("/api/manager/coupons")
@roles_required("admin", "manager")
@api_view
def coupons():
    return jsonify({"coupons": list_coupons()})


@app.post("/api/manager/coupons")
@roles_required("admin", "manager")
@api_view
def create_coupon():
    payload = _json()
    coupon = add_coupon(payload.get("coupon_code"), payload.get("discount_percentage"))
    return jsonify({"success": "Coupon added.", "coupon": coupon}), 201


@app.delete("/api/manager/coupons/<coupon_code>")
@roles_required("admin", "manager")
@api_view
def delete_coupon(coupon_code):
    remove_coupon(coupon_code)
    return jsonify({"success": "Coupon deleted."})


@app.get("/api/manager/summary")
@roles_required("admin", "manager")
@api_view
def manager_summary():
    return jsonify(summary())


@app.put("/api/manager/low-stock-threshold")
@roles_required("admin", "manager")
@api_view
def update_threshold():
    threshold = set_threshold(_json().get("threshold"))
    return jsonify(
        {
            "low_stock_threshold": threshold,
            "low_stock": low_stock_products(threshold),
        }
    )


@app.post("/api/manager/prepare_report")
@roles_required("admin", "manager")
@api_view
def prepare_report():
    task = generate_sales_report.delay()
    return jsonify({"task_id": task.id, "state": "PENDING"}), 202


@app.get("/api/manager/report/<task_id>")
@roles_required("admin", "manager")
@api_view
def report_status(task_id):
    celery_app = app.extensions["celery"]
    result = celery_app.AsyncResult(task_id)
    return jsonify({"task_id": task_id, "state": result.state})


@app.get("/api/manager/report/<task_id>/download")
@roles_required("admin", "manager")
@api_view
def report_download(task_id):
    celery_app = app.extensions["celery"]
    result = celery_app.AsyncResult(task_id)
    if result.state != "SUCCESS":
        raise AppError("Report is not ready.", 409)
    path = result.result
    report_dir = os.path.realpath(app.config["REPORT_DIR"])
    real_path = os.path.realpath(path)
    if not real_path.startswith(report_dir + os.sep):
        raise AppError("Report not found.", 404)
    return send_file(
        real_path,
        mimetype="text/csv",
        as_attachment=True,
        download_name="sales_report.csv",
    )


@app.get("/api/admin/manager_requests")
@roles_required("admin")
@api_view
def manager_requests():
    return jsonify({"manager_requests": get_manager_requests()})


@app.post("/api/admin/accept_manager")
@roles_required("admin")
@api_view
def accept_manager():
    approve_manager(_json().get("email"))
    cache.clear()
    return jsonify({"success": "Manager request accepted."})


@app.post("/api/admin/reject_manager")
@roles_required("admin")
@api_view
def reject_manager():
    deny_manager(_json().get("email"))
    cache.clear()
    return jsonify({"success": "Manager request rejected."})


# Silence unused import if a future route wants the caller email explicitly.
_ = (get_jwt_identity, request)
