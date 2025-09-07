"""Application factory for Flask app."""
import os
from flask import Flask
from dotenv import load_dotenv

from .config import get_config
from .extensions import db, migrate, login_manager

def create_app():
    """Application factory pattern."""
    load_dotenv()
    env = os.getenv("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(get_config(env))

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .blueprints.core import bp as core_bp

    app.register_blueprint(core_bp)

    return app
