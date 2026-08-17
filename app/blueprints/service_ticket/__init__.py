from flask import Blueprint

service_tickets_bp = Blueprint(
    "service_tickets",
    __name__,
    url_prefix="/service-tickets"  
)

from . import routes  # noqa: E402, F401