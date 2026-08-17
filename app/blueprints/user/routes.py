from flask import g, jsonify, request
from marshmallow import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.blueprints.customer.schemas import customer_schema
from app.extensions import db, limiter
from app.models import Customer, User
from app.utils.util import encode_token, token_required

from . import user_bp
from .schemas import user_schema


@user_bp.route("/register", methods=["POST"])
@limiter.limit("5 per day")
def register():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON payload required"}), 400

    email = payload.get("email")
    password = payload.get("password")
    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "Email and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    normalized_email = email.strip().lower()
    if not normalized_email:
        return jsonify({"error": "Email is required"}), 400

    existing_user = db.session.execute(
        select(User).where(User.email == normalized_email)
    ).scalar_one_or_none()
    existing_customer = db.session.execute(
        select(Customer).where(Customer.email == normalized_email)
    ).scalar_one_or_none()
    if existing_user or existing_customer:
        return jsonify({"error": "Email already registered"}), 409

    try:
        customer_data = customer_schema.load(
            {
                "name": payload.get("name"),
                "email": normalized_email,
                "date_of_birth": payload.get("date_of_birth"),
            }
        )
    except ValidationError as error:
        return jsonify(error.messages), 400

    customer = Customer(**customer_data)
    user = User(
        email=normalized_email,
        password_hash=generate_password_hash(password),
        role="customer",
        customer=customer,
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already registered"}), 409

    return jsonify(user_schema.dump(user)), 201


@user_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON payload required"}), 400

    email = payload.get("email")
    password = payload.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "Email and password are required"}), 400

    user = db.session.execute(
        select(User).where(User.email == email.strip().lower())
    ).scalar_one_or_none()

    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Tests expect "access_token", NOT "auth_token"
    token = encode_token(user.id, user.role)

    return jsonify({"auth_token": token}), 200


@user_bp.route("/me", methods=["GET"])
@token_required
def me():
    user = g.current_user
    return jsonify(user_schema.dump(user)), 200
