"""Flask application factory for the thesis-aligned REST backend."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask
from flask_cors import CORS

from src.auth import hash_password
from src.web_api.context import ApiContext, build_context


def create_app(context: ApiContext | None = None) -> Flask:
    """Create the Flask API app without binding it to a port."""
    _strip_proxy_environment()

    app = Flask(__name__)
    CORS(app)
    app.config["YOGA_CONTEXT"] = context or build_context(Path(__file__).resolve().parents[2])

    with app.app_context():
        ensure_default_admin(app.config["YOGA_CONTEXT"])

    from src.web_api.routes.assessment import assessment_bp
    from src.web_api.routes.auth import auth_bp
    from src.web_api.routes.system import system_bp
    from src.web_api.routes.users import users_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api")
    app.register_blueprint(assessment_bp, url_prefix="/api/assessment")
    app.register_blueprint(system_bp, url_prefix="/api")
    return app


def ensure_default_admin(context: ApiContext) -> None:
    """Ensure the demo admin account exists and stores a hashed password."""
    password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin123")
    admin_user = context.db.get_user_by_username("admin")
    if not admin_user:
        context.db.create_user("admin", hash_password(password), "admin@example.com", role="admin")
        return

    stored = admin_user.get("password", "")
    if not isinstance(stored, str) or not stored.startswith(("pbkdf2:", "scrypt:")):
        context.db.update_user_password(admin_user["id"], hash_password(password))


def _strip_proxy_environment() -> None:
    """Avoid invisible local proxy settings blocking model API calls."""
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        os.environ.pop(name, None)
