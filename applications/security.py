import os
import re
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from applications.errors import AppError

EMAIL_PATTERN = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


def hash_password(password):
    return generate_password_hash(password, method="pbkdf2:sha256")


def verify_password(password, password_hash):
    if not password_hash:
        return False
    try:
        return check_password_hash(password_hash, password)
    except ValueError:
        return False


def validate_email(email):
    return bool(email) and EMAIL_PATTERN.match(email) is not None


def validate_phone_number(phone_number):
    digits = re.sub(r"\D", "", phone_number or "")
    return len(digits) == 10


def resolve_admin_email(raw_email):
    """Map the historical admin username to the configured admin email."""
    value = (raw_email or "").strip()
    if value.lower() == "admin":
        return os.environ.get("ADMIN_EMAIL", "admin@grocery.local")
    return value


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            role = get_jwt().get("role")
            if role not in roles:
                return jsonify({"error": "You are not authorized to perform this action."}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_fields(data, fields):
    data = data or {}
    missing = [field for field in fields if data.get(field) in (None, "")]
    if missing:
        raise AppError("Missing required fields: " + ", ".join(missing))
    return data
