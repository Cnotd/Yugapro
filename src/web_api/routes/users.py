"""User, profile-history, and admin routes."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from src.auth import hash_password
from src.web_api.security import admin_required, api_role, db_role, login_required


users_bp = Blueprint("users", __name__)


@users_bp.get("/users")
@login_required
@admin_required
def list_users(user):
    context = current_app.config["YOGA_CONTEXT"]
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    users = context.db.list_users(limit=limit, offset=offset)
    return jsonify([_public_user(item) for item in users])


@users_bp.post("/users")
@login_required
@admin_required
def create_user(user):
    context = current_app.config["YOGA_CONTEXT"]
    data = request.get_json(force=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    email = data.get("email", "").strip()
    role = db_role(data.get("role", "learner"))

    if role is None:
        return jsonify({"error": "Only learner and admin roles are supported"}), 400
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if context.db.get_user_by_username(username):
        return jsonify({"error": "Username already exists"}), 409

    user_id = context.db.create_user(username, hash_password(password), email, role=role)
    return jsonify(
        {
            "id": user_id,
            "username": username,
            "email": email,
            "role": api_role(role),
        }
    )


@users_bp.put("/users/<int:user_id>")
@login_required
@admin_required
def update_user(user, user_id):
    context = current_app.config["YOGA_CONTEXT"]
    data = request.get_json(force=True) or {}
    updated = False

    if "role" in data and data.get("role") is not None:
        role = db_role(data.get("role", ""))
        if role is None:
            return jsonify({"error": "Only learner and admin roles are supported"}), 400
        updated = context.db.update_user_role(user_id, role)

    if "is_active" in data:
        updated = context.db.set_user_active(user_id, bool(data["is_active"])) or updated

    if not updated:
        return jsonify({"error": "User update failed"}), 400

    user_record = context.db.get_user_by_id(user_id)
    return jsonify(_public_user(user_record) if user_record else {"id": user_id})


@users_bp.get("/user/assessments")
@login_required
def list_user_assessments(user):
    context = current_app.config["YOGA_CONTEXT"]
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    return jsonify(context.db.get_user_assessments(user["id"], limit=limit, offset=offset))


@users_bp.get("/admin/stats")
@login_required
@admin_required
def admin_stats(user):
    context = current_app.config["YOGA_CONTEXT"]
    stats = context.db.get_system_overview()
    return jsonify(
        {
            "total_assessments": stats.get("total_assessments", 0),
            "avg_score": stats.get("average_score", 0),
            "total_users": stats.get("total_users", 0),
            "today_assessments": stats.get("today_assessments", 0),
            "active_users": stats.get("active_users", 0),
            "pose_types": stats.get("pose_types", 0),
        }
    )


def _public_user(user: dict) -> dict:
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "email": user.get("email"),
        "role": api_role(user.get("role", "user")),
        "is_active": bool(user.get("is_active", 1)),
        "created_at": user.get("created_at"),
        "last_login": user.get("last_login"),
    }
