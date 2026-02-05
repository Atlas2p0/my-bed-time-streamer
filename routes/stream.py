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
    from models import stream_state
    from config import PRESETS
    
    data = request.json
    movie_path = data.get('path')
    preset_key = data.get('preset', 'cpu_fast')
    preset = PRESETS.get(preset_key)
    sub_path = data.get('sub_path')

    metadata = get_video_metadata(movie_path)
    
    # Build command and get working directory
    cmd, work_dir = build_ffmpeg_command(movie_path, preset, metadata, sub_path)
    
    # Cleanup and start in the correct directory
    cleanup_hls_directory()
    
    # Change to HLS directory for FFmpeg
    import os
    original_dir = os.getcwd()
    try:
        os.chdir(work_dir)
        stream_state.current_process = subprocess.Popen(cmd)
    finally:
        os.chdir(original_dir)
    
    return jsonify({"status": "started"})