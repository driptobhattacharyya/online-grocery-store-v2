from applications.database import *

def get_categories():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    cursor.close()
    return categories

def get_products_by_category(category_id):
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("SELECT * FROM products WHERE categoryID = ?", (category_id,))
        product_rows = cursor.fetchall()
        cursor.close()
        return product_rows
        # products = []
        # for row in product_rows:
        #     product = {
        #         "productID": row[0],
        #         "name": row[1],
        #         "manufacture_date": row[2],
        #         "expiry_date": row[3],
        #         "price": row[4],
        #         "dynamic_price": row[5],
        #         "is_recommended": bool(row[6]),  # Convert 0 or 1 to boolean
        #         "categoryID": row[7],
        #         "unit": row[8]
        #     }
        #     products.append(product)
    except Exception as e:
        cursor.close()
        raise e

def get_10_products():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products INNER JOIN inventory ON products.productID = inventory.productID")
    products = cursor.fetchall()
    cursor.close()
    return products
