from applications.database import *
from applications.categories_functions import *

def add_category_to_db(category_name):
    db = get_db()
    cursor = db.cursor()
    try:
        # Query to insert a new category into the categories table
        query = "INSERT INTO categories (category_name) VALUES (?)"
        
        cursor.execute(query, (category_name,))
        
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e


def remove_category_from_db(category_id):
    db = get_db()
    cursor = db.cursor()
    try: 
        cursor.execute("DELETE FROM products WHERE categoryID = ?",(category_id,))

        query = "DELETE FROM categories WHERE categoryID = ?"        
        cursor.execute(query, (category_id,))
        
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e


def add_product_to_category_in_db(category, product_name, quantity, manufacture_date, expiry_date, price, unit):
    categories = get_categories()
    db = get_db()
    cursor = db.cursor()

    try:
        category_id = None

        for existing_category_id, existing_category_name in categories:
            if category == existing_category_name:
                category_id = existing_category_id
                break

        if category_id is None:
            # Category doesn't exist, insert it
            cursor.execute("INSERT INTO categories (category_name) VALUES (?)", (category,))
            db.commit()
            category_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO products (name, manufacture_date, expiry_date, price, unit, categoryID) VALUES (?, ?, ?, ?, ?, ?)",
            (product_name, manufacture_date, expiry_date, price, unit, category_id)
        )
        
        product_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO inventory (productID, quantity) VALUES (?, ?)", (product_id, quantity))
        
        db.commit()
        cursor.close()
        
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e




def remove_product_from_db(product_id):
    # Query to delete a product from the products table
    db = get_db()
    cursor = db.cursor()

    try:
        # Get the product's category ID before deleting it
        cursor.execute("SELECT categoryID FROM products WHERE productID = ?", (product_id,))
        category_id = cursor.fetchone()[0]
        
        # Delete from the inventory table
        cursor.execute("DELETE FROM inventory WHERE productID = ?", (product_id,))
        query = "DELETE FROM products WHERE productID = ?"
        cursor.execute(query, (product_id,))

        # Check if the category becomes empty
        cursor.execute("SELECT COUNT(*) FROM products WHERE categoryID = ?", (category_id,))
        product_count_in_category = cursor.fetchone()[0]
        if product_count_in_category == 0:
            # Delete the category from categories table
            cursor.execute("DELETE FROM categories WHERE categoryID = ?", (category_id,))
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e


def get_categories_with_products_from_db():
    try:
        db = get_db()
        cursor = db.cursor()
        # Query to fetch categories along with their products from the database
        query = """
        SELECT c.categoryID, c.category_name, p.productID, p.name AS product_name, p.price, p.unit, i.quantity, p.manufacture_date, p.expiry_date
        FROM categories AS c
        LEFT JOIN products AS p ON c.categoryID = p.categoryID
        LEFT JOIN inventory AS i ON p.productID = i.productID
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        categories_with_products = {}    
        # organize data into the dictionary
        for row in rows:
            category_id, category_name, product_id, product_name, price, unit, quantity, manufacture_date, expiry_date = row
            product = {'productID': product_id, 'product_name': product_name, 'price':price, 'unit':unit, 'quantity': quantity, 'manufacture_date':manufacture_date, 'expiry_date':expiry_date}
            
            if category_id not in categories_with_products:
                categories_with_products[category_id] = {'categoryID': category_id, 'category_name': category_name, 'products': []}
            
            categories_with_products[category_id]['products'].append(product)
        
        cursor.close()
        return list(categories_with_products.values())
    except Exception as e:
        cursor.close()
        raise e


def get_product_by_id(product_id):
    db = get_db()
    cursor = db.cursor()

    try:
        query = """
                SELECT p.name, c.category_name, i.quantity, p.price, p.unit, p.manufacture_date, p.expiry_date
                FROM categories AS c
                JOIN products AS p ON c.categoryID = p.categoryID
                JOIN inventory AS i ON p.productID = i.productID
                WHERE p.productID = ?
                """
        cursor.execute(query, (product_id,))
        product = cursor.fetchone()
        cursor.close()
        print(product)
        return product
    except Exception as e:
        cursor.close()
        raise e
    

def update_product_in_db(product_id, product_name, category, quantity, price, unit, manufacture_date, expiry_date):
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("SELECT categoryID FROM categories WHERE category_name=?", (category,))
        category_id = cursor.fetchone()[0]
        # Update the product details
        cursor.execute(
            "UPDATE products SET name=?, manufacture_date=?, expiry_date=?, price=?, unit=?, categoryID=? WHERE productID=?",
            (product_name, manufacture_date, expiry_date, price, unit, category_id, product_id)
        )
        
        # Update the inventory quantity
        cursor.execute("UPDATE inventory SET quantity=? WHERE productID=?", (quantity, product_id))
        
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e
    

