"""Routes for the main UI and preset listing."""

from flask import render_template, jsonify

from routes import ui_bp
from config import PRESETS


@ui_bp.route('/')
def index():
    return render_template('index.html')


@ui_bp.route('/api/presets', methods=['GET'])
def get_presets():
    return jsonify(list(PRESETS.keys()))