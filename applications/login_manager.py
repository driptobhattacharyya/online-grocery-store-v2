import hashlib
import hmac
import re

from werkzeug.security import generate_password_hash, check_password_hash

from applications.database import get_db
from applications.http_errors import BadRequest, Conflict, Unauthorized

INVALID_CREDENTIALS = "Invalid email or password. Please try again."


def validate_email(email):
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return isinstance(email, str) and re.match(email_pattern, email) is not None


def validate_phone_number(phone_number):
    if not isinstance(phone_number, str):
        return False
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


def login(email, password):
    """Raise Unauthorized unless the shopper's credentials are valid.

    The same message is used for unknown e-mails and wrong passwords so the
    endpoint can't be used to discover which accounts exist.
    """
    cursor = get_db().cursor()
    try:
        cursor.execute("SELECT password FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
    finally:
        cursor.close()
    if not user or not _password_matches(user[0], password):
        raise Unauthorized(INVALID_CREDENTIALS)


def register_user(email, password, name, phone, address):
    """Create the login and the profile together, or neither."""
    if len(password) < 6:
        raise BadRequest("Password must be at least 6 characters")
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT 1 FROM users WHERE email=?", (email,))
        if cursor.fetchone() is not None:
            raise Conflict("Email already exists")
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)",
                       (email, generate_password_hash(password)))
        cursor.execute("INSERT INTO user_profiles (email, name, address, phone) VALUES (?, ?, ?, ?)",
                       (email, name, address, phone))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


def manager_login(email, password):
    """Admin login (the `managers` table holds the admin account)."""
    cursor = get_db().cursor()
    try:
        cursor.execute("SELECT password FROM managers WHERE email=?", (email,))
        manager = cursor.fetchone()
    finally:
        cursor.close()
    if not manager or not _password_matches(manager[0], password):
        raise Unauthorized(INVALID_CREDENTIALS)
