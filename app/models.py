"""Database models for the application."""

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
