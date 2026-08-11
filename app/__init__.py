from flask import Flask, jsonify
from werkzeug.exceptions import BadRequest, MethodNotAllowed

from .blueprints.customers import customers_bp
from .blueprints.mechanics import mechanics_bp
from .blueprints.service_tickets import service_tickets_bp
from .extensions import db, ma


def create_app(config_object):
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.url_map.strict_slashes = False

    ma.init_app(app)
    db.init_app(app)

    @app.errorhandler(BadRequest)
    def handle_bad_request(error):
        return jsonify({"error": "Invalid request", "details": error.description}), 400

    @app.errorhandler(MethodNotAllowed)
    def handle_method_not_allowed(error):
        return jsonify(
            {
                "error": "Method not allowed",
                "allowed_methods": sorted(error.valid_methods or []),
            }
        ), 405

    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(mechanics_bp, url_prefix="/mechanics")
    app.register_blueprint(service_tickets_bp, url_prefix="/service-tickets")
    app.register_blueprint(
        service_tickets_bp,
        url_prefix="/service_tickets",
        name="service_tickets_underscore",
    )

    return app
