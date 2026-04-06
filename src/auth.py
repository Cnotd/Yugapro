"""用户认证与会话管理模块"""

import secrets
import time
from functools import wraps
from typing import Optional, Dict
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

ACCESS_TTL = 15 * 60
REFRESH_TTL = 7 * 24 * 3600

_access_sessions: Dict[str, Dict] = {}
_refresh_sessions: Dict[str, Dict] = {}


def hash_password(password: str) -> str:
    return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def _create_token(ttl: int) -> (str, float):
    token = secrets.token_urlsafe(32)
    expires_at = time.time() + ttl
    return token, expires_at


def create_access_token(user_id: int) -> str:
    token, expires_at = _create_token(ACCESS_TTL)
    _access_sessions[token] = {
        'user_id': user_id,
        'expires_at': expires_at
    }
    return token


def create_refresh_token(user_id: int) -> str:
    token, expires_at = _create_token(REFRESH_TTL)
    _refresh_sessions[token] = {
        'user_id': user_id,
        'expires_at': expires_at
    }
    return token


def create_session(user_id: int) -> Dict[str, object]:
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': ACCESS_TTL,
        'refresh_expires_in': REFRESH_TTL
    }


def get_user_id_from_access_token(token: str) -> Optional[int]:
    if not token:
        return None
    session = _access_sessions.get(token)
    if not session:
        return None
    if session['expires_at'] < time.time():
        _access_sessions.pop(token, None)
        return None
    return session['user_id']


def get_user_id_from_refresh_token(token: str) -> Optional[int]:
    if not token:
        return None
    session = _refresh_sessions.get(token)
    if not session:
        return None
    if session['expires_at'] < time.time():
        _refresh_sessions.pop(token, None)
        return None
    return session['user_id']


def invalidate_access_token(token: str) -> None:
    _access_sessions.pop(token, None)


def invalidate_refresh_token(token: str) -> None:
    _refresh_sessions.pop(token, None)


def invalidate_user_sessions(user_id: int) -> None:
    for token in list(_access_sessions.keys()):
        if _access_sessions[token]['user_id'] == user_id:
            _access_sessions.pop(token, None)
    for token in list(_refresh_sessions.keys()):
        if _refresh_sessions[token]['user_id'] == user_id:
            _refresh_sessions.pop(token, None)


def refresh_session(refresh_token: str) -> Optional[Dict[str, object]]:
    user_id = get_user_id_from_refresh_token(refresh_token)
    if not user_id:
        return None

    # 旧 refresh token 只可使用一次
    invalidate_refresh_token(refresh_token)
    access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)
    return {
        'access_token': access_token,
        'refresh_token': new_refresh_token,
        'expires_in': ACCESS_TTL,
        'refresh_expires_in': REFRESH_TTL
    }


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()

        user_id = get_user_id_from_access_token(token) if token else None
        if user_id is None:
            return jsonify({'error': 'Unauthorized'}), 401

        return func(user_id=user_id, *args, **kwargs)

    return wrapper
