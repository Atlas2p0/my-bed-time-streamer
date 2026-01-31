import os
from flask import Flask, send_from_directory
import sys

# Get project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
    template_folder=os.path.join(PROJECT_ROOT, 'web', 'templates'),
    static_folder=os.path.join(PROJECT_ROOT, 'static'),
    static_url_path='/static'
)

# Import after app creation
from routes import register_blueprints
register_blueprints(app)

from config import HLS_DIR

# Ensure HLS directory exists
os.makedirs(HLS_DIR, exist_ok=True)


@app.route('/health')
def health():
    return {'status': 'ok'}


# Serve HLS files directly from Flask
@app.route('/hls/<path:filename>')
def serve_hls(filename):
    return send_from_directory(HLS_DIR, filename)


@app.route('/debug')
def debug_paths():
    from flask import current_app
    return {
        'project_root': PROJECT_ROOT,
        'template_folder': current_app.template_folder,
        'template_folder_exists': os.path.exists(current_app.template_folder),
        'hls_dir': HLS_DIR,
        'hls_dir_exists': os.path.exists(HLS_DIR),
    }


if __name__ == "__main__":
    from waitress import serve
    import socket
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"template_folder: {os.path.join(PROJECT_ROOT, 'web', 'templates')}")
    print(f"exists: {os.path.exists(os.path.join(PROJECT_ROOT, 'web', 'templates'))}")
    print(f"contents: {os.listdir(os.path.join(PROJECT_ROOT, 'web', 'templates')) if os.path.exists(os.path.join(PROJECT_ROOT, 'web', 'templates')) else 'NOT FOUND'}")
    
    # Get local IP for user-friendly output
    hostname = socket.gethostname()
    local_ip = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
    
    print(f"Starting Bedtime Streamer...")
    print(f"Web UI:    http://{local_ip}:5000")
    print(f"HLS Stream: http://{local_ip}:5000/hls/index.m3u8 (when active)")
    print(f"Press Ctrl+C to stop")
    
    serve(app, host='0.0.0.0', port=5000, threads=8)