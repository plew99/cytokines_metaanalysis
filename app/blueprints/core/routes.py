"""Core routes for the application."""

from flask import jsonify, render_template

from app.models import Study

from . import bp


@bp.get("/healthz")
def healthz():
    """Health check endpoint."""
    return jsonify(status="ok"), 200


@bp.get("/")
def index():
    """Application root."""
    return render_template("index.html")


@bp.get("/studies")
def studies():
    """List available studies."""
    all_studies = Study.query.order_by(Study.publication_year.desc()).all()
    return render_template("studies.html", studies=all_studies)
