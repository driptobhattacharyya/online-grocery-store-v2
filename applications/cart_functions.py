from applications.database import *

def insert_cart_item(email, product_id, quantity):
    db = get_db()
    cursor = db.cursor()

    # Check if the product is available in the inventory with enough quantity
    cursor.execute("SELECT quantity FROM inventory WHERE productID = ?", (product_id,))
    available_quantity = cursor.fetchone()
    
    if available_quantity is None or available_quantity[0] < quantity:
        cursor.close()
        raise Exception("Insufficient stock for this product. Available in stock:", available_quantity[0])
    
    try:
        # Check if the product is already in the cart for the user
        cursor.execute("SELECT quantity FROM cart WHERE email = ? AND product_id = ?", (email, product_id))
        existing_quantity = cursor.fetchone()
        
        if existing_quantity:
            # If the product is already in the cart, update the quantity
            new_quantity = existing_quantity[0] + quantity
            cursor.execute("UPDATE cart SET quantity = ? WHERE email = ? AND product_id = ?", 
                           (new_quantity, email, product_id))
        else:
            # If the product is not in the cart, insert a new row
            cursor.execute("INSERT INTO cart (email, product_id, quantity) VALUES (?, ?, ?)",
                            (email, product_id, quantity))
        
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e


def fetch_cart_items_by_email(email):
    db = get_db()
    cursor = db.cursor()
    
    try:
    
        # Query cart items based on the user's email
        cursor.execute('''SELECT products.name, products.price, cart.quantity, products.productID
                        FROM cart
                        INNER JOIN products ON cart.product_id = products.productID
                        WHERE cart.email = ?''', (email,))
        
        cart_items = cursor.fetchall()
        cursor.close()
        
        cart_items_list = []
        for item in cart_items:
            cart_item_dict = {
                "name": item[0],
                "price": item[1],
                "quantity": item[2],
                "productID": item[3]
            }
            cart_items_list.append(cart_item_dict)

        return cart_items_list
    
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e

def fetch_cart_items_by_email_for_checkout(email):
    db = get_db()
    cursor = db.cursor()

    try:
    
        # Query cart items based on the user's email
        cursor.execute('''SELECT products.name, products.price, cart.quantity, products.productID
                        FROM cart
                        INNER JOIN products ON cart.product_id = products.productID
                        WHERE cart.email = ?''', (email,))
        
        cart_items = cursor.fetchall()
        cursor.close()
        return cart_items
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e

def apply_coupon(email, coupon_code):
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT discount_percentage FROM coupons WHERE coupon_code = ?", (coupon_code,))
        coupon_data = cursor.fetchone()
        
        if coupon_data is None:
            # Coupon code not found in the database
            raise Exception('No such coupon code available.')
        
        # Check if the coupon code has already been used by the user
        cursor.execute("SELECT * FROM used_coupons WHERE user_email = ? AND coupon_code = ?", (email, coupon_code))
        used_coupon_data = cursor.fetchone()
        
        if used_coupon_data is not None:
            # Coupon code has already been used by the user
            raise Exception("You've already used this coupon code.")
        
        # Insert the coupon code into the used_coupons table
        cursor.execute("INSERT INTO used_coupons (user_email, coupon_code) VALUES (?, ?)", (email, coupon_code))

        db.commit()
        db.close()
        return int(coupon_data[0])
    except Exception as e:
        db.rollback()
        db.close()
        raise e
    
def empty_cart(email):
    
    db = get_db()
    cursor = db.cursor()
    try:
        # Delete all cart items associated with the user's email
        cursor.execute("DELETE FROM cart WHERE email = ?", (email,))
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e
    
def delete_cart_item(email, product_id):
    db = get_db()
    cursor = db.cursor()
    try:
        # Delete the cart item associated with the user's email and product ID
        cursor.execute("DELETE FROM cart WHERE email = ? AND product_id = ?", (email, product_id))
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e
    
def update_cart_item(email, product_id, quantity):
    db = get_db()
    cursor = db.cursor()
    try:
        # Update the cart item associated with the user's email and product ID
        if quantity == 0:
            cursor.execute("DELETE FROM cart WHERE email = ? AND product_id = ?", (email, product_id))
        else:
            cursor.execute("UPDATE cart SET quantity = ? WHERE email = ? AND product_id = ?", 
                            (quantity, email, product_id))
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e


def record_order(email, order_date, cart_items, totalPrice):
    db = get_db()
    cursor = db.cursor()
    try:
        # Insert the order into the orders table
        cursor.execute("INSERT INTO orders (email, order_date, total_price) VALUES (?, ?, ?)", (email, order_date, totalPrice))
        order_id = cursor.lastrowid
        
        print(cart_items)
        # Insert the order items into the order_items table
        for cart_item in cart_items:
            cursor.execute("INSERT INTO order_items (orderID, product_name, quantity) VALUES (?, ?, ?)", 
                            (order_id, cart_item[0], cart_item[2]))
        print(2)
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e
    

def update_inventory():
    db = get_db()
    cursor = db.cursor()
    try:
        # Update the inventory based on the cart items
        cursor.execute("SELECT c.product_id, c.quantity, p.name FROM cart c JOIN products p ON c.product_id = p.productID")
        cart_items = cursor.fetchall()
        print(cart_items)
        
        for cart_item in cart_items:
            cursor.execute("SELECT quantity FROM inventory WHERE productID = ?", (cart_item[0],))
            inventory_quantity = cursor.fetchone()[0]
            
            if inventory_quantity < cart_item[1]:
                raise Exception(f"Not enough inventory for product '{cart_item[2]}'. Available: {inventory_quantity}, Requested: {cart_item[1]}")

            cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE productID = ?", 
                            (cart_item[1], cart_item[0]))
        
        db.commit()
        cursor.close()

    except Exception as e:
        db.rollback()
        cursor.close()
        raise e