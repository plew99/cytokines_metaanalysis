"""Core routes for the application."""

from flask import flash, jsonify, redirect, render_template, url_for

from ... import db
from ...models import RawRecord, Study
from ...forms import StudyForm

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


@bp.route("/studies/new", methods=["GET", "POST"])
def studies_create():
    """Create a new study."""
    form = StudyForm()
    if form.validate_on_submit():
        study = Study(
            id=form.id.data,
            authors_text=form.author.data,
            year=form.year.data,
            country=form.country.data,
            title=form.title.data or "Untitled",
        )
        db.session.add(study)
        db.session.commit()
        flash("Dodano badanie", "success")
        return redirect(url_for("core.studies_list"))
    return render_template("studies/new.html", form=form)


@bp.get("/raw-records/")
def raw_records_list():
    """Display raw imported records with invalid fields highlighted."""

    records = RawRecord.query.all()
    return render_template("raw_records/index.html", records=records)
