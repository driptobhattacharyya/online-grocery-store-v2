from applications.database import get_db
from applications.http_errors import Conflict, NotFound
from applications.user_info import fetch_user_info


def manager_check(email):
    cursor = get_db().cursor()
    try:
        cursor.execute("SELECT 1 FROM store_manager WHERE email=? AND manager_status='approved'", (email,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()


def manager_status_check(email):
    cursor = get_db().cursor()
    try:
        cursor.execute("SELECT manager_status FROM store_manager WHERE email=?", (email,))
        row = cursor.fetchone()
    finally:
        cursor.close()
    return row[0] if row else "Not Applied"


def add_manager_apply(email):
    """Record a request to become a store manager.

    A user whose earlier request was denied may apply again; a pending or
    approved user may not.
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT manager_status FROM store_manager WHERE email=?", (email,))
        row = cursor.fetchone()
        if row and row[0] == "pending":
            raise Conflict("You have already applied for manager status.")
        if row and row[0] == "approved":
            raise Conflict("You are already a store manager.")
        cursor.execute(
            "INSERT OR REPLACE INTO store_manager (email, manager_status) VALUES (?, 'pending')", (email,)
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


def get_manager_requests():
    cursor = get_db().cursor()
    try:
        cursor.execute("SELECT email FROM store_manager WHERE manager_status='pending'")
        emails = [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()
    requests = []
    for email in emails:
        user = fetch_user_info(email)
        requests.append(user or {'email': email, 'name': None, 'address': None, 'phone_no': None})
    return requests


def _decide_request(email, status):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE store_manager SET manager_status=? WHERE email=? AND manager_status='pending'",
            (status, email),
        )
        if cursor.rowcount == 0:
            raise NotFound("No pending manager request for this user.")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


def approve_manager(email):
    _decide_request(email, "approved")


def deny_manager(email):
    _decide_request(email, "Denied")
