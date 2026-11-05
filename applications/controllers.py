from functools import wraps

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from applications.ai_service import shopping_assistant, smart_search
from applications.caching import cache
from applications.cart_functions import (
    apply_coupon,
    cart_quote,
    checkout_order,
    delete_cart_item,
    insert_cart_item,
    remove_coupon,
    update_cart_item,
)
from applications.catalog import get_categories, list_products, products_by_category, search_products
from applications.catalog import get_product as fetch_product
from applications.errors import AppError
from applications.login_manager import login, signup
from applications.ratings import list_reviews, upsert_review
from applications.recommendations import recommend, recommend_for_cart, recommend_for_user
from applications.store_manager import add_manager_apply, manager_status_check
from applications.user_info import fetch_order_history, fetch_user_info
from applications.wishlist import add_to_wishlist, list_wishlist, move_to_cart, remove_from_wishlist
from flask import current_app as app


def api_view(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except AppError as exc:
            return jsonify({"error": exc.message}), exc.status

    return wrapper


def _json():
    return request.get_json(silent=True) or {}


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/user_dashboard")
@cache.cached(timeout=30)
def index():
    return jsonify({"products": list_products()})


@app.get("/api/getCategories")
@cache.cached(timeout=50)
def categories():
    return jsonify(get_categories())


@app.get("/api/category/<int:category_id>")
def products_by_category_route(category_id):
    return jsonify({"products": products_by_category(category_id)})


@app.post("/api/search")
@api_view
def search():
    return jsonify(search_products(_json()))


@app.post("/api/search/smart")
@api_view
def search_smart():
    query = (_json().get("query") or _json().get("search_query") or "").strip()
    if not query:
        raise AppError("Enter a search.")
    return jsonify(smart_search(query))


@app.post("/api/assistant")
@api_view
def assistant():
    message = (_json().get("message") or "").strip()
    if not message:
        raise AppError("Tell the assistant what you want to cook or buy.")
    return jsonify(shopping_assistant(message))


@app.get("/api/products/<int:product_id>")
@api_view
def product_detail(product_id):
    product = fetch_product(product_id)
    product["reviews"] = list_reviews(product_id)
    product["bought_together"] = recommend([product_id], limit=4, context="product")
    return jsonify({"product": product})


@app.post("/api/products/<int:product_id>/reviews")
@jwt_required()
@api_view
def create_review(product_id):
    payload = _json()
    review = upsert_review(
        get_jwt_identity(),
        product_id,
        payload.get("rating"),
        payload.get("body") or payload.get("review") or "",
    )
    cache.clear()
    return jsonify({"success": "Review saved.", "review": review}), 201


@app.get("/api/recommendations/popular")
def popular():
    return jsonify({"recommendations": recommend([], limit=6, context="cart")})


@app.get("/api/recommendations/cart")
@jwt_required()
@api_view
def cart_recommendations():
    return jsonify({"recommendations": recommend_for_cart(get_jwt_identity())})


@app.get("/api/recommendations/for-you")
@jwt_required()
@api_view
def for_you():
    return jsonify({"recommendations": recommend_for_user(get_jwt_identity())})


@app.get("/api/shopping_cart")
@jwt_required()
@api_view
def view_shopping_cart():
    return jsonify(cart_quote(get_jwt_identity()))


@app.post("/api/add_to_cart")
@jwt_required()
@api_view
def add_to_cart():
    payload = _json()
    insert_cart_item(get_jwt_identity(), payload.get("product_id"), payload.get("quantity"))
    cache.clear()
    return jsonify({"success": "Product added to the cart successfully"})


@app.post("/api/shopping_cart/update_product")
@jwt_required()
@api_view
def update_product():
    payload = _json()
    update_cart_item(get_jwt_identity(), payload.get("product_id"), payload.get("quantity"))
    cache.clear()
    return jsonify({"success": "Product quantity updated successfully."})


@app.post("/api/shopping_cart/delete_product")
@jwt_required()
@api_view
def delete_product():
    delete_cart_item(get_jwt_identity(), _json().get("product_id"))
    cache.clear()
    return jsonify({"success": "Product deleted successfully."})


@app.post("/api/shopping_cart/apply_coupon")
@jwt_required()
@api_view
def apply_coupon_route():
    quote = apply_coupon(get_jwt_identity(), _json().get("coupon_code"))
    return jsonify(quote)


@app.post("/api/shopping_cart/remove_coupon")
@jwt_required()
@api_view
def remove_coupon_route():
    return jsonify(remove_coupon(get_jwt_identity()))


@app.post("/api/shopping_cart/checkout")
@jwt_required()
@api_view
def checkout():
    # The client may still send totalPrice. It is not read.
    result = checkout_order(get_jwt_identity())
    cache.clear()
    return jsonify(result)


@app.get("/api/wishlist")
@jwt_required()
@api_view
def wishlist():
    return jsonify({"wishlist": list_wishlist(get_jwt_identity())})


@app.post("/api/wishlist")
@jwt_required()
@api_view
def wishlist_add():
    add_to_wishlist(get_jwt_identity(), _json().get("product_id"))
    return jsonify({"success": "Saved to your wishlist."})


@app.delete("/api/wishlist/<int:product_id>")
@jwt_required()
@api_view
def wishlist_remove(product_id):
    remove_from_wishlist(get_jwt_identity(), product_id)
    return jsonify({"success": "Removed from your wishlist."})


@app.post("/api/wishlist/<int:product_id>/move-to-cart")
@jwt_required()
@api_view
def wishlist_move(product_id):
    quantity = _json().get("quantity", 1)
    move_to_cart(get_jwt_identity(), product_id, quantity)
    cache.clear()
    return jsonify({"success": "Moved to your cart."})


@app.get("/api/dashboard")
@jwt_required()
@api_view
def user_dashboard():
    email = get_jwt_identity()
    return jsonify(
        {
            "user_info": fetch_user_info(email),
            "user_orders": fetch_order_history(email),
            "manager_status": manager_status_check(email),
        }
    )


@app.post("/api/login")
@api_view
def login_route():
    payload = _json()
    user = login(payload.get("email"), payload.get("password"))
    profile = fetch_user_info(user["email"])
    from flask_jwt_extended import create_access_token

    token = create_access_token(identity=user["email"], additional_claims={"role": user["role"]})
    return jsonify(
        {
            "access_token": token,
            "name": profile["name"],
            "role": user["role"],
            "is_manager": user["role"] == "manager",
        }
    )


@app.post("/api/signup")
@api_view
def signup_route():
    payload = _json()
    signup(
        payload.get("email"),
        payload.get("password"),
        payload.get("name"),
        payload.get("phoneNo") or payload.get("phone"),
        payload.get("address"),
    )
    return jsonify({"message": "Success"}), 201


@app.post("/api/apply_manager")
@jwt_required()
@api_view
def apply_manager():
    add_manager_apply(get_jwt_identity())
    return jsonify({"success": "Applied for manager status."})
