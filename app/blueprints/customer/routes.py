from flask import g, jsonify, request
from marshmallow import ValidationError
from sqlalchemy import select

from app.extensions import db, limiter
from app.csv_export import csv_response
from app.models import Student
from app.utils.util import roles_required, token_required

from . import customers_bp
from .schemas import student_schema, students_schema


@customers_bp.route("/", methods=["POST"])
@limiter.limit("5 per day")
@roles_required("admin")
def create_customer():
    try:
        student_data = student_schema.load(request.json)
    except ValidationError as error:
        return jsonify(error.messages), 400

    query = select(Student).where(Student.email == student_data["email"])
    existing_student = db.session.execute(query).scalar_one_or_none()
    if existing_student:
        return jsonify({"error": "Email already exists"}), 400

    new_student = Student(**student_data)
    db.session.add(new_student)
    db.session.commit()
    return student_schema.jsonify(new_student), 201


@customers_bp.route("/", methods=["GET"])
@roles_required("admin", "teacher")
@roles_required("admin", "teacher")
def get_customers():
    query = select(Student)
    search = request.args.get("search", "", type=str)
    if search:
        query = query.where(Student.name.ilike(f"%{search}%"))

    if request.args.get("sort", "") == "name":
        query = query.order_by(Student.name)

    offset = request.args.get("offset", 0, type=int)
    if offset:
        query = query.offset(offset)

    limit = request.args.get("limit", type=int)
    if limit is not None:
        query = query.limit(limit)

    students = db.session.execute(query).scalars().all()
    return students_schema.jsonify(students), 200


@customers_bp.route("/export.csv", methods=["GET"])
@roles_required("admin", "teacher")
def export_customers():
    students = db.session.execute(select(Student).order_by(Student.id)).scalars().all()
    rows = [
        {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "date_of_birth": student.date_of_birth.isoformat(),
        }
        for student in students
    ]
    return csv_response("students.csv", rows, ["id", "name", "email", "date_of_birth"])


@customers_bp.route("/<int:customer_id>", methods=["GET"])
@token_required
def get_customer(customer_id):
    student = db.session.get(Student, customer_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    if g.current_user.role == "student" and g.current_user.student_id != customer_id:
        return jsonify({"error": "Insufficient permissions"}), 403
    if g.current_user.role not in {"admin", "teacher", "student"}:
        return jsonify({"error": "Insufficient permissions"}), 403

    return student_schema.jsonify(student), 200


@customers_bp.route("/<int:customer_id>", methods=["PUT"])
@token_required
def update_customer(customer_id):
    student = db.session.get(Student, customer_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    if g.current_user.role == "student" and g.current_user.student_id != customer_id:
        return jsonify({"error": "Insufficient permissions"}), 403
    if g.current_user.role not in {"admin", "student"}:
        return jsonify({"error": "Insufficient permissions"}), 403

    try:
        student_data = student_schema.load(request.json, partial=True)
    except ValidationError as error:
        return jsonify(error.messages), 400

    for key, value in student_data.items():
        setattr(student, key, value)

    db.session.commit()
    return student_schema.jsonify(student), 200


@customers_bp.route("/<int:customer_id>", methods=["DELETE"])
@roles_required("admin")
def delete_customer(customer_id):
    student = db.session.get(Student, customer_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    if student.sessions:
        return jsonify(
            {"error": "Student has 1:1 sessions and cannot be deleted"}
        ), 409
    if student.user:
        return jsonify({"error": "Student has a user account and cannot be deleted"}), 409

    db.session.delete(student)
    db.session.commit()
    return jsonify(
        {"message": f"Student id: {customer_id}, successfully deleted."}
    ), 200
