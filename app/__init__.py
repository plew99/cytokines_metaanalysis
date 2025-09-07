"""Application factory for Flask app."""
import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv

from .config import get_config
from .extensions import db, migrate, login_manager

def create_app():
    """Application factory pattern."""
    load_dotenv()
    env = os.getenv("FLASK_ENV", "development")

    # Important: instance_relative_config + ensure instance path exists
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    app.config.from_object(get_config(env))

    # Stabilize SQLite path
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "").strip()
    if not uri:
        db_path = Path(app.instance_path) / "meta.sqlite3"
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    elif uri.startswith("sqlite:///") and not uri.startswith("sqlite:////") and ":memory:" not in uri:
        rel = uri.replace("sqlite:///", "", 1)
        db_path = Path(app.instance_path) / rel
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Blueprints
    from .blueprints.core import bp as core_bp
    app.register_blueprint(core_bp)

    # CLI commands
    from . import cli as cli_mod
    cli_mod.init_app(app)

    # Simple healthcheck
    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    return app

