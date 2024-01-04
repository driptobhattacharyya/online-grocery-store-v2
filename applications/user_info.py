from applications.database import *

def fetch_order_history(email):
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Query to fetch the user's order history from the database
        query = "SELECT orderID, order_date, total_price FROM orders WHERE email = ? ORDER BY order_date DESC"
        cursor.execute(query, (email,))
        order_history = cursor.fetchall()
        
        user_orders = []
        for order_row in order_history:
            orderID = order_row[0]
            order_date = order_row[1]
            total_price = order_row[2]

            # Query to fetch order items for the current orderID
            item_query = "SELECT product_name, quantity FROM order_items WHERE orderID = ?"
            cursor.execute(item_query, (orderID,))
            order_items = cursor.fetchall()

            items_list = []
            for item_row in order_items:
                product_name = item_row[0]
                quantity = item_row[1]
                items_list.append({'product_name': product_name, 'quantity': quantity})

            user_orders.append({
                'order_date': order_date,
                'items': items_list,
                'total_price': total_price
            })
        
        cursor.close()
        return user_orders
    except Exception as e:
        cursor.close()
        raise e

def fetch_user_info(email):
    db = get_db()
    cursor = db.cursor()
    try:
    # Query to fetch the user's information from the user_profiles table
        query = "SELECT email, name, address, phone FROM user_profiles WHERE email = ?"
        cursor.execute(query, (email,))
        
        user_info = cursor.fetchone()
        
        (email, name, address, phone_no) = user_info
        userinfo = {'email': email, 'name': name, 'address': address, 'phone_no': phone_no}
        
        return userinfo
    except Exception as e:
        cursor.close()
        raise e

def add_user_info(email, name, phone, address):
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Query to insert the user's information into the user_profiles table
        query = "INSERT INTO user_profiles (email, name, address, phone) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (email, name, address, phone))
        
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e