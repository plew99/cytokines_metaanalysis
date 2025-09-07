"""Core routes for the application."""

from flask import (
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
import os
import tempfile

from app.models import (
    Study,
    import_cohorts_from_csv,
    import_studies_from_csv,
)

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


@bp.route("/import", methods=["GET", "POST"])
def import_data():
    """Import studies or cohorts from a CSV file."""
    if request.method == "POST":
        data_type = request.form.get("data_type")
        uploaded = request.files.get("file")
        if not uploaded or data_type not in {"studies", "cohorts"}:
            flash("Invalid upload", "danger")
            return redirect(url_for("core.import_data"))

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            uploaded.save(tmp.name)
            tmp_path = tmp.name
        try:
            if data_type == "studies":
                created = import_studies_from_csv(tmp_path)
                flash(f"Imported {len(created)} studies", "success")
            else:
                created = import_cohorts_from_csv(tmp_path)
                flash(f"Imported {len(created)} cohorts", "success")
        finally:
            os.unlink(tmp_path)

        return redirect(url_for("core.import_data"))

    return render_template("import.html")
