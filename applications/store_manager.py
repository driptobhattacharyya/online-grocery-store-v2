from applications.database import *
from applications.user_info import fetch_user_info

def manager_check(email):
    db = get_db()
    cursor = db.cursor()
    try:
        query = "SELECT * FROM store_manager WHERE email=? AND manager_status='approved' "
        cursor.execute(query, (email,))
        manager = cursor.fetchone()
        cursor.close()
        if manager is None:
            return False
        else:
            return True
    except Exception as e:
        cursor.close()
        raise e
    

def manager_status_check(email):
    db = get_db()
    cursor = db.cursor()
    try:
        query = "SELECT manager_status FROM store_manager WHERE email=? "
        cursor.execute(query, (email,))
        manager_status = cursor.fetchone()
        if manager_status is None:
            manager_status = "Not Applied"
        else:
            manager_status = manager_status[0]
        print(f"Manager status: {manager_status}")
        return manager_status
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e
    
def add_manager_apply(email):
    db = get_db()
    cursor = db.cursor()
    try:
        query = "INSERT INTO store_manager (email, manager_status) VALUES (?, 'pending')"
        cursor.execute(query, (email,))
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e
    
def get_manager_requests():
    db = get_db()
    cursor = db.cursor()
    try:
        query = "SELECT email FROM store_manager WHERE manager_status='pending'"
        cursor.execute(query)
        manager_requests = cursor.fetchall()
        cursor.close()
        requests = []
        for email in manager_requests:
            user = fetch_user_info(email[0])
            requests.append(user)
        return requests
    except Exception as e:
        cursor.close()
        raise e
    
def approve_manager(email):
    db = get_db()
    cursor = db.cursor()
    try:
        query = "UPDATE store_manager SET manager_status='approved' WHERE email=?"
        cursor.execute(query, (email,))
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e
    
def deny_manager(email):
    db = get_db()
    cursor = db.cursor()
    try:
        query = "UPDATE store_manager SET manager_status='Denied' WHERE email=?"
        cursor.execute(query, (email,))
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e