"""Core routes for the application."""

from flask import jsonify, render_template

from ...models import Study

from . import bp


@bp.get("/healthz")
def healthz():
    """Health check endpoint."""
    return jsonify(status="ok"), 200


@bp.get("/")
def index():
    """Application root."""
    return render_template("index.html")


@bp.get("/studies/")
def studies_list():
    """Display all studies."""
    studies = Study.query.all()
    return render_template("studies/index.html", studies=studies)
