import os
import subprocess
import json

from config import HLS_DIR


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


def build_ffmpeg_command(movie_path, preset, metadata, sub_path=None):
    """Build the FFmpeg command for CMAF streaming."""
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
        esc_path = movie_path.replace("'", "'\\\\\\''").replace(":", "\\:")
        filter_str = f"subtitles='{esc_path}':si={idx},format=yuv420p"
        cmd += ["-vf", filter_str]
    elif metadata.get('pgs_sub_index') is not None:
        # Internal Image (PGS)
        idx = metadata.get('pgs_sub_index')
        cmd += ["-filter_complex", f"[0:v][0:s:{idx}]overlay,format=yuv420p"]
    else:
        # No Subs
        cmd += ["-vf", "format=yuv420p"]

    # Video encoding - CMAF compatible (fMP4)
    cmd += ["-c:v", preset['v_codec']] + preset['v_profile']

    # Audio encoding - CMAF compatible
    cmd += ["-c:a", preset['a_codec'], "-b:a", "192k", "-ac", "2"]

    # CMAF settings
    cmd += [
        # Enable CMAF mode
        "-f", "hls",
        "-hls_playlist_type", "event",
        "-hls_flags", "independent_segments+omit_endlist",
        "-hls_segment_type", "fmp4",  # Fragmented MP4 for CMAF
        "-hls_time", "6",
        "-hls_list_size", "0",
        # CMAF initialization segment
        "-hls_fmp4_init_filename", f"{HLS_DIR}/init.mp4",
        # Segment template
        "-hls_segment_filename", f"{HLS_DIR}/chunk_%d.m4s",
        # Output playlist
        f"{HLS_DIR}/index.m3u8"
    ]

    return cmd


def cleanup_hls_directory():
    """Remove old CMAF segments and playlist files."""
    extensions = (".m4s", ".m3u8", ".mp4")  # CMAF uses .m4s and .mp4
    for f in os.listdir(HLS_DIR):
        if f.endswith(extensions):
            try:
                os.remove(os.path.join(HLS_DIR, f))
            except:
                pass