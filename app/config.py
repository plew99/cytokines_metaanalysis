"""Application configuration."""
import os


class BaseConfig:
    """Base configuration with defaults."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True


class ProductionConfig(BaseConfig):
    DEBUG = False


def get_config(env: str):
    """Return configuration class based on environment string."""
    mapping = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
    }
    return mapping.get(env, DevelopmentConfig)
