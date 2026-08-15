from flask import Flask, jsonify
from werkzeug.exceptions import BadRequest, MethodNotAllowed

from .blueprints.customer import customers_bp
from .blueprints.inventory import inventory_bp
from .blueprints.mechanic import mechanics_bp
from .blueprints.service_ticket import service_tickets_bp
from .blueprints.user import user_bp
from .extensions import cache, db, limiter, ma, migrate


def create_app(config_object="config.DevelopmentConfig"):
    app = Flask(__name__)
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
        return jsonify({"error": "Invalid request", "details": error.description}), 400

    @app.errorhandler(MethodNotAllowed)
    def handle_method_not_allowed(error):
        return jsonify(
            {
                "error": "Method not allowed",
                "allowed_methods": sorted(error.valid_methods or []),
            }
        ), 405

    app.register_blueprint(user_bp, url_prefix="/users")
    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(mechanics_bp, url_prefix="/mechanics")
    app.register_blueprint(service_tickets_bp, url_prefix="/service-tickets")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")

    return app
