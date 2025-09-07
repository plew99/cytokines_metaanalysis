from flask_sqlalchemy import SQLAlchemy

# Global SQLAlchemy database instance
# Initialized in application factory
# Use: from app import db


db = SQLAlchemy()
