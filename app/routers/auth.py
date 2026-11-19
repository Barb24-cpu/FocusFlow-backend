# TODO: Implement this file
"""
routers/auth.py - Register, login, logout and "who am I" endpoints (FF-2).

Endpoints (the frontend's authService.js calls exactly these):
    POST /auth/register   {name | username, email, password}  -> 201 {"user": {...}}
    POST /auth/login      {email, password}                   -> 200 {"user": {...}} + httpOnly cookie
    POST /auth/logout                                         -> 200 {"message": ...} + cookie cleared
    GET  /auth/me                                             -> 200 {"user": {...}} or 401

"""
from flask import Blueprint, current_app, jsonify, request

from app.database import database
from app.deps import COOKIE_NAME, current_user, error_response, login_required
from app.models import userfrom app.schemas import ValidationError, user_to_dict, validate_login, validate_register
from app.security import create_access_token, hash_password, verify_password

auth_bp =Blueprint("auth", __name__, url_prefix="/auth")


def _json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _cookie_options():
    return {
        "path": "/",
        "httponly": True,
        "secure": bool(current_app.config.get("COOKIE_SECURE", False)),
        "samesite": current_app.config.get("COOKIE_SAMESITE", "Lax"),
    }


def _set_auth_cookie(response, token):
    minutes = int(current_app.config.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))
    response.set_cookie(COOKIE_NAME, token, max_age=minutes * 60, **_cookie_options())
    return response
