"""Shopper-facing and authentication API routes.

Errors are returned as ``{"error": "<message>"}`` with a matching HTTP status
(400 bad input, 401 bad credentials, 403 not allowed, 404 not found,
409 conflict, 500 unexpected).
"""
from flask import current_app as app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from applications.auth import per_user_cache_key
from applications.caching import cache
from applications.cart_functions import (
    checkout_cart, delete_cart_item, fetch_cart_items_by_email, insert_cart_item, update_cart_item,
)
from applications.categories_functions import category_exists, get_10_products, get_categories, get_products_by_category
from applications.http_errors import (
    BadRequest, NotFound, api_errors, json_body, number, only_ok, optional_date,
    positive_int, require_str,
)
from applications.database import get_db_instance_id
from applications.login_manager import (
    login, normalize_email, register_user, validate_email, validate_phone_number,
)
from applications.search_functions import (
    get_products_by_category_search, search_categories_in_db, search_products_in_db,
)
from applications.store_manager import add_manager_apply, manager_check, manager_status_check
from applications.user_info import fetch_order_history, fetch_user_info


@app.get('/api/health')
def health():
    return jsonify({"status": "ok"})


@app.route('/api/user_dashboard', methods=["GET"])
@cache.cached(timeout=30, response_filter=only_ok)
@api_errors
def index():
    return jsonify({"products": get_10_products()})


@app.route("/api/getCategories", methods=['GET'])
@cache.cached(timeout=50, response_filter=only_ok)
@api_errors
def getCategories():
    return jsonify(get_categories())


@app.route('/api/category/<int:category_id>', methods=['GET'])
@api_errors
def products_by_category(category_id):
    if not category_exists(category_id):
        raise NotFound("Category not found")
    return jsonify(get_products_by_category(category_id))


# --- cart -------------------------------------------------------------------

def _product_id(data):
    if data.get('product_id') in (None, ""):
        raise BadRequest("product_id is required")
    return positive_int(data.get('product_id'), "product_id")


@app.route('/api/shopping_cart', methods=["GET"])
@jwt_required()
@cache.cached(timeout=10, key_prefix=per_user_cache_key, response_filter=only_ok)
@api_errors
def view_shopping_cart():
    return jsonify({"cart": fetch_cart_items_by_email(get_jwt_identity())})


@app.route('/api/add_to_cart', methods=["POST"])
@jwt_required()
@api_errors
def add_to_cart():
    data = json_body()
    product_id = _product_id(data)
    if data.get('quantity') in (None, ""):
        raise BadRequest("quantity is required")
    quantity = positive_int(data.get('quantity'), "Quantity")
    insert_cart_item(get_jwt_identity(), product_id, quantity)
    cache.clear()
    return jsonify({"success": "Product added to the cart successfully"})


@app.route('/api/shopping_cart/update_product', methods=['POST'])
@jwt_required()
@api_errors
def update_product():
    data = json_body()
    product_id = _product_id(data)
    if data.get('quantity') in (None, ""):
        raise BadRequest("quantity is required")
    quantity = positive_int(data.get('quantity'), "Quantity", allow_zero=True)
    update_cart_item(get_jwt_identity(), product_id, quantity)
    cache.clear()
    return jsonify({"success": "Product quantity updated successfully."})


@app.route('/api/shopping_cart/delete_product', methods=['POST'])
@jwt_required()
@api_errors
def delete_product():
    product_id = _product_id(json_body())
    delete_cart_item(get_jwt_identity(), product_id)
    cache.clear()
    return jsonify({"success": "Product deleted successfully."})


@app.route('/api/shopping_cart/checkout', methods=['POST'])
@jwt_required()
@api_errors
def checkout():
    # The total is computed from the cart and current prices on the server;
    # anything the client sends in the body is ignored.
    order_id, items, total = checkout_cart(get_jwt_identity())
    cache.clear()
    return jsonify({
        "success": "Checkout successful",
        "order_id": order_id,
        "cart_items": items,
        "totalPrice": total,
    })


