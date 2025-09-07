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

from sqlalchemy.orm import joinedload

from app.models import (
    Study,
    Cohort,
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
    """List available studies with optional sorting."""
    sort_key = request.args.get("sort", "publication_year")
    direction = request.args.get("direction", "desc")
    sort_options = {
        "id": Study.id,
        "study_id": Study.study_id,
        "first_author": Study.first_author,
        "publication_year": Study.publication_year,
        "country": Study.country,
        "study_design": Study.study_design,
        "notes": Study.notes,
    }
    sort_col = sort_options.get(sort_key, Study.publication_year)
    order_by = sort_col.asc() if direction == "asc" else sort_col.desc()
    all_studies = (
        Study.query.options(joinedload(Study.cohorts))
        .order_by(order_by)
        .all()
    )
    return render_template(
        "studies.html", studies=all_studies, sort=sort_key, direction=direction
    )


@bp.get("/cohorts/<int:cohort_id>")
def cohort_detail(cohort_id: int):
    """Display details for a cohort."""
    cohort = Cohort.query.get_or_404(cohort_id)
    return render_template("cohort_detail.html", cohort=cohort)


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
