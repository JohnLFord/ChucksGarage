from flask import jsonify, request
from marshmallow import ValidationError

from app.extensions import db
from app.csv_export import csv_response
from app.models import Mechanic
from app.utils.util import roles_required, token_required

from . import mechanics_bp
from .schemas import mechanic_schema, mechanics_schema


@mechanics_bp.route("/", methods=["POST"])
@roles_required("admin")
def create_mechanic():
    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as error:
        return jsonify(error.messages), 400

    mechanic = Mechanic(**mechanic_data)
    db.session.add(mechanic)
    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 201


@mechanics_bp.route("/", methods=["GET"])
@token_required
def get_mechanics():
    query = db.select(Mechanic)
    search = request.args.get("search", "", type=str)
    if search:
        query = query.where(Mechanic.name.ilike(f"%{search}%"))

    mechanics = db.session.execute(query).scalars().all()
    sort_mode = request.args.get("sort", "")
    if sort_mode == "most_tickets":
        mechanics.sort(key=lambda mechanic: len(mechanic.sessions), reverse=True)
    elif sort_mode == "fewest_tickets":
        mechanics.sort(key=lambda mechanic: len(mechanic.sessions))

    limit = request.args.get("limit", type=int)
    offset = request.args.get("offset", 0, type=int)
    if limit is not None:
        mechanics = mechanics[offset : offset + limit]
    elif offset:
        mechanics = mechanics[offset:]

    return mechanics_schema.jsonify(mechanics), 200


@mechanics_bp.route("/export.csv", methods=["GET"])
@token_required
def export_mechanics():
    mechanics = db.session.execute(db.select(Mechanic).order_by(Mechanic.id)).scalars().all()
    rows = [
        {
            "id": mechanic.id,
            "name": mechanic.name,
            "specialty": mechanic.specialty,
            "experience": mechanic.experience,
            "certification": mechanic.certification,
        }
        for mechanic in mechanics
    ]
    return csv_response("teachers.csv", rows, ["id", "name", "specialty", "experience", "certification"])


@mechanics_bp.route("/<int:mechanic_id>", methods=["GET"])
@token_required
def get_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 404

    return mechanic_schema.jsonify(mechanic), 200


@mechanics_bp.route("/<int:mechanic_id>", methods=["PUT"])
@roles_required("admin")
def update_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 404

    try:
        mechanic_data = mechanic_schema.load(request.json, partial=True)
    except ValidationError as error:
        return jsonify(error.messages), 400

    for key, value in mechanic_data.items():
        setattr(mechanic, key, value)

    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 200


@mechanics_bp.route("/<int:mechanic_id>", methods=["DELETE"])
@roles_required("admin")
def delete_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 404
    if mechanic.sessions:
        return jsonify({"error": "Teacher has 1:1 sessions and cannot be deleted"}), 409
    if mechanic.user:
        return jsonify({"error": "Mechanic has a user account and cannot be deleted"}), 409

    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({"message": f"Mechanic id: {mechanic_id}, successfully deleted."}), 200