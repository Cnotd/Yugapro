"""HTTP authentication helpers for route modules."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Optional

from flask import current_app, jsonify, request

from src.auth import get_user_id_from_access_token


def get_auth_token() -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return ""


def get_authenticated_user() -> Optional[dict]:
    token = get_auth_token()
    user_id = get_user_id_from_access_token(token)
    if not user_id:
        return None
    return current_app.config["YOGA_CONTEXT"].db.get_user_by_id(user_id)


def login_required(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        user = get_authenticated_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        return func(user=user, *args, **kwargs)

    return wrapper


def admin_required(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(user: dict, *args: Any, **kwargs: Any) -> Any:
        if user.get("role") != "admin":
            return jsonify({"error": "Forbidden"}), 403
        return func(user=user, *args, **kwargs)

    return wrapper


def api_role(db_role: str) -> str:
    return "learner" if db_role == "user" else db_role


def db_role(api_value: str) -> Optional[str]:
    if api_value in {"learner", "user", ""}:
        return "user"
    if api_value == "admin":
        return "admin"
    return None
