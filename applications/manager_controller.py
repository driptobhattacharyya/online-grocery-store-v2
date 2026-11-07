"""Store-manager and admin API routes.

Errors are returned as ``{"error": "<message>"}`` with a matching HTTP status
(400 bad input, 401 bad credentials, 403 not allowed, 404 not found,
409 conflict, 500 unexpected).
"""
import csv
import io

from flask import Response, current_app as app, jsonify
from flask_jwt_extended import create_access_token, jwt_required

from applications.auth import is_admin, is_manager_or_admin, per_user_cache_key
from applications.caching import cache
from applications.cart_functions import product_exists
from applications.categories_functions import get_category_id_by_name
from applications.database import get_db, get_db_instance_id
from applications.http_errors import (
    BadRequest, Forbidden, NotFound, api_errors, iso_date, json_body, number, only_ok,
    positive_int, require_str,
)
from applications.login_manager import manager_login, normalize_email
from applications.manager_functions import (
    add_category_to_db, add_product_to_category_in_db, get_categories_with_products_from_db,
    remove_category_from_db, remove_product_from_db, update_product_in_db,
)
from applications.store_manager import approve_manager, deny_manager, get_manager_requests

NOT_AUTHORIZED = "You are not authorized to perform this action."


def _require_manager_or_admin():
    if not is_manager_or_admin():
        raise Forbidden(NOT_AUTHORIZED)


def _require_admin():
    if not is_admin():
        raise Forbidden(NOT_AUTHORIZED)


def _required_id(data, field):
    if data.get(field) in (None, ""):
        raise BadRequest(f"{field} is required")
    return positive_int(data.get(field), field)


def _product_fields(data):
    """Validate the body shared by add_product and edit_product."""
    product_name = require_str(data, 'product_name', "Product name")
    category_name = require_str(data, 'category', "Category")
    unit = require_str(data, 'unit', "Unit")
    for field, label in (('quantity', "Quantity"), ('price', "Price"),
                         ('manufacture_date', "Manufacture date"), ('expiry_date', "Expiry date")):
        if data.get(field) in (None, ""):
            raise BadRequest(f"{label} is required")
    quantity = positive_int(data.get('quantity'), "Quantity", allow_zero=True)
    price = number(data.get('price'), "Price")
    manufacture_date = iso_date(data.get('manufacture_date'), "Manufacture date")
    expiry_date = iso_date(data.get('expiry_date'), "Expiry date")
    if expiry_date < manufacture_date:
        raise BadRequest("Expiry date cannot be before the manufacture date")
    category_id = get_category_id_by_name(category_name)
    if category_id is None:
        raise NotFound(f"Category '{category_name}' not found")
    return dict(product_name=product_name, category_id=category_id, quantity=quantity, price=price,
                unit=unit, manufacture_date=manufacture_date, expiry_date=expiry_date)


@app.route('/api/admin/login', methods=['POST'])
@api_errors
def manager_login_route():  # admin login
    data = json_body()
    email = normalize_email(require_str(data, 'email', "Username"))
    password = data.get('password')
    if not isinstance(password, str) or not password:
        raise BadRequest("Password is required")
    manager_login(email, password)
    access_token = create_access_token(
        identity=email, additional_claims={"role": "admin", "dbid": get_db_instance_id()}
    )
    return jsonify({'access_token': access_token})


@app.route('/api/manager/dashboard', methods=['GET'])
@jwt_required()
@cache.cached(timeout=30, key_prefix=per_user_cache_key, response_filter=only_ok)
@api_errors
def manager_dashboard_route():
    _require_manager_or_admin()
    return jsonify({"categories": get_categories_with_products_from_db()})


@app.route('/api/manager/add_product', methods=['POST'])
@jwt_required()
@api_errors
def add_product_route():
    _require_manager_or_admin()
    fields = _product_fields(json_body())
    add_product_to_category_in_db(
        fields['category_id'], fields['product_name'], fields['quantity'], fields['manufacture_date'],
        fields['expiry_date'], fields['price'], fields['unit'],
    )
    cache.clear()
    return jsonify({"success": "Product added to the category."}), 201


@app.route('/api/manager/edit_product', methods=['POST'])
@jwt_required()
@api_errors
def edit_product():
    _require_manager_or_admin()
    data = json_body()
    product_id = _required_id(data, 'product_id')
    if not product_exists(product_id):
        raise NotFound("Product not found")
    fields = _product_fields(data)
    update_product_in_db(
        product_id, fields['product_name'], fields['category_id'], fields['quantity'], fields['price'],
        fields['unit'], fields['manufacture_date'], fields['expiry_date'],
    )
    cache.clear()
    return jsonify({"success": "Product updated."})


@app.route('/api/manager/delete_product', methods=['POST'])
@jwt_required()
@api_errors
def remove_product_route():
    _require_manager_or_admin()
    remove_product_from_db(_required_id(json_body(), 'product_id'))
    cache.clear()
    return jsonify({"success": "Product deleted."})


@app.route('/api/manager/categories/delete_category', methods=['POST'])
@jwt_required()
@api_errors
def remove_category():
    _require_admin()
    remove_category_from_db(_required_id(json_body(), 'categoryID'))
    cache.clear()
    return jsonify({"success": "Category deleted successfully"})


@app.route('/api/manager/categories/add_category', methods=['POST'])
@jwt_required()
@api_errors
def add_category():
    _require_admin()
    category_name = require_str(json_body(), 'category_name', "Category name")
    add_category_to_db(category_name)
    cache.clear()
    return jsonify({"success": "Category added successfully"}), 201


# Spreadsheet apps treat a cell starting with one of these as a formula.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value):
    """Neutralise CSV/formula injection: text cells that a spreadsheet would
    evaluate (e.g. a product named ``=HYPERLINK(...)``) get a leading ``'``.
    Numbers are left alone so negative amounts stay numeric."""
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


@app.route('/api/manager/prepare_report', methods=['GET'])
@jwt_required()
@api_errors
def prepare_report():
    _require_manager_or_admin()
    cursor = get_db().cursor()
    try:
        cursor.execute('''SELECT order_items.product_name,
                                 SUM(order_items.quantity) AS total_quantity,
                                 SUM(order_items.quantity * products.price) AS total_price
                          FROM order_items
                          INNER JOIN products ON order_items.product_name = products.name
                          GROUP BY order_items.product_name''')
        rows = cursor.fetchall()
    finally:
        cursor.close()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['Product name', 'Quantity sold', 'Total amount'])
    writer.writerows([_csv_safe(cell) for cell in row] for row in rows)
    response = Response(buffer.getvalue().encode('utf-8'), content_type='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=order_report.csv'
    return response


@app.route('/api/admin/manager_requests', methods=['GET'])
@jwt_required()
@cache.cached(timeout=20, key_prefix=per_user_cache_key, response_filter=only_ok)
@api_errors
def manager_requests():
    _require_admin()
    return jsonify({"manager_requests": get_manager_requests()})


def _manager_email():
    return require_str(json_body(), 'email', "email")


@app.route('/api/admin/accept_manager', methods=['POST'])
@jwt_required()
@api_errors
def accept_manager():
    _require_admin()
    approve_manager(_manager_email())
    cache.clear()
    return jsonify({"success": "Manager request accepted."})


@app.route('/api/admin/reject_manager', methods=['POST'])
@jwt_required()
@api_errors
def reject_manager():
    _require_admin()
    deny_manager(_manager_email())
    cache.clear()
    return jsonify({"success": "Manager request rejected."})
