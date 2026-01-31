"""Routes for library listing and file probing."""

from flask import jsonify, request

from routes import library_bp
from utils.filesystem import scan_library
from utils.ffmpeg import get_video_metadata


@library_bp.route('/api/library', methods=['GET'])
def list_library():
    library_data = scan_library()
    return jsonify(library_data)


@library_bp.route('/api/probe', methods=['POST'])
def probe_file():
    path = request.json.get('path')
    metadata = get_video_metadata(path)
    return jsonify(metadata)