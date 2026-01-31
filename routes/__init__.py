"""Blueprint registration for Flask routes."""

from flask import Blueprint

# Create blueprints
library_bp = Blueprint('library', __name__)
stream_bp = Blueprint('stream', __name__)
ui_bp = Blueprint('ui', __name__)

# Import route handlers to register them
from . import library
from . import stream
from . import ui


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(library_bp)
    app.register_blueprint(stream_bp)
    app.register_blueprint(ui_bp)