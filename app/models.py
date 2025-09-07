"""Database models for the application."""

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Study(db.Model):
    """Research study metadata."""

    __tablename__ = "studies"

    study_id = db.Column(db.String, primary_key=True)
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
