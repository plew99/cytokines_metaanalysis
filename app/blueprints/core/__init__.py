"""Core blueprint."""
from flask import Blueprint

# templates globalne -> nie trzeba template_folder
bp = Blueprint("core", __name__)

from . import routes  # noqa: E402,F401
