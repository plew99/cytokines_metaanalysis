"""Extensions used by the app."""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id: str):
    """Return user by ID for Flask-Login."""
    from .models import User

    return db.session.get(User, int(user_id))
