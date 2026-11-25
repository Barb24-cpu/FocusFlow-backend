from flask import Blueprint, current_app, jsonify, request

from app.database import db
from app.deps import COOKIE_NAME, current_user, error_response, login_required
from app.models import User
from app.schemas import ValidationError, user_to_dict, validate_login, validate_register
from app.security import create_access_token, hash_password, verify_password

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


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


@auth_bp.post("/register")
def register():
    try:
        data = validate_register(_json_body())
    except ValidationError as exc:
        return error_response(exc.message, 400, exc.errors)

    if User.query.filter_by(email=data["email"]).first():
        return error_response(
            "An account with this email already exists",
            409,
            {"email": "An account with this email already exists"},
        )

    user = User(
        name=data["name"],
        email=data["email"],
        password_hash=hash_password(data["password"]),
    )
    try:
        db.session.add(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        if User.query.filter_by(email=data["email"]).first():
            return error_response("An account with this email already exists", 409)
        raise

    return jsonify({"message": "Account created", "user": user_to_dict(user)}), 201


@auth_bp.post("/login")
def login():
    try:
        data = validate_login(_json_body())
    except ValidationError as exc:
        return error_response(exc.message, 400, exc.errors)

    user = User.query.filter_by(email=data["email"]).first()
    if user is None or not verify_password(data["password"], user.password_hash):
        return error_response("Invalid email or password", 401)

    token = create_access_token({"sub": str(user.id), "user_id": user.id})
    response = jsonify({"user": user_to_dict(user)})
    return _set_auth_cookie(response, token)


@auth_bp.post("/logout")
def logout():
    response = jsonify({"message": "Logged out"})
    response.delete_cookie(COOKIE_NAME, **_cookie_options())
    return response


@auth_bp.get("/me")
@login_required
def me():
    return jsonify({"user": user_to_dict(current_user())})
