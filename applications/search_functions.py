from applications.database import *

def search_products_in_db(search_query, min_price, max_price,
                            min_manufacture_date='', max_manufacture_date='',
                            min_expiry_date='', max_expiry_date='', exclude_out_of_stock=False):
    
    db = get_db()
    cursor = db.cursor()
    try:
        query = """
        SELECT *
        FROM products
        WHERE LOWER(name) LIKE ?
        AND price >= ? AND price <= ?
        """
        params = [f"%{search_query}%", min_price, max_price]
        
        if min_manufacture_date:
            query += " AND manufacture_date >= ?"
            params.append(min_manufacture_date)
        if max_manufacture_date:
            query += " AND manufacture_date <= ?"
            params.append(max_manufacture_date)
        if min_expiry_date:
            query += " AND expiry_date >= ?"
            params.append(min_expiry_date)
        if max_expiry_date:
            query += " AND expiry_date <= ?"
            params.append(max_expiry_date)

        if exclude_out_of_stock:
            query += " AND productID IN (SELECT productID FROM inventory WHERE quantity > 0)"
        
        # Execute the query and fetch the rows
        cursor.execute(query, params)
        products_list_1 = cursor.fetchall()
        
        cursor.close()
        # return products_list
        products_list = [
            {
                "productID": product[0],
                "name": product[1],
                "manufacture_date": product[2],
                "expiry_date": product[3],
                "price": product[4],
                "dynamic_price": product[5],
                "is_recommended": product[6],
                "categoryID": product[7],
                "unit": product[8]
            }
            for product in products_list_1
        ]
        
        return products_list
    except Exception as e:
        cursor.close()
        raise e


def search_categories_in_db(search_query):
    db = get_db()
    cursor = db.cursor()
    
    query = """
        SELECT * FROM categories
        WHERE LOWER(category_name) LIKE ?
    """
    results = cursor.execute(query, ('%' + search_query + '%',)).fetchall()
    
    print(results)
    cursor.close()
    return results

def get_products_by_category_search(category_ids, min_price, max_price,
                                        min_manufacture_date, max_manufacture_date,
                                        min_expiry_date, max_expiry_date, exclude_out_of_stock=False):
    # Query to get products from specified categories and apply filters
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Generate placeholders for the IN clause using parameter binding
        category_id = category_ids[0][0]
        print(category_id)
        query = """
        SELECT * FROM products
        WHERE categoryID = ?
        AND price >= ? AND price <= ?
        AND (manufacture_date >= ? OR ? = '')
        AND (manufacture_date <= ? OR ? = '')
        AND (expiry_date >= ? OR ? = '')
        AND (expiry_date <= ? OR ? = '')
        """

        if exclude_out_of_stock:
            query += " AND productID IN (SELECT productID FROM inventory WHERE quantity > 0)"
        # Concatenate category IDs and other filter parameters
        params = [category_id, min_price, max_price,
                                min_manufacture_date, min_manufacture_date,
                                max_manufacture_date, max_manufacture_date,
                                min_expiry_date, min_expiry_date,
                                max_expiry_date, max_expiry_date]
        
        cursor.execute(query, params)
        filtered_products = cursor.fetchall()
        cursor.close()
        print("Filtered products", filtered_products)
        products_list = [
            {
                "productID": product[0],
                "name": product[1],
                "manufacture_date": product[2],
                "expiry_date": product[3],
                "price": product[4],
                "dynamic_price": product[5],
                "is_recommended": product[6],
                "categoryID": product[7],
                "unit": product[8]
            }
            for product in filtered_products
        ]
        
        return products_list
    except Exception as e:
        cursor.close()
        raise e
