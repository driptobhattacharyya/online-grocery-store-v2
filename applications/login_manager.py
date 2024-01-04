import hashlib
from applications.database import *
import re

def validate_email(email):
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(email_pattern, email) is not None

def validate_phone_number(phone_number):
    numeric_phone = re.sub(r'\D', '', phone_number)
    return len(numeric_phone) == 10

def get_user(email):
    db = get_db()
    cursor = db.cursor()
    try:
        query = "SELECT * FROM user_profiles WHERE email=?"
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        cursor.close()
        return user
    except Exception as e:
        cursor.close()
        raise e

def login(email, password):
    db = get_db()
    cursor = db.cursor()
    if not validate_email(email): raise Exception("Invalid email")
    
    try:
        query = "SELECT * FROM users WHERE email=?"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if user:
            stored_hashed_password = user[1]
            input_hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            if stored_hashed_password == input_hashed_password:
                cursor.close()
                return
            else:
                raise Exception("Invalid password. Please try again.")        
        else:
            raise Exception("Email does not exist. Please try again.")
    except Exception as e:
        cursor.close()
        raise e



def signup(email, password):
    db = get_db()
    cursor = db.cursor()
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        query_1 = "SELECT * FROM users WHERE email=?"
        cursor.execute(query_1, (email,))
        existing_user = cursor.fetchone()
        print(existing_user)
        if existing_user != None:
            raise Exception("Email already exists")
        query = "INSERT INTO users (email, password) VALUES (?, ?)"
        cursor.execute(query, (email, hashed_password))
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e


def manager_login(email, password):
    db = get_db()
    cursor = db.cursor()
    
    query = "SELECT * FROM managers WHERE email=? AND password=?"
    cursor.execute(query, (email, password))
    manager = cursor.fetchone()

    cursor.close()

    if manager:
        return True
    else:
        raise Exception("Invalid email or password. Please try again.")
