from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import current_app, g, jsonify, request
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from app.extensions import db


def encode_token(user_id, role):
    payload = {
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
        "sub": str(user_id),
        "role": role,
    }

    return jwt.encode(
        payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256"
    )


def decode_token(token):
    return jwt.decode(
        token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
    )


def token_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return jsonify({"error": "Bearer token required"}), 401

        try:
            payload = decode_token(token)
            user_id = int(payload["sub"])
        except (ExpiredSignatureError, JWTError, KeyError, ValueError):
            return jsonify({"error": "Invalid or expired token"}), 401

        from app.models import User

        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"error": "User not found"}), 401

        g.current_user = user
        return view(*args, **kwargs)

    return wrapped_view


def roles_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def authorized_view(*args, **kwargs):
            if g.current_user.role not in allowed_roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return view(*args, **kwargs)

        return token_required(authorized_view)

    return decorator
