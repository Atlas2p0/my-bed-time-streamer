from flask import Flask, render_template, jsonify, request
import os
import subprocess
import json

app = Flask(__name__)

# CONFIGURATION
LIBRARY_PATH = "/media/atlas/Gaming/Media Library/"
HLS_DIR = "/var/www/hls"
VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov')
PRESETS = {
    "cpu_fast": {
        "v_codec": "libx264",
        "v_profile": ["-preset", "veryfast", "-crf", "23"],
        "a_codec": "aac",
    },
    "gpu_nvenc": {
        "v_codec": "h264_nvenc",
        "v_profile": ["-preset", "p4", "-b:v", "4M"],
        "a_codec": "aac",
    },
    "gpu_nvenc_high_quality": {
        "v_codec": "h264_nvenc",
        "v_profile": ["-preset", "p7", "-b:v", "8M"],
        "a_codec": "aac",
    }
}
current_process = None

def get_video_metadata(file_path):
    """Uses ffprobe to check for video info and subtitle tracks."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_streams',
        '-of', 'json',
        file_path
    ]
    try:
        result = subprocess.check_output(cmd).decode('utf-8')
        data = json.loads(result)
        has_subtitles = any(s['codec_type'] == 'subtitle' for s in data['streams'])
        video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
        return {
            "has_subtitles": has_subtitles,
            "codec": video_stream.get('codec_name') if video_stream else "unknown",
            "resolution":
            f"{video_stream.get('width')}x{video_stream.get('height')}" if video_stream else "unknown"
        }
    except Exception as e:
        print(f"Error probing {file_path}: {e}")
        return None
    
@app.route('/api/library', methods=['GET'])
def list_library():
    movie_list = []
    # Walk through the "Media Library" dir
    for root, dirs, files in os.walk(LIBRARY_PATH):
        for file in files:
            if file.lower().endswith(VIDEO_EXTENSIONS):
                full_path = os.path.abspath(os.path.join(root, file))

                # Get folder name (The "Movie Name")
                display_name = os.path.basename(root)
                
                # Probe the file for details
                metadata = get_video_metadata(full_path)

                movie_list.append({
                    "title": display_name,
                    "filename": file,
                    "full_path": full_path,
                    "metadata": metadata
                })
    return jsonify(movie_list)

@app.route('/api/stop', methods=['POST'])
def stop_stream():
    global current_process
    if current_process:
        current_process.terminate() # Or .send_signal(signal.SIGINT)
        current_process =  None
    return jsonify({"status": "stopped"})

@app.route('/api/start', methods=['POST'])
def start_stream():
    global current_process
    data = request.json

    movie_path = data.get('path')
    preset_key = data.get('preset', 'cpu_fast')
    sub_path = data.get('sub_path') # This will be the path to an .srt file if provided
    preset = PRESETS.get(preset_key)

    # 1. Kill old stream if running
    if current_process:
        current_process.terminate()
    # 2. Build the command
    # Base command
    cmd = [
        "ffmpeg", "-y", "-i", movie_path
    ]

    # Handle Subtitles (Hardcoding/Burn-in)
    # If a sub_path is provided, we use the subtitles filter
    video_filters = "format=yuv420p"
    if sub_path:
        # Formatting paths for subtitles filter can be tricky
        video_filters = f"subtitles='{sub_path}',format=yuv420p"
    
    cmd += ["-vf", video_filters]

    # Apply Preset Video Settings
    cmd += ["-c:v", preset['v_codec']]
    cmd += preset['v_profile']

    # Audio Settings
    cmd += ["-c:a", preset['a_codec'], "-b:a", "192k", "-ac", "2"]

    # HLS Output Settings
    cmd += [
        "-f", "hls",
        "-hls_time", "6",
        "-hls_list_size", "0", # VOD mode
        "-hls_segment_filename", "/var/www/hls/segment_%03d.ts",
        "/var/www/hls/index.m3u8"
    ]
    # 1.5 Clean up old segments
    for f in os.listdir(HLS_DIR):
        if f.endswith(".ts") or f.endswith(".m3u8"):
            try:
                os.remove(os.path.join(HLS_DIR, f))
            except:
                pass
    current_process = subprocess.Popen(cmd)
    return jsonify({"status" : "started", "command": " ".join(cmd)})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)