from flask import Flask, render_template, request, redirect, session,url_for, flash, g, jsonify
from applications.login_manager import *
from applications.categories_functions import *
from applications.cart_functions import *
from applications.user_info import *
from applications.search_functions import *
from applications.database import *
from applications.backend_tasks import *
from applications.store_manager import *
from flask import current_app as app
from datetime import date
from .caching import cache

from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

@app.get('/say_hello')
def say_hello_view():
    task  = say_hello.delay()
    return jsonify({"task-id": task.id})

# @app.get('/create_resource_csv')
# def download_csv():
#     task = create_resource_csv.delay()
#     return jsonify({"task-id": task.id})


@app.route('/api/user_dashboard', methods=["GET"])
@cache.cached(timeout=30)
# @jwt_required()
def index():
    # print("Is this working")
        # token=request.headers["Auth-token"]
    if request.method == "GET":
        try:
            products = get_10_products()
            # email = get_jwt_identity()
            # print("Received JWT identity:", email)
            # if email:
                # user = fetch_user_info(email)
                # name = user['name']
            response_data = {
                "products": products,
            }
            
            return jsonify(response_data)
        
        except Exception as e:
            response_data = {"error": str(e)}
            return jsonify(response_data)

@app.route("/api/getCategories", methods=['GET'])
@cache.cached(timeout=50)
def getCategories():
    try:
        categories = get_categories()
        print(categories)
        return jsonify(categories)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/shopping_cart', methods=["GET"])
@jwt_required()
@cache.cached(timeout=10)
def view_shopping_cart():
    try:
        email = get_jwt_identity()
        cart_data = fetch_cart_items_by_email(email)
        return jsonify({"cart": cart_data})
    except Exception as e:
        return jsonify({"error": str(e)})




@app.route('/api/add_to_cart', methods=["POST", "GET"])
@jwt_required()
def add_to_cart():
    email = get_jwt_identity()
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity')

    if not product_id or not quantity or int(quantity) <= 0:
        return jsonify({"error": "Invalid product or quantity"})

    try:
        cache.clear()
        insert_cart_item(email, product_id, quantity)
        return jsonify({"success": "Product added to the cart successfully"})
    except Exception as e:
        return jsonify({"error": str(e)})


# @app.route('/shopping_cart', methods=['GET', 'POST'], endpoint='shopping_cart')
# def shopping_cart():
#     categories = get_categories()
#     if 'email' not in session:
#         return redirect(url_for('login_route'))
    
#     email = session['email']
#     totalPrice = 0;
#     try:
#         cart_items = fetch_cart_items_by_email(email)
#         for (name, price, quantity, productID) in cart_items:
#             totalPrice += price * quantity

#         email = session['email']
#         user = get_user(email)
#         name = user[1]

#         coupon_code = request.form.get('coupon_code')
#         if coupon_code:
#             try:
#                 discount_percentage = apply_coupon(email, coupon_code)
#                 if discount_percentage is not None:
#                     totalPrice -= totalPrice * (discount_percentage / 100)
#                     flash('Coupon code applied')
#             except Exception as e:
#                 flash(str(e), "error")
#                 return redirect('/shopping_cart')

#         formatted_total_price = "{:.2f}".format(totalPrice)
#         return render_template('shopping_cart.html', user=name,cart_items=cart_items, totalPrice=formatted_total_price, signed=True, categories=categories)
#     except Exception as e:
#         flash(str(e), "error")
#         return redirect(url_for('index'))

@app.route('/api/shopping_cart/update_product', methods=['GET','POST'])
@jwt_required()
def update_product():
    email = get_jwt_identity()
    try:
        product_id = request.json.get('product_id')
        quantity = request.json.get('quantity')
        update_cart_item(email, product_id, quantity)
        cache.clear()
        print("ok")
        return jsonify({"success":"Product quantity updated successfully."})
    except Exception as e:
        return jsonify({"error": str(e)})
    

@app.route('/api/shopping_cart/delete_product', methods=['POST', 'GET'])
@jwt_required()
def delete_product():
    email = get_jwt_identity()
    try:
        product_id = request.json.get('product_id')
        delete_cart_item(email, product_id)
        cache.clear()
        return jsonify({"success":"Product deleted successfully."})
    except Exception as e:
        return jsonify({"error": str(e)})
    

