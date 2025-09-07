"""Form definitions for the application."""

from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField
from wtforms.validators import DataRequired


class StudyForm(FlaskForm):
    """Form for creating a new study."""

    id = IntegerField("ID", validators=[DataRequired()])
    author = StringField("Autor", validators=[DataRequired()])
    year = IntegerField("Rok", validators=[DataRequired()])
    country = StringField("Kraj", validators=[DataRequired()])
    title = StringField("Tytuł")
