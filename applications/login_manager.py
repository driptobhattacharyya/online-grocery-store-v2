from applications.database import get_db
from applications.errors import AppError
from applications.security import (
    hash_password,
    validate_email,
    validate_phone_number,
    verify_password,
)


def user_role(email):
    db = get_db()
    row = db.execute("SELECT role FROM users WHERE email = ?", (email,)).fetchone()
    if not row:
        raise AppError("Email does not exist. Please try again.", 401)
    return row["role"]


def login(email, password):
    if not validate_email(email):
        raise AppError("Invalid email.", 401)
    db = get_db()
    user = db.execute(
        "SELECT email, password, role FROM users WHERE email = ?",
        (email.lower().strip(),),
    ).fetchone()
    if not user or not verify_password(password or "", user["password"]):
        raise AppError("Invalid email or password.", 401)
    return {"email": user["email"], "role": user["role"]}


def signup(email, password, name, phone_number, address):
    if not validate_email(email):
        raise AppError("Valid email required.")
    if not validate_phone_number(phone_number):
        raise AppError("Valid phone number required.")
    if not name or not str(name).strip():
        raise AppError("Name is required.")
    if not password or len(password) < 6:
        raise AppError("Password must be at least 6 characters.")
    email = email.lower().strip()
    db = get_db()
    existing = db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        raise AppError("Email already exists.")
    db.execute(
        "INSERT INTO users (email, password, role) VALUES (?, ?, 'customer')",
        (email, hash_password(password)),
    )
    db.execute(
        "INSERT INTO user_profiles (email, name, address, phone) VALUES (?, ?, ?, ?)",
        (email, name.strip(), address or "", phone_number),
    )
    db.commit()
    return email
