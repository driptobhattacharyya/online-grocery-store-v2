from flask import request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from applications.store_manager import manager_check


def is_admin():
    return get_jwt().get("role") == "admin"


def is_manager_or_admin():
    """Authorise from the server's own records, never from client-supplied flags."""
    return is_admin() or manager_check(get_jwt_identity())


def per_user_cache_key():
    """Cache key for flask-caching that keeps each user's responses separate."""
    verify_jwt_in_request()
    return f"view:{request.full_path}:{get_jwt().get('role', 'user')}:{get_jwt_identity()}"
