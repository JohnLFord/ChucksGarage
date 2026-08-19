from flask import Blueprint

mechanics_bp = Blueprint(
    "mechanics",
    __name__,
    url_prefix="/teachers"
)

from . import routes  # noqa: E402, F401