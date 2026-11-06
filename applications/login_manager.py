import hashlib
import hmac
from werkzeug.security import generate_password_hash, check_password_hash
from applications.database import *
import re

def validate_email(email):
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(email_pattern, email) is not None

def validate_phone_number(phone_number):
    numeric_phone = re.sub(r'\D', '', phone_number)
    return len(numeric_phone) == 10

def _password_matches(stored, password):
    """Check a password against a stored hash.

    Accepts werkzeug hashes and the legacy unsalted SHA-256 hex digests
    used by older versions of this app.
    """
    if stored.startswith(("pbkdf2:", "scrypt:")):
        return check_password_hash(stored, password)
    legacy = hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(stored, legacy)


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
            if _password_matches(user[1], password):
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
        if not password or len(password) < 6:
            raise Exception("Password must be at least 6 characters")
        hashed_password = generate_password_hash(password)
        query_1 = "SELECT * FROM users WHERE email=?"
        cursor.execute(query_1, (email,))
        existing_user = cursor.fetchone()
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
    
    query = "SELECT password FROM managers WHERE email=?"
    cursor.execute(query, (email,))
    manager = cursor.fetchone()

    cursor.close()

    if manager and password and _password_matches(manager[0], password):
        return True
    else:
        raise Exception("Invalid email or password. Please try again.")
