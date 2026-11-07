"""HTTP error types, a route decorator that maps them to JSON responses, and
small request-validation helpers shared by the API controllers.

Every error response has the shape ``{"error": "<message>"}``.
"""
from datetime import date
from functools import wraps
from numbers import Number

from flask import current_app, jsonify, request
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    status = 400

    def __init__(self, message, status=None):
        super().__init__(message)
        self.message = message
        if status is not None:
            self.status = status


class BadRequest(ApiError):
    status = 400


class Unauthorized(ApiError):
    status = 401


class Forbidden(ApiError):
    status = 403


class NotFound(ApiError):
    status = 404


class Conflict(ApiError):
    status = 409


def error_response(message, status):
    return jsonify({"error": message}), status


def api_errors(view):
    """Turn ApiError into its status code; log anything else and return a generic 500."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except ApiError as e:
            return error_response(e.message, e.status)
        except HTTPException:
            # e.g. 413 from reading an oversized body: app.py renders it as JSON
            raise
        except Exception:
            current_app.logger.exception("Unhandled error in %s %s", request.method, request.path)
            return error_response("Something went wrong. Please try again later.", 500)

    return wrapper


def only_ok(response):
    """flask-caching ``response_filter``: cache successful responses only."""
    if isinstance(response, tuple):
        return len(response) < 2 or response[1] == 200
    return getattr(response, "status_code", 200) == 200


# --- request validation -----------------------------------------------------

def json_body():
    data = request.get_json(silent=True)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise BadRequest("Request body must be a JSON object")
    return data


def require_str(data, field, label=None):
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise BadRequest(f"{label or field} is required")
    return value.strip()


def positive_int(value, label, allow_zero=False):
    # bool is a subclass of int; reject it explicitly.
    if isinstance(value, bool):
        raise BadRequest(f"{label} must be a whole number")
    if isinstance(value, str):
        value = value.strip()
        if not value.lstrip("-").isdigit():
            raise BadRequest(f"{label} must be a whole number")
        value = int(value)
    elif isinstance(value, float) and value.is_integer():
        value = int(value)
    if not isinstance(value, int):
        raise BadRequest(f"{label} must be a whole number")
    if value < 0 or (value == 0 and not allow_zero):
        raise BadRequest(f"{label} must be {'zero or more' if allow_zero else 'greater than zero'}")
    return value


def number(value, label, positive=True):
    if isinstance(value, bool):
        raise BadRequest(f"{label} must be a number")
    if isinstance(value, str):
        try:
            value = float(value.strip())
        except ValueError:
            raise BadRequest(f"{label} must be a number")
    if not isinstance(value, Number) or value != value or value in (float("inf"), float("-inf")):
        raise BadRequest(f"{label} must be a number")
    if positive and value <= 0:
        raise BadRequest(f"{label} must be greater than zero")
    if value < 0:
        raise BadRequest(f"{label} cannot be negative")
    return float(value)


def iso_date(value, label):
    if not isinstance(value, str):
        raise BadRequest(f"{label} must be a date (YYYY-MM-DD)")
    try:
        return date.fromisoformat(value.strip()[:10]).isoformat()
    except ValueError:
        raise BadRequest(f"{label} must be a date (YYYY-MM-DD)")


def optional_date(value, label):
    """Search filters send "", 0 or null for "not set"."""
    if value in (None, "", 0):
        return ""
    return iso_date(value, label)
