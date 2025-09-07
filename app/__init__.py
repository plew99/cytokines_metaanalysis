"""Application factory for Flask app."""
import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv

from .config import get_config

def create_app():
    """Application factory pattern."""
    load_dotenv()
    env = os.getenv("FLASK_ENV", "development")

    # Important: instance_relative_config + ensure instance path exists
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    app.config.from_object(get_config(env))

    # Blueprints
    from .blueprints.core import bp as core_bp
    app.register_blueprint(core_bp)

    # Simple healthcheck
    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    return app

