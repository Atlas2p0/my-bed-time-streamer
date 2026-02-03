import os
from flask import Flask, send_from_directory, render_template
import socket

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
    template_folder=os.path.join(PROJECT_ROOT, 'web', 'templates'),
    static_folder=os.path.join(PROJECT_ROOT, 'web', 'static'),
    static_url_path='/web/static'
)

from routes import register_blueprints
register_blueprints(app)

from config import HLS_DIR
os.makedirs(HLS_DIR, exist_ok=True)


@app.route('/health')
def health():
    return {'status': 'ok'}


@app.route('/hls/<path:filename>')
def serve_hls(filename):
    return send_from_directory(HLS_DIR, filename)


@app.route('/player')
def player():
    return render_template('player.html')


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

if __name__ == "__main__":
    from waitress import serve
    
    local_ip = get_local_ip()
    
    print(f"Starting Bedtime Streamer...")
    print(f"Web UI:    http://{local_ip}:5000")
    print(f"Press Ctrl+C to stop")
    
    serve(app, host='0.0.0.0', port=5000, threads=8)