# --- account ----------------------------------------------------------------

@app.route('/api/dashboard', methods=['GET'])
@jwt_required()
@cache.cached(timeout=30, key_prefix=per_user_cache_key, response_filter=only_ok)
@api_errors
def user_dashboard():
    email = get_jwt_identity()
    user_info = fetch_user_info(email)
    if user_info is None:
        raise NotFound("User profile not found")
    return jsonify({
        "user_info": user_info,
        "user_orders": fetch_order_history(email),
        "manager_status": manager_status_check(email),
    })


@app.route('/api/login', methods=['POST'])
@api_errors
def login_route():
    data = json_body()
    email = normalize_email(require_str(data, 'email', "Email"))
    password = data.get('password')
    if not isinstance(password, str) or not password:
        raise BadRequest("Password is required")
    login(email, password)
    user = fetch_user_info(email)
    is_manager = manager_check(email)
    access_token = create_access_token(
        identity=email,
        additional_claims={"role": "manager" if is_manager else "user", "dbid": get_db_instance_id()},
    )
    return jsonify({
        'access_token': access_token,
        "name": user['name'] if user else email,
        "is_manager": is_manager,
    })


@app.route('/api/signup', methods=['POST'])
@api_errors
def signup_route():
    data = json_body()
    name = require_str(data, 'name', "Name")
    email = normalize_email(require_str(data, 'email', "Email"))
    password = data.get('password')
    phone_number = data.get('phoneNo')
    address = data.get('address') or ""
    if not validate_email(email):
        raise BadRequest("Valid email required")
    if not validate_phone_number(phone_number):
        raise BadRequest("Valid phone number required")
    if not isinstance(password, str) or not password:
        raise BadRequest("Password is required")
    if not isinstance(address, str):
        raise BadRequest("Address must be text")
    register_user(email, password, name, phone_number.strip(), address.strip())
    return jsonify({"message": "Success"}), 201


@app.route('/api/apply_manager', methods=['POST'])
@jwt_required()
@api_errors
def apply_manager():
    add_manager_apply(get_jwt_identity())
    cache.clear()
    return jsonify({"success": "Applied for manager status."})


# --- search -----------------------------------------------------------------

@app.route('/api/search', methods=['POST'])
@api_errors
def search():
    data = json_body()
    search_query = data.get('search_query') or ""
    if not isinstance(search_query, str):
        raise BadRequest("search_query must be text")
    search_query = search_query.strip().lower()

    min_price = data.get('min_price')
    min_price = 0 if min_price in (None, "") else number(min_price, "Minimum price", positive=False)
    max_price = data.get('max_price')
    # 0 / empty means "no upper limit"
    max_price = None if max_price in (None, "", 0) else number(max_price, "Maximum price", positive=False)
    if max_price is not None and max_price < min_price:
        raise BadRequest("Maximum price must not be below minimum price")

    filters = dict(
        min_price=min_price,
        max_price=max_price,
        min_manufacture_date=optional_date(data.get('min_manufacture_date'), "Minimum manufacture date"),
        max_manufacture_date=optional_date(data.get('max_manufacture_date'), "Maximum manufacture date"),
        min_expiry_date=optional_date(data.get('min_expiry_date'), "Minimum expiry date"),
        max_expiry_date=optional_date(data.get('max_expiry_date'), "Maximum expiry date"),
        exclude_out_of_stock=bool(data.get('exclude_out_of_stock')),
    )

    response_data = {}
    product_results = search_products_in_db(search_query, **filters)
    if product_results:
        response_data["products"] = product_results
    else:
        category_results = search_categories_in_db(search_query)
        if category_results:
            response_data["category_results"] = category_results
            products_in_category = get_products_by_category_search(category_results, **filters)
            if products_in_category:
                response_data["products_in_category"] = products_in_category
            else:
                response_data["no_results"] = True
        else:
            response_data["no_results"] = True
    return jsonify(response_data)
