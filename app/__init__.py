from dotenv.cli import get
from flask_swagger_ui import get_swaggerui_blueprint
from flask import Flask, jsonify, request
from datetime import datetime, date
from werkzeug.exceptions import BadRequest, MethodNotAllowed
from app.utils.util import encode_token
from config import TestingConfig

from .models import Member
from .blueprints.customer import customers_bp
from .blueprints.inventory import inventory_bp
from .blueprints.mechanic import mechanics_bp
from .blueprints.service_ticket import service_tickets_bp
from .blueprints.user import user_bp
from .extensions import cache, db, limiter, ma, migrate

SWAGGER_URL = "/api/docs"
API_URL = "/static/swagger.yaml"

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={"app_name": "Chucks Garage API"},
)


def create_app(config_object="config.DevelopmentConfig"):
    app = Flask(__name__)

    if config_object == "TestingConfig":
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(config_object)

    app.url_map.strict_slashes = False

    ma.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    cache.init_app(
        app,
        config={
            "CACHE_TYPE": "SimpleCache",
            "CACHE_DEFAULT_TIMEOUT": 30,
        },
    )

    @app.errorhandler(BadRequest)
    def handle_bad_request(error):
        return jsonify(
            {
                "error": "Invalid request",
                "details": error.description,
            }
        ), 400

    @app.errorhandler(MethodNotAllowed)
    def handle_method_not_allowed(error):
        return jsonify(
            {
                "error": "Method not allowed",
                "details": error.description,
            }
        ), 405

    @app.route("/members/", methods=["POST"])
    def create_member():
        payload = request.get_json(silent=True)

        if not isinstance(payload, dict):
            return jsonify({"error": "JSON payload required"}), 400

        # Validate required fields
        errors = {}

        if "email" not in payload:
            errors["email"] = ["Missing data for required field."]
        if "name" not in payload:
            errors["name"] = ["Missing data for required field."]
        if "password" not in payload:
            errors["password"] = ["Missing data for required field."]
        if "DOB" not in payload:
            errors["DOB"] = ["Missing data for required field."]

        if errors:
            return jsonify(errors), 400

        member = Member(
            name=payload["name"],
            email=payload["email"],
            DOB=datetime.strptime(payload["DOB"], "%Y-%m-%d").date(),
            password=payload["password"],
            role="customer",
        )

        db.session.add(member)
        db.session.commit()
        token = encode_token(member.id, member.role)
        return jsonify(
            {
                "id": member.id,
                "name": member.name,
                "email": member.email,
                "DOB": member.DOB.isoformat(),
                "auth_token": token,
            }
        ), 201

    @app.route("/members/", methods=["PUT"])
    def update_member():
        payload = request.get_json(silent=True)

        if not isinstance(payload, dict):
            return jsonify({"error": "JSON payload required"}), 400

        member = db.session.get(Member, 1)  # Assuming only one member for simplicity

        if member is None:
            return jsonify({"error": "Member not found"}), 404

        # Update allowed fields
        if payload.get("name"):
            member.name = payload["name"]
        if payload.get("email"):
            member.email = payload["email"]
        if payload.get("password"):
            member.password = payload["password"]
        if payload.get("DOB"):
            member.DOB = datetime.strptime(payload["DOB"], "%Y-%m-%d").date()

        db.session.add(member)
        db.session.commit()

        token = encode_token(member.id, member.role)

        return jsonify(
            {
                "id": member.id,
                "name": member.name,
                "email": member.email,
                "DOB": member.DOB.isoformat(),
                "auth_token": token,
            }
        ), 200

    app.register_blueprint(customers_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(mechanics_bp)
    app.register_blueprint(service_tickets_bp)
    app.register_blueprint(user_bp, url_prefix="/users")

    return app
