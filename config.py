"""Configuration for Bedtime Streamer"""

import os
import json
from pathlib import Path

# Try to load from config.json first (created by setup.py)
config_file = Path(__file__).parent / 'config.json'
if config_file.exists():
    with open(config_file) as f:
        _config = json.load(f)
    _default_media = _config.get('media_path', str(Path.home() / "Videos"))
    _default_stream = _config.get('stream_path', str(Path.home() / "bedtime-streamer"))
else:
    _default_media = str(Path.home() / "Videos")
    _default_stream = str(Path.home() / "bedtime-streamer")

# Paths (can be overridden by environment variables)
LIBRARY_PATH_RAW = os.environ.get("LIBRARY_PATH", _default_media)
HLS_DIR_RAW = os.environ.get("HLS_DIR", _default_stream)

# Convert to forward slashes for FFmpeg compatibility (works everywhere)
HLS_DIR = Path(HLS_DIR_RAW).as_posix()
LIBRARY_PATH = Path(LIBRARY_PATH_RAW).as_posix()

# Create directories using native paths (works on all OS)
Path(HLS_DIR_RAW).mkdir(parents=True, exist_ok=True)
Path(LIBRARY_PATH_RAW).mkdir(parents=True, exist_ok=True)

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