from flask import g, jsonify, request
from marshmallow import ValidationError
from sqlalchemy import select

from app.extensions import db, limiter
from app.csv_export import csv_response
from app.models import Customer
from app.utils.util import roles_required, token_required

from . import customers_bp
from .schemas import customer_schema, customers_schema


@customers_bp.route("/", methods=["POST"])
@limiter.limit("5 per day")
@roles_required("admin")
def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as error:
        return jsonify(error.messages), 400

    query = select(Customer).where(Customer.email == customer_data["email"])
    existing_customer = db.session.execute(query).scalar_one_or_none()
    if existing_customer:
        return jsonify({"error": "Email already exists"}), 400

    new_customer = Customer(**customer_data)
    db.session.add(new_customer)
    db.session.commit()
    return customer_schema.jsonify(new_customer), 201


@customers_bp.route("/", methods=["GET"])
@roles_required("admin", "mechanic")
def get_customers():
    query = select(Customer)
    search = request.args.get("search", "", type=str)
    if search:
        query = query.where(Customer.name.ilike(f"%{search}%"))

    if request.args.get("sort", "") == "name":
        query = query.order_by(Customer.name)

    offset = request.args.get("offset", 0, type=int)
    if offset:
        query = query.offset(offset)

    limit = request.args.get("limit", type=int)
    if limit is not None:
        query = query.limit(limit)

    customers = db.session.execute(query).scalars().all()
    return customers_schema.jsonify(customers), 200


@customers_bp.route("/export.csv", methods=["GET"])
@roles_required("admin", "mechanic")
def export_customers():
    customers = db.session.execute(select(Customer).order_by(Customer.id)).scalars().all()
    rows = [
        {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "date_of_birth": customer.date_of_birth.isoformat(),
        }
        for customer in customers
    ]
    return csv_response("students.csv", rows, ["id", "name", "email", "date_of_birth"])


@customers_bp.route("/<int:customer_id>", methods=["GET"])
@token_required
def get_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    if g.current_user.role == "customer" and g.current_user.customer_id != customer_id:
        return jsonify({"error": "Insufficient permissions"}), 403
    if g.current_user.role not in {"admin", "mechanic", "customer"}:
        return jsonify({"error": "Insufficient permissions"}), 403

    return customer_schema.jsonify(customer), 200


@customers_bp.route("/<int:customer_id>", methods=["PUT"])
@token_required
def update_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    if g.current_user.role == "customer" and g.current_user.customer_id != customer_id:
        return jsonify({"error": "Insufficient permissions"}), 403
    if g.current_user.role not in {"admin", "customer"}:
        return jsonify({"error": "Insufficient permissions"}), 403

    try:
        customer_data = customer_schema.load(request.json, partial=True)
    except ValidationError as error:
        return jsonify(error.messages), 400

    for key, value in customer_data.items():
        setattr(customer, key, value)

    db.session.commit()
    return customer_schema.jsonify(customer), 200


@customers_bp.route("/<int:customer_id>", methods=["DELETE"])
@roles_required("admin")
def delete_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    if customer.sessions:
        return jsonify(
            {"error": "Student has 1:1 sessions and cannot be deleted"}
        ), 409
    if customer.user:
        return jsonify({"error": "Customer has a user account and cannot be deleted"}), 409

    db.session.delete(customer)
    db.session.commit()
    return jsonify(
        {"message": f"Customer id: {customer_id}, successfully deleted."}
    ), 200
