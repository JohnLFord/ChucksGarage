from flask import Flask, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint
from werkzeug.exceptions import BadRequest, MethodNotAllowed
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
        data = request.get_json()

        member = Member(
            name=data["name"],
            email=data["email"],
        )

        db.session.add(member)
        db.session.commit()

        return jsonify(
            {
                "id": member.id,
                "name": member.name,
                "email": member.email,
            }
        ), 201

    app.register_blueprint(customers_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(mechanics_bp)
    app.register_blueprint(service_tickets_bp)
    app.register_blueprint(user_bp, url_prefix="/users")

    return app