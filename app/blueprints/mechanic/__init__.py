from flask import Blueprint

mechanics_bp = Blueprint(
    "mechanics",
    __name__,
    url_prefix="/mechanics"
)

from . import routes  # noqa: E402, F401