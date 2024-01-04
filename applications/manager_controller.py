from flask import Flask, render_template, request, redirect, session,url_for, flash, g, jsonify, Response
import sqlite3
from applications.login_manager import *
from applications.categories_functions import *
from applications.cart_functions import *
from applications.user_info import *
from applications.search_functions import *
from applications.manager_functions import *
from applications.manager_coupons_functions import *
from applications.manager_summary_functions import *
from applications.database import *
from applications.store_manager import *
from flask import current_app as app
from .caching import cache

from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity



@app.route('/api/admin/login', methods=['GET', 'POST'])
def manager_login_route(): #actually for the admin
    try:
        email = request.json.get('email')
        password = request.json.get('password')
    
        manager_login(email, password) #actually for the admin
        access_token = create_access_token(identity=email)
        return jsonify({'access_token': access_token}), 200     
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/manager/dashboard', methods=['GET', 'POST'])
@jwt_required()
@cache.cached(timeout=30)
def manager_dashboard_route():
    try:
        email = get_jwt_identity()
        is_manager = request.args.get("is_manager")
        print(is_manager, type(is_manager))
        if ((email == "admin") or (is_manager == 'true')):
            print("Please give this manager the categories and products")
            categories = get_categories_with_products_from_db()            
            print(categories)
            return jsonify({"categories":categories})
        else:
            print("Not a manager or an admin")
            raise Exception("You are not authorized to perform this action.")
    except Exception as e:
        return jsonify({"error":str(e)})
    

@app.route('/api/getProduct', methods=['GET'])
def getProduct():
    try:
        product_id = request.json.get('product_id')
        print(product_id)
        categories = get_categories_with_products_from_db()            
        print(categories)
        for category in categories:
            print("Category", category)
            for product in category['products']:
                print("Product", product)
                if product['productID'] == product_id:
                    print("Product:" , product)
                    return jsonify({"product":product})
    except Exception as e:
        return jsonify({"Error":str(e)})


@app.route('/api/manager/add_product', methods=['GET', 'POST'])
@jwt_required()
def add_product_route():
    try:
        email = get_jwt_identity()
        is_manager = request.args.get("is_manager")
        if ((email == "admin") or (is_manager == 'true')):
            category = request.json.get('category')
            product_name = request.json.get('product_name')
            quantity = request.json.get('quantity')
            price = request.json.get('price')
            unit = request.json.get('unit')
            manufacture_date = request.json.get('manufacture_date')
            expiry_date = request.json.get('expiry_date')
            cache.clear()
            add_product_to_category_in_db(category, product_name, quantity, manufacture_date, expiry_date, price, unit)
            
            return jsonify({"success": "Product added to the category."})
        else:
            print("Not a manager or an admin")
            raise Exception("You are not authorized to perform this action.")

    
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/manager/edit_product', methods=['GET', 'POST'])
@jwt_required()
def edit_product():
    print(request.get_json())
    try:
        email = get_jwt_identity()
        is_manager = request.json.get("is_manager")
        if ((email == "admin") or (is_manager == 'true')):
            product_id = request.json.get('product_id')
            print(product_id)
            product_name = request.json.get('product_name')
            print(product_name)
            category = request.json.get('category')
            print(category)
            quantity = request.json.get('quantity')
            print(quantity)
            price = request.json.get('price')
            print(price)
            unit = request.json.get('unit')
            print(unit)
            manufacture_date = request.json.get('manufacture_date')
            print(manufacture_date)
            expiry_date = request.json.get('expiry_date')
            print(expiry_date)
            cache.clear()
            update_product_in_db(product_id, product_name, category, quantity, price, unit, manufacture_date, expiry_date)
            return jsonify({"success": "Product updated."})
        
        else:
            print("Not a manager or an admin")
            raise Exception("You are not authorized to perform this action.")
    
    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}) 
        

