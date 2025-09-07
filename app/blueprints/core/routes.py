"""Core routes for the application."""

from flask import jsonify, render_template

from . import bp


@bp.get("/healthz")
def healthz():
    """Health check endpoint."""
    return jsonify(status="ok"), 200


@bp.get("/")
def index():
    """Application root."""
    return render_template("index.html")
