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

        # Find the index of the first Text-Based subtitle stream
        text_sub_index = None
        pgs_sub_index = None
        # Common text formats supported by libass
        text_formats = ['ass', 'ssa', 'subrip', 'srt', 'mov_text']

        sub_count = 0
        for s in data['streams']:
            if s['codec_type'] == 'subtitle':
                codec = s.get('codec_name', '')
                if codec in text_formats and text_sub_index is None:
                    text_sub_index = sub_count

                elif codec == 'hdmv_pgs_subtitle' and pgs_sub_index is None:
                    pgs_sub_index = sub_count
                sub_count += 1


        video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
        return {
            "has_internal_subs": (text_sub_index is not None or pgs_sub_index is not None),
            "text_sub_index": text_sub_index,
            "pgs_sub_index": pgs_sub_index, 
            "codec": video_stream.get('codec_name') if video_stream else "unknown",
            "resolution":
            f"{video_stream.get('width')}x{video_stream.get('height')}" if video_stream else "unknown"
        }
    except Exception as e:
        print(f"Error probing {file_path}: {e}")
        return None
    
@app.route('/api/library', methods=['GET'])
def list_library():
    library_data = []
    
    # We list the top-level directories in your Media Library
    for entry in os.scandir(LIBRARY_PATH):
        if entry.is_dir():
            folder_path = entry.path
            episodes = []
            local_subs = []

            # Scan inside this specific folder
            for root, dirs, files in os.walk(folder_path):
                for f in files:
                    full_p = os.path.join(root, f)
                    if f.lower().endswith(VIDEO_EXTENSIONS):
                        episodes.append({
                            "name": f,
                            "path": full_p
                        })
                    elif f.lower().endswith('.srt'):
                        local_subs.append({
                            "name": f,
                            "path": full_p
                        })

            if episodes:
                library_data.append({
                    "folder_name": entry.name,
                    "local_subs": local_subs,
                    "episodes": sorted(episodes, key=lambda x: x['name'])
                })

    return jsonify(library_data)

@app.route('/api/probe', methods=['POST'])
def probe_file():
    path = request.json.get('path')
    metadata = get_video_metadata(path)
    return jsonify(metadata)
@app.route('/api/presets', methods=['GET'])
def get_presets():
    return jsonify(list(PRESETS.keys()))

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
    preset = PRESETS.get(preset_key)
    sub_path = data.get('sub_path') #  This will be the path to an .srt file if provided

    # Re-probe to get the latest metadata
    metadata = get_video_metadata(movie_path)

    # Base command
    cmd = ["ffmpeg", "-y", "-i", movie_path]

    # Filter Logic
    filter_str = ""
    if sub_path and sub_path != "":
        # External SRT
        esc_sub = sub_path.replace("'", "'\\\\\\''").replace(":", "\\:")
        filter_str = f"subtitles='{esc_sub}',format=yuv420p"
        cmd += ["-vf", filter_str]
    elif metadata.get('text_sub_index') is not None:
        # Internal Text (ASS/SRT)
        idx = metadata.get('text_sub_index')
        esc_path = movie_path.replace("'", "'\\\\\\''").replace(":","\\:")
        filter_str = f"subtitles='{esc_path}':si={idx},format=yuv420p"
        cmd += ["-vf", filter_str]
    elif metadata.get('pgs_sub_index') is not None:
        # Internal Image (PGS) - Needs filter_complex flage e e e 
        idx = metadata.get('pgs_sub_index')
        # This part overlays subtitle stream onto video stream
        cmd += ["-filter_complex", f"[0:v][0:s:{idx}]overlay,format=yuv420p"]
    else:
        # No Subs
        cmd += ["-vf", "format=yuv420p"]
    # Encoding Settings for Audio/Video
    cmd += ["-c:v", preset['v_codec']] + preset['v_profile']
    cmd += ["-c:a", preset['a_codec'], "-b:a", "192k", "-ac", "2"]

    # HLS Settings
    cmd += ["-f", "hls", "-hls_time", "6", "-hls_list_size", "0",
            "-hls_segment_filename", f"{HLS_DIR}/segment_%03d.ts",
            f"{HLS_DIR}/index.m3u8"]
    
    # Cleanup and Start stream
    for f in os.listdir(HLS_DIR):
        if f.endswith((".ts", ".m3u8")):
            try: os.remove(os.path.join(HLS_DIR, f))
            except: pass
    
    current_process = subprocess.Popen(cmd)
    return jsonify({"status": "started"})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)