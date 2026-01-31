from flask import Flask

from config import HLS_DIR
from routes import register_blueprints

app = Flask(__name__)

# Ensure HLS directory exists
import os
os.makedirs(HLS_DIR, exist_ok=True)

# Register all blueprints
register_blueprints(app)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)