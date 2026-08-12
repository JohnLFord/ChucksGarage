from flask import g, jsonify, request
from marshmallow import ValidationError

from app.extensions import db
from app.models import Customer, Mechanic, Service_Ticket
from app.utils.util import roles_required, token_required

from . import service_tickets_bp
from .schemas import service_ticket_schema, service_tickets_schema


@service_tickets_bp.route("", methods=["POST"])
@token_required
def create_service_ticket():
    try:
        service_ticket_data = service_ticket_schema.load(request.json)
    except ValidationError as error:
        return jsonify(error.messages), 400

    customer_id = service_ticket_data["customer_id"]
    if g.current_user.role == "customer" and g.current_user.customer_id != customer_id:
        return jsonify({"error": "Insufficient permissions"}), 403
    if g.current_user.role not in {"admin", "mechanic", "customer"}:
        return jsonify({"error": "Insufficient permissions"}), 403
    if not db.session.get(Customer, customer_id):
        return jsonify({"error": "Customer not found"}), 404

    service_ticket = Service_Ticket(**service_ticket_data)
    db.session.add(service_ticket)
    db.session.commit()
    return service_ticket_schema.jsonify(service_ticket), 201


@service_tickets_bp.route("", methods=["GET"])
@token_required
def get_service_tickets():
    query = db.select(Service_Ticket)
    if g.current_user.role == "customer":
        query = query.where(Service_Ticket.customer_id == g.current_user.customer_id)
    elif g.current_user.role == "mechanic":
        query = query.where(
            Service_Ticket.mechanics.any(Mechanic.id == g.current_user.mechanic_id)
        )
    elif g.current_user.role != "admin":
        return jsonify({"error": "Insufficient permissions"}), 403

    service_tickets = db.session.execute(query).scalars().all()
    return service_tickets_schema.jsonify(service_tickets), 200


@service_tickets_bp.route("/<int:service_ticket_id>", methods=["GET"])
@token_required
def get_service_ticket(service_ticket_id):
    service_ticket = db.session.get(Service_Ticket, service_ticket_id)
    if not service_ticket:
        return jsonify({"error": "Service ticket not found"}), 404
    if g.current_user.role == "customer" and (
        g.current_user.customer_id != service_ticket.customer_id
    ):
        return jsonify({"error": "Insufficient permissions"}), 403
    if g.current_user.role == "mechanic" and (
        g.current_user.mechanic_id not in {
            mechanic.id for mechanic in service_ticket.mechanics
        }
    ):
        return jsonify({"error": "Insufficient permissions"}), 403
    if g.current_user.role not in {"admin", "mechanic", "customer"}:
        return jsonify({"error": "Insufficient permissions"}), 403

    return service_ticket_schema.jsonify(service_ticket), 200


@service_tickets_bp.route("/<int:service_ticket_id>", methods=["PUT"])
@roles_required("admin", "mechanic")
def update_service_ticket(service_ticket_id):
    service_ticket = db.session.get(Service_Ticket, service_ticket_id)
    if not service_ticket:
        return jsonify({"error": "Service ticket not found"}), 404

    try:
        service_ticket_data = service_ticket_schema.load(request.json, partial=True)
    except ValidationError as error:
        return jsonify(error.messages), 400

    customer_id = service_ticket_data.get("customer_id")
    if customer_id is not None and not db.session.get(Customer, customer_id):
        return jsonify({"error": "Customer not found"}), 404

    for key, value in service_ticket_data.items():
        setattr(service_ticket, key, value)

    db.session.commit()
    return service_ticket_schema.jsonify(service_ticket), 200


@service_tickets_bp.route("/<int:service_ticket_id>", methods=["DELETE"])
@roles_required("admin")
def delete_service_ticket(service_ticket_id):
    service_ticket = db.session.get(Service_Ticket, service_ticket_id)
    if not service_ticket:
        return jsonify({"error": "Service ticket not found"}), 404

    db.session.delete(service_ticket)
    db.session.commit()
    return jsonify(
        {"message": f"Service ticket id: {service_ticket_id}, successfully deleted."}
    ), 200


@service_tickets_bp.route(
    "/<int:service_ticket_id>/mechanics/<int:mechanic_id>", methods=["POST"]
)
@roles_required("admin")
def assign_mechanic(service_ticket_id, mechanic_id):
    service_ticket = db.session.get(Service_Ticket, service_ticket_id)
    if not service_ticket:
        return jsonify({"error": "Service ticket not found"}), 404

    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 404

    if mechanic in service_ticket.mechanics:
        return jsonify({"error": "Mechanic is already assigned to this ticket"}), 409

    service_ticket.mechanics.append(mechanic)
    db.session.commit()
    return jsonify(
        {
            "message": "Mechanic assigned successfully",
            "service_ticket_id": service_ticket_id,
            "mechanic_id": mechanic_id,
        }
    ), 201


@service_tickets_bp.route(
    "/<int:service_ticket_id>/mechanics/<int:mechanic_id>", methods=["DELETE"]
)
@roles_required("admin")
def remove_mechanic(service_ticket_id, mechanic_id):
    service_ticket = db.session.get(Service_Ticket, service_ticket_id)
    if not service_ticket:
        return jsonify({"error": "Service ticket not found"}), 404

    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic or mechanic not in service_ticket.mechanics:
        return jsonify({"error": "Mechanic is not assigned to this ticket"}), 404

    service_ticket.mechanics.remove(mechanic)
    db.session.commit()
    return jsonify({"message": "Mechanic removed successfully"}), 200