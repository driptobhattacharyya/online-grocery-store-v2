from applications.database import *


def get_coupon_codes_from_db():
    db = get_db()
    cursor = db.cursor()
    
    try:
    # Query to fetch all coupon codes from the coupons table
        query = """
                SELECT c.coupon_code, c.discount_percentage, COUNT(u.user_email) AS usage_count
                FROM coupons c
                LEFT JOIN used_coupons u ON c.coupon_code = u.coupon_code
                GROUP BY c.coupon_code, c.discount_percentage
                """
        
        cursor.execute(query)
        rows = cursor.fetchall()

        # Return the list of coupon codes as dictionaries
        result = [{'coupon_code': row[0], 'discount_percentage': row[1], 'count': row[2]} for row in rows]

        cursor.close()
        return result
    
    except Exception as e:
        cursor.close()
        raise e


def add_coupon_code_to_db(code, discount):
    existing_coupons = get_coupon_codes_from_db()
    for coupon in existing_coupons:
        if coupon['coupon_code'] == code:
            raise Exception('Coupon code already exists')
    
    db = get_db()
    cursor = db.cursor()
    
    try:
    # Query to insert a new coupon code into the coupons table
        query = "INSERT INTO coupons (coupon_code, discount_percentage) VALUES (?, ?)"
        
        cursor.execute(query, (code, discount))
        
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e


def remove_coupon_code_from_db(coupon_code):
    db = get_db()
    cursor = db.cursor()
    
    try:
    # Query to delete a coupon code from both coupons and used_coupons tables
        delete_coupon_query = "DELETE FROM coupons WHERE coupon_code = ?"
        delete_used_coupon_query = "DELETE FROM used_coupons WHERE coupon_code = ?"
        
        cursor.execute(delete_coupon_query, (coupon_code,))
        cursor.execute(delete_used_coupon_query, (coupon_code,))
        
        db.commit()
        cursor.close()

    except Exception as e:
        db.rollback()
        cursor.close()
        raise e