@app.route('/api/manager/delete_product', methods=['GET', 'POST'])
@jwt_required()
def remove_product_route():        
    try:
        email = get_jwt_identity()
        is_manager = request.args.get("is_manager")
        print(is_manager)
        if ((email == "admin") or (is_manager == 'true')):
            product_id = request.json.get('product_id')
            cache.clear()
            remove_product_from_db(product_id)
            return jsonify({"success": "Product deleted."})
            
        else:
            print("Not a manager or an admin")
            raise Exception("You are not authorized to perform this action.")

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/manager/categories/delete_category', methods=['GET','POST'])
@jwt_required()
def remove_category():
    email = get_jwt_identity()
    if email != "admin":
        return jsonify({"error": "You are not authorized to perform this action."})
    
    try:
        categoryID = request.json.get('categoryID')
        cache.clear()
        remove_category_from_db(categoryID)
        return jsonify({"success":"Category deleted successfully"})
    except Exception as e:
        return jsonify({"error":str(e)})

@app.route('/manager/categories/add_category', methods=['GET','POST'])
@jwt_required()
def add_category():
    email = get_jwt_identity()
    if email != "admin":
        return jsonify({"error": "You are not authorized to perform this action."})
        
    
    try:
            
            category_name = request.json.get('category_name')
            cache.clear()
            add_category_to_db(category_name)
            return jsonify({"success":"Category added succesfully"})
    except Exception as e:
        flash(str(e))
    return redirect('/manager/dashboard')

import csv

@app.route('/api/manager/prepare_report', methods=['GET','POST'])
# @jwt_required()
def prepare_report():
    try:
        # email = get_jwt_identity()
        # if email != "admin":
        #     return jsonify({"error": "You are not authorized to perform this action."})
        db = get_db()
        cursor=db.cursor()
        query = '''SELECT 
                        order_items.product_name,
                        SUM(order_items.quantity) AS total_quantity,
                        SUM(order_items.quantity * products.price) AS total_price
                    FROM 
                        order_items
                    INNER JOIN 
                        products ON order_items.product_name = products.name
                    GROUP BY 
                        order_items.product_name;
                    '''
        
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        csv_data = [['Product name', 'Quantity sold', 'Total amount']]
        for row in result:
            csv_data.append([row[0], row[1], row[2]])
        
        file_path = 'sale_report.csv' 
        with open(file_path, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerows(csv_data)
        
        # Convert CSV data to bytes
        csv_bytes = '\n'.join([','.join(map(str, row)) for row in csv_data]).encode('utf-8')
        
        response = Response(csv_bytes, content_type='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=order_report.csv'
        
        return response
    
    except Exception as e:
        return jsonify({"error": str(e)})
    

@app.route('/api/admin/manager_requests', methods=['GET'])
@jwt_required()
@cache.cached(timeout=20)
def manager_requests():
    try:
        email = get_jwt_identity()
        if email != "admin":
            return jsonify({"error": "You are not authorized to perform this action."})
        manager_requests = get_manager_requests()
        return jsonify({"manager_requests": manager_requests})
    except Exception as e:
        return jsonify({"error": str(e)})
    
@app.route('/api/admin/accept_manager', methods=['POST'])
@jwt_required()
def accept_manager():
    try:
        email = get_jwt_identity()
        if email != "admin":
            return jsonify({"error": "You are not authorized to perform this action."})
        manager_email = request.json.get('email')
        cache.clear()
        approve_manager(manager_email)
        return jsonify({"success": "Manager request accepted."})
    except Exception as e:
        return jsonify({"error":str(e)})
    
@app.route('/api/admin/reject_manager', methods=['POST', 'GET'])
@jwt_required()
def reject_manager():
    try:
        email = get_jwt_identity()
        if email != "admin":
            return jsonify({"error": "You are not authorized to perform this action."})
        manager_email = request.json.get('email')
        cache.clear()
        deny_manager(manager_email)
        return jsonify({"success": "Manager request rejected."})
    except Exception as e:
        return jsonify({"error":str(e)})