@app.route('/api/shopping_cart/checkout', methods=['POST', 'GET'])
@jwt_required()
def checkout():
    email = get_jwt_identity()
    print(email)    
    try:
        cache.clear()
        cart_items = fetch_cart_items_by_email_for_checkout(email)
        print(cart_items)
        totalPrice = request.json.get('totalPrice')
        print(totalPrice)
        order_date = str(date.today())
        update_inventory()
        print("inventory updated")
        record_order(email, order_date, cart_items, totalPrice)
        print("Order recorded")
        empty_cart(email)
        print("Cart emptied")
        
        return jsonify({
            "success": "Checkout successful",
            "cart_items": cart_items,
            "totalPrice": totalPrice
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/dashboard', methods=['GET'])
@jwt_required()
@cache.cached(timeout=30)
def user_dashboard():
    email = get_jwt_identity()

    try:
        user_info = fetch_user_info(email)
        user_orders = fetch_order_history(email)
        manager_status = manager_status_check(email)

        return jsonify({
            "user_info": user_info,
            "user_orders": user_orders,
            "manager_status": manager_status
        })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/login', methods=['POST', 'GET'])
def login_route():
        print("Doing nothing")
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            login(email, password)
            user = fetch_user_info(email)
            access_token = create_access_token(identity=email)
            is_manager = manager_check(email)
            return jsonify({'access_token': access_token, "name": user['name'], "is_manager": is_manager}), 200            
        except Exception as e:
            return jsonify({"message": "Error: "+str(e)}),500



@app.route('/api/signup', methods=['POST', 'GET'])
def signup_route():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        phone_number = data.get('phoneNo')
        print(phone_number == "") # this is coming as true
        address = data.get('address')
        if not validate_email(email):  
            raise Exception("Valid email required")
        if not validate_phone_number(phone_number): 
            raise Exception("Valid phone number required")
        
        signup(email, password)
        add_user_info(email, name, phone_number, address)
        return jsonify({"message":"Success"})
    except Exception as e:
        return jsonify({"Error": str(e)})

@app.route('/api/category/<int:category_id>', methods=['GET'])
def products_by_category(category_id):
    try:
        products = get_products_by_category(category_id)
        return jsonify(products)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/search', methods=['POST', 'GET'])
def search():
    try:

        search_query = request.json.get('search_query')
        print(search_query)
        min_price = request.json.get('min_price', 0)
        max_price = request.json.get('max_price')
        if max_price == 0: max_price = float('inf')
        min_manufacture_date = request.json.get('min_manufacture_date', '')
        max_manufacture_date = request.json.get('max_manufacture_date', '')
        min_expiry_date = request.json.get('min_expiry_date', '')
        max_expiry_date = request.json.get('max_expiry_date', '')
        exclude_out_of_stock = request.json.get('exclude_out_of_stock')
        
        product_results = search_products_in_db(search_query.lower(), min_price, max_price,
                                                min_manufacture_date, max_manufacture_date,
                                                min_expiry_date, max_expiry_date, exclude_out_of_stock)
        print(len(product_results))
        category_results = search_categories_in_db(search_query.lower())
        
        response_data = { }

        if product_results:
            response_data["products"] = product_results
        elif category_results:
            response_data["category_results"] = category_results
            products_in_category = get_products_by_category_search(category_results, min_price, max_price,
                                                min_manufacture_date, max_manufacture_date,
                                                min_expiry_date, max_expiry_date)
            print("Products in category", products_in_category)
            if products_in_category:
                response_data["products_in_category"] = products_in_category
            else:
                response_data["no_results"] = True
        else:
            response_data["no_results"] = True
        
        print(response_data)
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)})
    
@app.route('/api/apply_manager', methods=['GET', 'POST'])
@jwt_required()
def apply_manager():
    try:
        email = get_jwt_identity()
        print(email)
        add_manager_apply(email)
        return jsonify({"success": "Applied for manager status."})
    except Exception as e:
        return jsonify({"error": str(e)})
