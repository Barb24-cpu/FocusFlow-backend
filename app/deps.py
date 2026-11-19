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


