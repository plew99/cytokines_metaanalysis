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
