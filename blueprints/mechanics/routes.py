from flask import jsonify, request
from marshmallow import ValidationError

from app.extensions import db
from app.models import Mechanic
from app.utils.util import roles_required, token_required

from . import mechanics_bp
from .schemas import mechanic_schema, mechanics_schema


@mechanics_bp.route("", methods=["POST"])
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


@mechanics_bp.route("", methods=["GET"])
@token_required
def get_mechanics():
    mechanics = db.session.execute(db.select(Mechanic)).scalars().all()
    return mechanics_schema.jsonify(mechanics), 200


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
    if mechanic.user:
        return jsonify({"error": "Mechanic has a user account and cannot be deleted"}), 409

    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({"message": f"Mechanic id: {mechanic_id}, successfully deleted."}), 200