from applications.database import get_db
from applications.errors import AppError
from applications.user_info import fetch_user_info


def manager_check(email):
    db = get_db()
    row = db.execute("SELECT role FROM users WHERE email = ?", (email,)).fetchone()
    return bool(row and row["role"] in ("manager", "admin"))


def manager_status_check(email):
    db = get_db()
    role = db.execute("SELECT role FROM users WHERE email = ?", (email,)).fetchone()
    if role and role["role"] == "admin":
        return "Admin"
    row = db.execute(
        "SELECT manager_status FROM store_manager WHERE email = ?",
        (email,),
    ).fetchone()
    if not row:
        return "Not Applied"
    return row["manager_status"]


def add_manager_apply(email):
    db = get_db()
    role = db.execute("SELECT role FROM users WHERE email = ?", (email,)).fetchone()
    if role and role["role"] in ("manager", "admin"):
        raise AppError("You already have manager access.")
    existing = db.execute(
        "SELECT manager_status FROM store_manager WHERE email = ?",
        (email,),
    ).fetchone()
    if existing and existing["manager_status"] == "pending":
        raise AppError("Your application is already pending.")
    if existing:
        db.execute(
            "UPDATE store_manager SET manager_status = 'pending' WHERE email = ?",
            (email,),
        )
    else:
        db.execute(
            "INSERT INTO store_manager (email, manager_status) VALUES (?, 'pending')",
            (email,),
        )
    db.commit()


def get_manager_requests():
    db = get_db()
    rows = db.execute(
        "SELECT email FROM store_manager WHERE manager_status = 'pending'"
    ).fetchall()
    return [fetch_user_info(row["email"]) for row in rows]


def approve_manager(email):
    db = get_db()
    row = db.execute(
        "SELECT email FROM store_manager WHERE email = ?", (email,)
    ).fetchone()
    if not row:
        raise AppError("Manager request not found.", 404)
    db.execute(
        "UPDATE store_manager SET manager_status = 'approved' WHERE email = ?",
        (email,),
    )
    db.execute("UPDATE users SET role = 'manager' WHERE email = ?", (email,))
    db.commit()


def deny_manager(email):
    db = get_db()
    row = db.execute(
        "SELECT email FROM store_manager WHERE email = ?", (email,)
    ).fetchone()
    if not row:
        raise AppError("Manager request not found.", 404)
    db.execute(
        "UPDATE store_manager SET manager_status = 'Denied' WHERE email = ?",
        (email,),
    )
    db.execute(
        "UPDATE users SET role = 'customer' WHERE email = ? AND role != 'admin'",
        (email,),
    )
    db.commit()
