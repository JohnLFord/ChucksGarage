from flask import g, jsonify, request
from marshmallow import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.blueprints.customer.schemas import student_schema
from app.blueprints.mechanic.schemas import teacher_schema
from app.extensions import db, limiter
from app.models import Student, Teacher, User
from app.utils.util import encode_token, roles_required, token_required

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
    existing_student = db.session.execute(
        select(Student).where(Student.email == normalized_email)
    ).scalar_one_or_none()
    if existing_user or existing_student:
        return jsonify({"error": "Email already registered"}), 409

    try:
        student_data = student_schema.load(
            {
                "name": payload.get("name"),
                "email": normalized_email,
                "date_of_birth": payload.get("date_of_birth"),
            }
        )
    except ValidationError as error:
        return jsonify(error.messages), 400

    student = Student(**student_data)
    user = User(
        email=normalized_email,
        password_hash=generate_password_hash(password),
        role="student",
        student=student,
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already registered"}), 409

    return jsonify(user_schema.dump(user)), 201


@user_bp.route("/students/<int:student_id>/promote-teacher", methods=["POST"])
@roles_required("admin")
def promote_student_to_teacher(student_id):
    user = db.session.execute(
        select(User).where(User.student_id == student_id)
    ).scalar_one_or_none()
    if user is None:
        return jsonify({"error": "Student account not found"}), 404
    if user.teacher_id is not None or user.role == "teacher":
        return jsonify({"error": "Account is already a teacher"}), 409

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON payload required"}), 400

    try:
        teacher_data = teacher_schema.load(
            {
                "name": payload.get("name") or user.student.name,
                "specialty": payload.get("specialty"),
                "experience": payload.get("experience"),
                "certification": payload.get("certification"),
            }
        )
    except ValidationError as error:
        return jsonify(error.messages), 400

    teacher = Teacher(**teacher_data)
    user.role = "teacher"
    user.teacher = teacher
    db.session.add(teacher)
    db.session.commit()
    return jsonify(user_schema.dump(user)), 200


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

    token = encode_token(user.id, user.role)

    return jsonify({"auth_token": token}), 200


@user_bp.route("/me", methods=["GET"])
@token_required
def me():
    user = g.current_user
    return jsonify(user_schema.dump(user)), 200
