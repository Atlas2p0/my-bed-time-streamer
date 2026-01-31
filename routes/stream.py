"""Routes for starting and stopping the HLS stream."""

import subprocess

from flask import jsonify, request

from routes import stream_bp
from models import stream_state
from config import PRESETS
from utils.ffmpeg import get_video_metadata, build_ffmpeg_command, cleanup_hls_directory


@stream_bp.route('/api/stop', methods=['POST'])
def stop_stream():
    if stream_state.current_process:
        stream_state.current_process.terminate()
        stream_state.current_process = None
    return jsonify({"status": "stopped"})


@stream_bp.route('/api/start', methods=['POST'])
def start_stream():
    data = request.json
    movie_path = data.get('path')
    preset_key = data.get('preset', 'cpu_fast')
    preset = PRESETS.get(preset_key)
    sub_path = data.get('sub_path')

    # Re-probe to get the latest metadata
    metadata = get_video_metadata(movie_path)

    # Build FFmpeg command
    cmd = build_ffmpeg_command(movie_path, preset, metadata, sub_path)

    # Cleanup and Start stream
    cleanup_hls_directory()
    
    stream_state.current_process = subprocess.Popen(cmd)
    return jsonify({"status": "started"})