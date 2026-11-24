from functools import wraps

from flask import g, jsonify, request

from app.models import User
from app.security import decode_access_token

COOKIE_NAME = "access_token"


def error_response(message, status=400, errors=None):
    """Consistent JSON errors: {"error": "...", "errors": {...}}. The frontend (api.js) reads "error"."""
    body = {"error": message}
    if errors:
        body["errors"] = errors
    return jsonify(body), status


def _get_token():
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip() or None
    return None


def login_required(view):
    """Decorator: returns 401 JSON unless a valid login token is present."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            return error_response("Authentication required", 401)
        g.current_user = user
        return view(*args, **kwargs)

    return wrapper


def current_user():
    """Load the logged-in user from the access_token cookie / Bearer header."""
    if "current_user" in g:
        return g.current_user
    token = _get_token()
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except Exception:
        return None
    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        return None
    try:
        user = User.query.get(int(user_id))
    except Exception:
        return None
    g.current_user = user
    return user
