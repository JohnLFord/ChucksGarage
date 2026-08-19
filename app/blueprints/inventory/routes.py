from flask import jsonify, request
from marshmallow import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.csv_export import csv_response
from app.models import Lesson
from app.utils.util import roles_required, token_required

from . import inventory_bp
from .schemas import lesson_schema, lessons_schema


@inventory_bp.route("/", methods=["POST"])
@roles_required("admin")
def create_part():
    try:
        lesson_data = lesson_schema.load(request.json)
    except ValidationError as error:
        return jsonify(error.messages), 400

    query = select(Lesson).where(Lesson.sku == lesson_data["sku"])
    existing_lesson = db.session.execute(query).scalar_one_or_none()
    if existing_lesson:
        return jsonify({"error": "Course code already exists"}), 400

    new_lesson = Lesson(**lesson_data)
    db.session.add(new_lesson)
    db.session.commit()
    return lesson_schema.jsonify(new_lesson), 201


@inventory_bp.route("/", methods=["GET"])
@token_required
def get_parts():
    query = select(Lesson)
    search = request.args.get("search", "", type=str)
    if search:
        query = query.where(Lesson.name.ilike(f"%{search}%"))

    sort = request.args.get("sort", "")
    if sort == "name":
        query = query.order_by(Lesson.name)
    elif sort == "stock":
        query = query.order_by(Lesson.stock_quantity)

    offset = request.args.get("offset", 0, type=int)
    if offset:
        query = query.offset(offset)

    limit = request.args.get("limit", type=int)
    if limit is not None:
        query = query.limit(limit)

    lessons = db.session.execute(query).scalars().all()
    return lessons_schema.jsonify(lessons), 200


@inventory_bp.route("/export.csv", methods=["GET"])
@token_required
def export_parts():
    lessons = db.session.execute(select(Lesson).order_by(Lesson.id)).scalars().all()
    rows = [
        {"id": part.id, "name": part.name, "sku": part.sku, "stock_quantity": part.stock_quantity}
        for part in lessons
    ]
    return csv_response("lessons.csv", rows, ["id", "name", "sku", "stock_quantity"])


@inventory_bp.route("/<int:part_id>", methods=["GET"])
@token_required
def get_part(part_id):
    part = db.session.get(Lesson, part_id)
    if not part:
        return jsonify({"error": "Lesson not found"}), 404

    return lesson_schema.jsonify(part), 200


@inventory_bp.route("/<int:part_id>", methods=["PUT"])
@roles_required("admin", "teacher")
@roles_required("admin", "teacher")
def update_part(part_id):
    part = db.session.get(Lesson, part_id)
    if not part:
        return jsonify({"error": "Lesson not found"}), 404

    try:
        part_data = lesson_schema.load(request.json, partial=True)
    except ValidationError as error:
        return jsonify(error.messages), 400

    for key, value in part_data.items():
        setattr(part, key, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Course code already exists"}), 400

    return lesson_schema.jsonify(part), 200


@inventory_bp.route("/<int:part_id>", methods=["DELETE"])
@roles_required("admin")
def delete_part(part_id):
    part = db.session.get(Lesson, part_id)
    if not part:
        return jsonify({"error": "Lesson not found"}), 404

    if part.sessions:
        return jsonify(
            {"error": "Lesson has sessions and cannot be deleted"}
        ), 409

    db.session.delete(part)
    db.session.commit()
    return jsonify({"message": f"Lesson id: {part_id}, successfully deleted."}), 200
