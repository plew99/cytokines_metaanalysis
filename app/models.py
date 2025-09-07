"""Database models and import utilities for the application."""

import csv
from typing import List

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Study(db.Model):
    """Research study metadata."""

    __tablename__ = "studies"

    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.String, unique=True, nullable=False)
    first_author = db.Column(db.String, nullable=False)
    publication_year = db.Column(db.Integer)
    country = db.Column(db.String)
    study_design = db.Column(db.String)
    notes = db.Column(db.Text)


class Cohort(db.Model):
    """Clinical cohort (study arm/group) with clinical parameters."""

    __tablename__ = "cohorts"
    __table_args__ = (
        db.UniqueConstraint("study_id", "cohort_label", name="uq_cohort_study_label"),
    )

    cohort_id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.String, db.ForeignKey("studies.study_id"), nullable=False)
    cohort_label = db.Column(db.String, nullable=False)
    cohort_notes = db.Column(db.Text)
    sample_size = db.Column(db.Integer)
    age_central_value = db.Column(db.Float)
    age_dispersion_value = db.Column(db.Float)
    age_summary_type = db.Column(
        db.Enum("mean_sd", "median_iqr", name="age_summary_type")
    )
    percent_male = db.Column(db.Float)
    ethnicity = db.Column(db.String)
    inflammation_excluded_by_emb = db.Column(db.Boolean)
    cad_excluded = db.Column(db.Boolean)
    other_causes_excluded = db.Column(db.Text)
    disease_confirmation_desc = db.Column(db.Text)
    nyha_summary = db.Column(db.String)
    lvef_percent_central = db.Column(db.Float)
    lvef_percent_dispersion = db.Column(db.Float)
    lvef_summary_type = db.Column(
        db.Enum("mean_sd", "median_iqr", name="lvef_summary_type")
    )
    lvedd_central = db.Column(db.Float)
    lvedd_dispersion = db.Column(db.Float)
    lvedd_summary_type = db.Column(
        db.Enum("mean_sd", "median_iqr", name="lvedd_summary_type")
    )
    emb_performed = db.Column(db.Boolean)
    emb_criteria = db.Column(db.Text)
    emb_lymphocyte_density_per_mm2 = db.Column(db.Float)
    emb_other_findings = db.Column(db.Text)
    viral_presence = db.Column(db.Text)
    cmr_performed = db.Column(db.Boolean)

    study = db.relationship(
        "Study", backref=db.backref("cohorts", cascade="all, delete-orphan")
    )


def _parse_bool(value: str | None) -> bool | None:
    """Convert common textual truthy/falsey values to bool.

    Empty strings return ``None`` so that SQLAlchemy stores ``NULL``.
    """

    if value is None or value == "":
        return None
    return value.strip().lower() in {"1", "true", "t", "yes", "y"}


_SUMMARY_TYPES = {"mean_sd", "median_iqr"}


def _parse_summary_type(value: str | None) -> str | None:
    """Validate summary type enums used by :class:`Cohort`.

    Empty strings or unrecognised values are converted to ``None`` so that the
    database stores ``NULL`` and SQLAlchemy's Enum type does not raise errors
    when reading the row back.
    """

    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    return value if value in _SUMMARY_TYPES else None


def import_studies_from_csv(path: str) -> List[Study]:
    """Import studies from a CSV file.

    The CSV must include all :class:`Study` columns except the auto-increment
    ``id``. Each row is converted into a :class:`Study` instance and written to
    the database. The function returns the list of created objects.
    """

    created: List[Study] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row.pop("id", None)
            if row.get("publication_year"):
                row["publication_year"] = int(row["publication_year"])
            study = Study(**row)
            db.session.add(study)
            created.append(study)
    db.session.commit()
    return created


def import_cohorts_from_csv(path: str) -> List[Cohort]:
    """Import cohorts from a CSV file.

    The CSV should contain all :class:`Cohort` columns except ``cohort_id``.
    Numeric and boolean columns are converted from strings when possible. The
    function returns the list of created objects.
    """

    created: List[Cohort] = []
    int_fields = {"sample_size"}
    float_fields = {
        "age_central_value",
        "age_dispersion_value",
        "percent_male",
        "lvef_percent_central",
        "lvef_percent_dispersion",
        "lvedd_central",
        "lvedd_dispersion",
        "emb_lymphocyte_density_per_mm2",
    }
    bool_fields = {
        "inflammation_excluded_by_emb",
        "cad_excluded",
        "emb_performed",
        "cmr_performed",
    }
    summary_fields = {
        "age_summary_type",
        "lvef_summary_type",
        "lvedd_summary_type",
    }

    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row.pop("cohort_id", None)
            row.pop("id", None)

            for field in int_fields:
                value = row.get(field)
                if value is None or value.strip() == "":
                    row[field] = None
                else:
                    row[field] = int(value)
            for field in float_fields:
                value = row.get(field)
                if value is None or value.strip() == "":
                    row[field] = None
                else:
                    row[field] = float(value)
            for field in bool_fields:
                row[field] = _parse_bool(row.get(field))
            for field in summary_fields:
                row[field] = _parse_summary_type(row.get(field))

            cohort = Cohort(**row)
            db.session.add(cohort)
            created.append(cohort)

    db.session.commit()
    return created
