from applications.database import *
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
import io
import base64
from datetime import date, timedelta

from datetime import date, timedelta

def generate_bar_chart():
    db = get_db()
    cursor = db.cursor()
    
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        query = """
            SELECT p.name AS product_name, SUM(oi.quantity) AS total_sales
            FROM products p
            JOIN order_items oi ON p.name = oi.product_name
            JOIN orders o ON oi.orderID = o.orderID
            WHERE o.order_date >= ? AND o.order_date <= ?
            GROUP BY p.productID
            ORDER BY total_sales DESC
            LIMIT 10
        """
        
        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()
        
        products = [row[0] for row in rows]
        sales = [row[1] for row in rows]
        
        plt.bar(products, sales)
        plt.xlabel('Products')
        plt.ylabel('Total Sales (Past Week)')
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        img_data = base64.b64encode(img_buffer.read()).decode()
        
        cursor.close()
        plt.close()
        return img_data
    
    except Exception as e:
        cursor.close()
        plt.close()
        raise e

    

def generate_pie_chart():
    db = get_db()
    cursor = db.cursor()

    try:
        query = """
            SELECT c.category_name, COUNT(p.productID) AS product_count
            FROM categories c
            LEFT JOIN products p ON c.categoryID = p.categoryID
            GROUP BY c.categoryID
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        categories = [row[0] for row in rows]
        counts = [row[1] for row in rows]
        
        plt.pie(counts, labels=categories, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')  
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        img_data = base64.b64encode(img_buffer.read()).decode()
        
        cursor.close()
        plt.close()
        return img_data

    except Exception as e:
        cursor.close()
        plt.close()
        raise e