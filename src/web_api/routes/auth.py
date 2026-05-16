"""Authentication routes."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from src.auth import (
    create_session,
    hash_password,
    invalidate_access_token,
    invalidate_refresh_token,
    invalidate_user_sessions,
    refresh_session,
    verify_password,
)
from src.web_api.security import api_role, get_auth_token, login_required


auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    context = current_app.config["YOGA_CONTEXT"]
    data = request.get_json(force=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    email = data.get("email", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if context.db.get_user_by_username(username):
        return jsonify({"error": "Username already exists"}), 409

    user_id = context.db.create_user(username, hash_password(password), email, role="user")
    session = create_session(user_id)
    return jsonify(
        {
            "user": {
                "id": user_id,
                "username": username,
                "email": email,
                "role": "learner",
            },
            **session,
        }
    )


@auth_bp.post("/login")
def login():
    context = current_app.config["YOGA_CONTEXT"]
    data = request.get_json(force=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = context.db.get_user_by_username(username)
    if not user or not verify_password(password, user["password"]):
        return jsonify({"error": "Invalid username or password"}), 401
    if not user.get("is_active", 1):
        return jsonify({"error": "User is disabled"}), 403

    context.db.update_user_last_login(user["id"])
    session = create_session(user["id"])
    return jsonify(
        {
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user.get("email"),
                "role": api_role(user.get("role", "user")),
            },
            **session,
        }
    )


@auth_bp.post("/refresh")
def refresh_token():
    data = request.get_json(force=True) or {}
    refresh_token_value = data.get("refresh_token", "").strip()
    if not refresh_token_value:
        return jsonify({"error": "refresh_token is required"}), 400

    session = refresh_session(refresh_token_value)
    if not session:
        return jsonify({"error": "refresh_token is invalid or expired"}), 401
    return jsonify(session)


@auth_bp.post("/logout")
@login_required
def logout(user):
    token = get_auth_token()
    body = request.get_json(silent=True) or {}
    refresh_token_value = body.get("refresh_token")

    if token:
        invalidate_access_token(token)
    if refresh_token_value:
        invalidate_refresh_token(refresh_token_value)
    else:
        invalidate_user_sessions(user["id"])

    return jsonify({"message": "Logged out"})


@auth_bp.get("/me")
@login_required
def profile(user):
    return jsonify(
        {
            "id": user["id"],
            "username": user["username"],
            "email": user.get("email"),
            "role": api_role(user.get("role", "user")),
            "is_active": bool(user.get("is_active", 1)),
            "last_login": user.get("last_login"),
        }
    )
