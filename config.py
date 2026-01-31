"""Configuration constants for the HLS streaming app"""
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