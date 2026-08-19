from flask import Blueprint

inventory_bp = Blueprint(
    "inventory", 
    __name__,
    url_prefix="/lessons"
)

from . import routes  # noqa: E402, F401
